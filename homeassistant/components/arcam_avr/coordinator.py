"""Data update coordinator for Arcam AVR integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .arcam.connection import ArcamConnection
from .arcam.commands import (
    ArcamCommands,
    decode_power_response,
    decode_volume_response,
    decode_mute_response,
    decode_source_response,
    get_source_name,
)
from .arcam.exceptions import ArcamConnectionError, ArcamTimeoutError
from .arcam.protocol import ArcamResponse
from .const import (
    DOMAIN,
    DEFAULT_UPDATE_INTERVAL,
    UPDATE_INTERVAL_FAST,
    MANUFACTURER,
    ZONE_1,
)

_LOGGER = logging.getLogger(__name__)


class ArcamAvrCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Arcam AVR data."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize coordinator."""
        self.config_entry = config_entry
        self.host = config_entry.data[CONF_HOST]
        self.port = config_entry.data[CONF_PORT]
        
        # Initialize connection
        self.arcam = ArcamConnection(self.host, self.port)
        
        # Device information from config entry
        self.device_model = config_entry.data.get("model", "AVR")
        self.device_version = config_entry.data.get("version", "Unknown")
        
        # State tracking
        self._last_activity = None
        self._fast_update_until = None
        
        # Get update interval from options or use default
        update_interval = config_entry.options.get("update_interval", DEFAULT_UPDATE_INTERVAL)
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.host}",
            update_interval=timedelta(seconds=update_interval),
        )

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.host)},
            "name": f"Arcam {self.device_model}",
            "manufacturer": MANUFACTURER,
            "model": self.device_model,
            "sw_version": self.device_version,
            "configuration_url": f"http://{self.host}",
        }

    async def _async_setup(self) -> None:
        """Set up the coordinator."""
        try:
            # Connect to device
            await self.arcam.connect()
            
            # Start broadcast listener for real-time updates
            await self.arcam.start_broadcast_listener(self._handle_broadcast_message)
            
            _LOGGER.info("Successfully connected to Arcam AVR at %s:%d", self.host, self.port)
            
        except (ArcamConnectionError, ArcamTimeoutError) as err:
            _LOGGER.error("Failed to connect to Arcam AVR: %s", err)
            raise UpdateFailed(f"Connection failed: {err}") from err

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the device."""
        if not self.arcam.is_connected:
            try:
                await self.arcam.connect()
                # Restart broadcast listener after reconnection
                await self.arcam.start_broadcast_listener(self._handle_broadcast_message)
            except (ArcamConnectionError, ArcamTimeoutError) as err:
                raise UpdateFailed(f"Connection failed: {err}") from err

        try:
            # Fetch all device state
            data = await self._fetch_device_state()
            
            # Update availability
            data["available"] = True
            data["model"] = self.device_model
            data["version"] = self.device_version
            
            _LOGGER.debug("Updated device state: %s", data)
            return data
            
        except (ArcamConnectionError, ArcamTimeoutError) as err:
            _LOGGER.error("Failed to update device state: %s", err)
            raise UpdateFailed(f"Update failed: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error during update: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def _fetch_device_state(self) -> dict[str, Any]:
        """Fetch current device state."""
        state = {}
        
        try:
            # Get power status
            power_command = ArcamCommands.get_power_status(ZONE_1)
            power_response = await self.arcam.send_command(power_command)
            if power_response.is_success:
                state["power"] = decode_power_response(power_response.data)
            else:
                _LOGGER.warning("Failed to get power status: %s", power_response.error_message)
                state["power"] = None

            # Get volume level
            volume_command = ArcamCommands.get_volume(ZONE_1)
            volume_response = await self.arcam.send_command(volume_command)
            if volume_response.is_success:
                state["volume"] = decode_volume_response(volume_response.data)
            else:
                _LOGGER.warning("Failed to get volume: %s", volume_response.error_message)
                state["volume"] = None

            # Get mute status
            mute_command = ArcamCommands.get_mute_status(ZONE_1)
            mute_response = await self.arcam.send_command(mute_command)
            if mute_response.is_success:
                state["mute"] = decode_mute_response(mute_response.data)
            else:
                _LOGGER.warning("Failed to get mute status: %s", mute_response.error_message)
                state["mute"] = None

            # Get current source
            source_command = ArcamCommands.get_source(ZONE_1)
            source_response = await self.arcam.send_command(source_command)
            if source_response.is_success:
                source_name = decode_source_response(source_response.data)
                state["source"] = source_name or "Unknown"
            else:
                _LOGGER.warning("Failed to get source: %s", source_response.error_message)
                state["source"] = "Unknown"

        except Exception as err:
            _LOGGER.error("Error fetching device state: %s", err)
            raise

        return state

    async def async_send_command(
        self, 
        command_func: Callable, 
        *args, 
        immediate_refresh: bool = True
    ) -> bool:
        """Send command to device and optionally refresh state immediately.
        
        Args:
            command_func: Function to create the command
            *args: Arguments for the command function
            immediate_refresh: Whether to refresh state immediately after command
            
        Returns:
            True if command was successful, False otherwise
        """
        try:
            # Create and send command
            command = command_func(*args)
            response = await self.arcam.send_command(command)
            
            if not response.is_success:
                _LOGGER.warning(
                    "Command failed: %s (code: 0x%02X)", 
                    response.error_message, 
                    response.answer_code
                )
                return False
            
            _LOGGER.debug(
                "Command successful: zone=%d, code=0x%02X", 
                command.zone, 
                command.command_code
            )
            
            # Trigger immediate refresh if requested
            if immediate_refresh:
                await self.async_request_refresh()
                
            # Enable fast updates temporarily
            self._enable_fast_updates()
            
            return True
            
        except (ArcamConnectionError, ArcamTimeoutError) as err:
            _LOGGER.error("Command failed due to connection error: %s", err)
            return False
        except Exception as err:
            _LOGGER.exception("Unexpected error sending command: %s", err)
            return False

    async def _handle_broadcast_message(self, response: ArcamResponse) -> None:
        """Handle broadcast message from device."""
        _LOGGER.debug(
            "Received broadcast: zone=%d, code=0x%02X, answer=0x%02X",
            response.zone,
            response.command_code,
            response.answer_code,
        )
        
        # Only process successful status updates
        if not response.is_success:
            return
            
        # Update coordinator data based on broadcast message
        if self.data is None:
            return
            
        updated_data = dict(self.data)
        
        # Handle different command types
        if response.command_code == 0x00:  # Power status
            power_state = decode_power_response(response.data)
            if power_state is not None:
                updated_data["power"] = power_state
                
        elif response.command_code == 0x0D:  # Volume
            volume_level = decode_volume_response(response.data)
            if volume_level is not None:
                updated_data["volume"] = volume_level
                
        elif response.command_code == 0x0E:  # Mute status
            mute_state = decode_mute_response(response.data)
            if mute_state is not None:
                updated_data["mute"] = mute_state
                
        elif response.command_code == 0x1D:  # Source
            source_name = decode_source_response(response.data)
            if source_name is not None:
                updated_data["source"] = source_name
        
        # Update data if anything changed
        if updated_data != self.data:
            _LOGGER.debug("Broadcast updated state: %s", updated_data)
            self.async_set_updated_data(updated_data)
            self._enable_fast_updates()

    def _enable_fast_updates(self) -> None:
        """Enable fast updates for a short period after activity."""
        from datetime import datetime, timedelta
        
        self._last_activity = datetime.now()
        self._fast_update_until = self._last_activity + timedelta(seconds=60)
        
        # Temporarily reduce update interval
        new_interval = timedelta(seconds=UPDATE_INTERVAL_FAST)
        if self.update_interval != new_interval:
            self.update_interval = new_interval
            _LOGGER.debug("Enabled fast updates for 60 seconds")

    def _check_update_interval(self) -> None:
        """Check if we should return to normal update interval."""
        from datetime import datetime
        
        if self._fast_update_until and datetime.now() > self._fast_update_until:
            # Return to normal interval
            normal_interval = self.config_entry.options.get("update_interval", DEFAULT_UPDATE_INTERVAL)
            new_interval = timedelta(seconds=normal_interval)
            
            if self.update_interval != new_interval:
                self.update_interval = new_interval
                _LOGGER.debug("Returned to normal update interval")
                
            self._fast_update_until = None

    async def async_refresh_status(self) -> None:
        """Refresh device status immediately."""
        await self.async_request_refresh()

    async def async_shutdown(self) -> None:
        """Shutdown coordinator and clean up resources."""
        try:
            # Stop broadcast listener
            await self.arcam.stop_broadcast_listener()
            
            # Disconnect from device
            await self.arcam.disconnect()
            
            _LOGGER.info("Coordinator shutdown complete")
            
        except Exception as err:
            _LOGGER.error("Error during coordinator shutdown: %s", err)

    async def async_config_entry_first_refresh(self) -> None:
        """Perform first refresh and setup."""
        await self._async_setup()
        await super().async_config_entry_first_refresh()

    def _async_update_listeners(self) -> None:
        """Update listeners and check update interval."""
        self._check_update_interval()
        super()._async_update_listeners()