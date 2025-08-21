"""Arcam AVR TCP connection management."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Awaitable

from .exceptions import (
    ArcamConnectionError,
    ArcamTimeoutError,
    ArcamProtocolError,
)
from .protocol import ArcamCommand, ArcamResponse, ArcamProtocol

_LOGGER = logging.getLogger(__name__)

# Connection constants
DEFAULT_PORT = 50000
DEFAULT_TIMEOUT = 3.0
RECONNECT_DELAY_BASE = 1.0
MAX_RECONNECT_ATTEMPTS = 5
BUFFER_SIZE = 1024


class ArcamConnection:
    """Manages TCP connection to Arcam device."""
    
    def __init__(self, host: str, port: int = DEFAULT_PORT, timeout: float = DEFAULT_TIMEOUT):
        """Initialize connection manager.
        
        Args:
            host: Device IP address
            port: TCP port (default 50000)
            timeout: Command timeout in seconds
        """
        self._host = host
        self._port = port
        self._timeout = timeout
        
        # Connection state
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._connected = False
        
        # Broadcast listener
        self._broadcast_callback: Callable[[ArcamResponse], Awaitable[None]] | None = None
        self._broadcast_task: asyncio.Task | None = None
        
        # Command lock to ensure single command execution
        self._command_lock = asyncio.Lock()
        
        # Reconnection state
        self._reconnect_attempts = 0
        self._reconnect_task: asyncio.Task | None = None
        
    @property
    def host(self) -> str:
        """Get device host."""
        return self._host
        
    @property
    def port(self) -> int:
        """Get device port."""
        return self._port
        
    @property
    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self._connected and self._writer is not None and not self._writer.is_closing()
        
    async def connect(self) -> None:
        """Establish connection to device."""
        if self.is_connected:
            return
            
        try:
            _LOGGER.debug("Connecting to Arcam device at %s:%d", self._host, self._port)
            
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=self._timeout
            )
            
            self._connected = True
            self._reconnect_attempts = 0
            
            _LOGGER.info("Connected to Arcam device at %s:%d", self._host, self._port)
            
        except asyncio.TimeoutError as err:
            raise ArcamConnectionError(f"Connection timeout to {self._host}:{self._port}") from err
        except OSError as err:
            raise ArcamConnectionError(f"Connection failed to {self._host}:{self._port}: {err}") from err
    
    async def disconnect(self) -> None:
        """Close connection to device."""
        _LOGGER.debug("Disconnecting from Arcam device")
        
        # Stop broadcast listener
        await self.stop_broadcast_listener()
        
        # Cancel reconnection task
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
        
        # Close writer
        if self._writer and not self._writer.is_closing():
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception as err:
                _LOGGER.debug("Error closing writer: %s", err)
        
        self._reader = None
        self._writer = None
        self._connected = False
        
        _LOGGER.info("Disconnected from Arcam device")
    
    async def send_command(self, command: ArcamCommand) -> ArcamResponse:
        """Send command and wait for response.
        
        Args:
            command: Command to send
            
        Returns:
            Device response
            
        Raises:
            ArcamConnectionError: If not connected
            ArcamTimeoutError: If command times out
            ArcamProtocolError: If response is invalid
        """
        async with self._command_lock:
            if not self.is_connected:
                raise ArcamConnectionError("Not connected to device")
            
            try:
                # Encode and send command
                command_bytes = ArcamProtocol.encode_command(command)
                
                _LOGGER.debug(
                    "Sending command: zone=%d, code=0x%02X, data=%s",
                    command.zone,
                    command.command_code,
                    command.data.hex() if command.data else "none"
                )
                
                self._writer.write(command_bytes)
                await self._writer.drain()
                
                # Wait for response
                response_data = await asyncio.wait_for(
                    self._read_response(),
                    timeout=self._timeout
                )
                
                # Decode response
                response = ArcamProtocol.decode_response(response_data)
                
                # Validate response matches command
                if not ArcamProtocol.validate_response(response, command.command_code):
                    _LOGGER.warning("Response command code mismatch")
                
                _LOGGER.debug(
                    "Received response: zone=%d, code=0x%02X, answer=0x%02X, data=%s",
                    response.zone,
                    response.command_code,
                    response.answer_code,
                    response.data.hex() if response.data else "none"
                )
                
                return response
                
            except asyncio.TimeoutError as err:
                _LOGGER.error("Command timeout after %s seconds", self._timeout)
                # Schedule reconnection
                asyncio.create_task(self._handle_connection_lost())
                raise ArcamTimeoutError("Command timeout") from err
            
            except (OSError, ConnectionError) as err:
                _LOGGER.error("Connection error during command: %s", err)
                # Schedule reconnection
                asyncio.create_task(self._handle_connection_lost())
                raise ArcamConnectionError(f"Connection error: {err}") from err
    
    async def _read_response(self) -> bytes:
        """Read response from device."""
        if not self._reader:
            raise ArcamConnectionError("No reader available")
        
        # Read response data
        # Arcam responses have variable length, so we need to read the header first
        header = await self._reader.read(5)  # Start + zone + command + answer + length
        if len(header) < 5:
            raise ArcamProtocolError(f"Incomplete header: {len(header)} bytes")
        
        data_length = header[4]
        remaining = data_length + 1  # Data + end byte
        
        if remaining > 0:
            data_and_end = await self._reader.read(remaining)
            if len(data_and_end) < remaining:
                raise ArcamProtocolError(f"Incomplete response: expected {remaining}, got {len(data_and_end)}")
            
            return header + data_and_end
        else:
            # No data, just end byte
            end_byte = await self._reader.read(1)
            if len(end_byte) < 1:
                raise ArcamProtocolError("Missing end byte")
            
            return header + end_byte
    
    async def start_broadcast_listener(self, callback: Callable[[ArcamResponse], Awaitable[None]]) -> None:
        """Start listening for broadcast messages from device.
        
        Args:
            callback: Function to call with broadcast responses
        """
        if self._broadcast_task and not self._broadcast_task.done():
            await self.stop_broadcast_listener()
        
        self._broadcast_callback = callback
        self._broadcast_task = asyncio.create_task(self._broadcast_listener())
        
        _LOGGER.debug("Started broadcast listener")
    
    async def stop_broadcast_listener(self) -> None:
        """Stop broadcast listener."""
        if self._broadcast_task and not self._broadcast_task.done():
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass
        
        self._broadcast_callback = None
        self._broadcast_task = None
        
        _LOGGER.debug("Stopped broadcast listener")
    
    async def _broadcast_listener(self) -> None:
        """Listen for broadcast messages."""
        if not self._reader:
            return
        
        try:
            while self.is_connected:
                try:
                    # Check if data is available without blocking
                    if self._reader.at_eof():
                        break
                    
                    # Try to read a response (with short timeout to not block commands)
                    response_data = await asyncio.wait_for(
                        self._read_response(),
                        timeout=0.1
                    )
                    
                    # Decode and process broadcast
                    response = ArcamProtocol.decode_response(response_data)
                    
                    _LOGGER.debug(
                        "Received broadcast: zone=%d, code=0x%02X, answer=0x%02X",
                        response.zone,
                        response.command_code,
                        response.answer_code
                    )
                    
                    # Call callback if available
                    if self._broadcast_callback:
                        await self._broadcast_callback(response)
                        
                except asyncio.TimeoutError:
                    # No data available, continue listening
                    continue
                except Exception as err:
                    _LOGGER.debug("Broadcast listener error: %s", err)
                    break
                    
        except Exception as err:
            _LOGGER.error("Broadcast listener failed: %s", err)
        finally:
            _LOGGER.debug("Broadcast listener stopped")
    
    async def _handle_connection_lost(self) -> None:
        """Handle connection loss and attempt reconnection."""
        if not self._connected:
            return
        
        _LOGGER.warning("Connection lost, attempting reconnection")
        self._connected = False
        
        # Start reconnection task if not already running
        if not self._reconnect_task or self._reconnect_task.done():
            self._reconnect_task = asyncio.create_task(self._reconnect_with_backoff())
    
    async def _reconnect_with_backoff(self) -> None:
        """Reconnect with exponential backoff."""
        while self._reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
            self._reconnect_attempts += 1
            delay = RECONNECT_DELAY_BASE * (2 ** (self._reconnect_attempts - 1))
            
            _LOGGER.info(
                "Reconnection attempt %d/%d in %s seconds",
                self._reconnect_attempts,
                MAX_RECONNECT_ATTEMPTS,
                delay
            )
            
            await asyncio.sleep(delay)
            
            try:
                await self.connect()
                
                # Restart broadcast listener if callback is set
                if self._broadcast_callback:
                    self._broadcast_task = asyncio.create_task(self._broadcast_listener())
                
                _LOGGER.info("Reconnection successful")
                return
                
            except ArcamConnectionError as err:
                _LOGGER.warning("Reconnection attempt %d failed: %s", self._reconnect_attempts, err)
        
        _LOGGER.error("Max reconnection attempts reached, giving up")
    
    async def get_device_info(self) -> dict[str, Any]:
        """Get basic device information.
        
        Returns:
            Dictionary with device information
        """
        from .commands import ArcamCommands, decode_version_response
        
        try:
            # Get software version
            version_command = ArcamCommands.get_software_version()
            version_response = await self.send_command(version_command)
            
            version = None
            if version_response.is_success:
                version = decode_version_response(version_response.data)
            
            return {
                "host": self._host,
                "port": self._port,
                "version": version or "Unknown",
                "connected": self.is_connected,
            }
            
        except Exception as err:
            _LOGGER.error("Failed to get device info: %s", err)
            return {
                "host": self._host,
                "port": self._port,
                "version": "Unknown",
                "connected": self.is_connected,
                "error": str(err),
            }
    
    def __repr__(self) -> str:
        """String representation of connection."""
        return f"ArcamConnection(host={self._host}, port={self._port}, connected={self.is_connected})"