"""Mock Arcam device for testing."""
import asyncio
from typing import Callable, Optional
from unittest.mock import AsyncMock


class MockArcamDevice:
    """Mock implementation of Arcam device for testing."""
    
    def __init__(self):
        """Initialize mock device with default state."""
        self.power = False
        self.volume = 50
        self.mute = False
        self.source = 0  # CD
        self.connected = False
        self.command_delay = 0.01  # Simulate response delay
        self.should_fail = False  # For testing error conditions
        self.broadcast_callback: Optional[Callable] = None
        
    async def connect(self) -> None:
        """Simulate connection."""
        if self.should_fail:
            raise ConnectionError("Mock connection failed")
        await asyncio.sleep(0.01)  # Simulate connection time
        self.connected = True
        
    async def disconnect(self) -> None:
        """Simulate disconnection."""
        self.connected = False
        
    async def send_command(self, command_bytes: bytes) -> bytes:
        """Process command and return appropriate response."""
        if not self.connected:
            raise ConnectionError("Not connected")
            
        if self.should_fail:
            raise TimeoutError("Mock command timeout")
            
        await asyncio.sleep(self.command_delay)
        
        # Parse command
        if len(command_bytes) < 6:
            return self._error_response(0x86)  # Invalid data length
            
        zone = command_bytes[1]
        command_code = command_bytes[2]
        data_length = command_bytes[3]
        
        if zone != 0x01:
            return self._error_response(0x82)  # Zone invalid
            
        # Handle specific commands
        if command_code == 0x00:  # Power
            return self._handle_power_command(command_bytes)
        elif command_code == 0x0D:  # Volume
            return self._handle_volume_command(command_bytes)
        elif command_code == 0x0E:  # Mute status
            return self._handle_mute_command(command_bytes)
        elif command_code == 0x1D:  # Source
            return self._handle_source_command(command_bytes)
        elif command_code == 0x08:  # RC5 simulate
            return self._handle_rc5_command(command_bytes)
        elif command_code == 0x04:  # Software version
            return self._handle_version_command(command_bytes)
        else:
            return self._error_response(0x83)  # Command not recognized
            
    def _handle_power_command(self, command_bytes: bytes) -> bytes:
        """Handle power command."""
        if len(command_bytes) != 6:
            return self._error_response(0x86)
            
        data = command_bytes[4]
        if data == 0xF0:  # Get power status
            return self._success_response(0x00, [0x01 if self.power else 0x00])
        elif data == 0x01:  # Power on
            self.power = True
            return self._success_response(0x00, [0x01])
        elif data == 0x00:  # Power off
            self.power = False
            return self._success_response(0x00, [0x00])
        else:
            return self._error_response(0x84)  # Parameter not recognized
            
    def _handle_volume_command(self, command_bytes: bytes) -> bytes:
        """Handle volume command."""
        if len(command_bytes) != 6:
            return self._error_response(0x86)
            
        data = command_bytes[4]
        if data == 0xF0:  # Get volume
            return self._success_response(0x0D, [self.volume])
        elif 0 <= data <= 99:  # Set volume
            self.volume = data
            return self._success_response(0x0D, [data])
        else:
            return self._error_response(0x84)  # Parameter not recognized
            
    def _handle_mute_command(self, command_bytes: bytes) -> bytes:
        """Handle mute status command."""
        if len(command_bytes) != 6:
            return self._error_response(0x86)
            
        data = command_bytes[4]
        if data == 0xF0:  # Get mute status
            return self._success_response(0x0E, [0x01 if self.mute else 0x00])
        else:
            return self._error_response(0x84)  # Parameter not recognized
            
    def _handle_source_command(self, command_bytes: bytes) -> bytes:
        """Handle source command."""
        if len(command_bytes) != 6:
            return self._error_response(0x86)
            
        data = command_bytes[4]
        if data == 0xF0:  # Get source
            return self._success_response(0x1D, [self.source])
        else:
            return self._error_response(0x84)  # Parameter not recognized
            
    def _handle_rc5_command(self, command_bytes: bytes) -> bytes:
        """Handle RC5 IR simulation."""
        if len(command_bytes) != 7:
            return self._error_response(0x86)
            
        rc5_1 = command_bytes[4]
        rc5_2 = command_bytes[5]
        
        # Handle mute toggle
        if rc5_1 == 0x10 and rc5_2 == 0x0D:
            self.mute = not self.mute
            
        # Handle source changes
        source_map = {
            (0x10, 0x76): 0,  # CD
            (0x10, 0x62): 1,  # BD
            (0x10, 0x5E): 2,  # AV
            (0x10, 0x64): 3,  # STB
        }
        
        if (rc5_1, rc5_2) in source_map:
            self.source = source_map[(rc5_1, rc5_2)]
            
        return self._success_response(0x08, [rc5_1, rc5_2])
    
    def _handle_version_command(self, command_bytes: bytes) -> bytes:
        """Handle version command."""
        if len(command_bytes) != 6:
            return self._error_response(0x86)
            
        data = command_bytes[4]
        if data == 0xF0:  # Get version
            # Return mock version string "2.01/0.03/1."
            version_bytes = [0x32, 0x2E, 0x30, 0x31, 0x2F, 0x30, 0x2E, 0x30, 0x33, 0x2F, 0x31, 0x2E]
            return self._success_response(0x04, version_bytes)
        else:
            return self._error_response(0x84)
        
    def _success_response(self, command_code: int, data: list[int]) -> bytes:
        """Generate success response."""
        response = [0x21, 0x01, command_code, 0x00, len(data)]
        response.extend(data)
        response.append(0x0D)
        return bytes(response)
        
    def _error_response(self, error_code: int) -> bytes:
        """Generate error response."""
        return bytes([0x21, 0x01, 0x00, error_code, 0x00, 0x0D])
        
    async def trigger_broadcast(self, message_type: str) -> None:
        """Trigger a broadcast message."""
        if not self.broadcast_callback:
            return
            
        if message_type == "power_change":
            response = self._success_response(0x00, [0x01 if self.power else 0x00])
        elif message_type == "volume_change":
            response = self._success_response(0x0D, [self.volume])
        elif message_type == "source_change":
            response = self._success_response(0x1D, [self.source])
        else:
            return
            
        await self.broadcast_callback(response)