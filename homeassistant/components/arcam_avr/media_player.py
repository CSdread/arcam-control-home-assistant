"""Media player entity for Arcam AVR integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .arcam.commands import ArcamCommands
from .const import (
    DOMAIN,
    SOURCE_MAPPING,
    AVAILABLE_SOURCES,
    VOLUME_MIN,
    VOLUME_MAX,
    ZONE_1,
    ATTR_INPUT_SOURCE,
    ATTR_MODEL,
    ATTR_VERSION,
)
from .coordinator import ArcamAvrCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Arcam AVR media player from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    # Create media player entity
    async_add_entities([ArcamAvrMediaPlayer(coordinator, config_entry)], True)


class ArcamAvrMediaPlayer(CoordinatorEntity[ArcamAvrCoordinator], MediaPlayerEntity):
    """Representation of an Arcam AVR as a media player."""

    def __init__(
        self,
        coordinator: ArcamAvrCoordinator,
        config_entry: ConfigEntry,
        zone: int = ZONE_1,
    ) -> None:
        """Initialize the media player."""
        super().__init__(coordinator)
        
        self._config_entry = config_entry
        self._zone = zone
        self._attr_unique_id = f"{config_entry.entry_id}_zone_{zone}"
        
        # Device information
        device_name = config_entry.data.get("name", "Arcam AVR")
        zone_suffix = f" Zone {zone}" if zone > 1 else ""
        self._attr_name = f"{device_name}{zone_suffix}"
        
        # Entity configuration
        self._attr_should_poll = False
        self._attr_has_entity_name = True
        self._attr_entity_registry_enabled_default = True

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return self.coordinator.device_info

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the device."""
        if not self.available:
            return MediaPlayerState.OFF
            
        if self.coordinator.data is None:
            return MediaPlayerState.OFF
            
        power = self.coordinator.data.get("power")
        if power is None:
            return MediaPlayerState.OFF
            
        return MediaPlayerState.ON if power else MediaPlayerState.OFF

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.get("available", False)
        )

    @property
    def volume_level(self) -> float | None:
        """Volume level of the media player (0..1)."""
        if self.coordinator.data is None:
            return None
            
        volume = self.coordinator.data.get("volume")
        if volume is None:
            return None
            
        # Convert device volume (0-99) to HA volume (0.0-1.0)
        return volume / VOLUME_MAX

    @property
    def is_volume_muted(self) -> bool | None:
        """Boolean if volume is currently muted."""
        if self.coordinator.data is None:
            return None
            
        return self.coordinator.data.get("mute")

    @property
    def source(self) -> str | None:
        """Return the current input source."""
        if self.coordinator.data is None:
            return None
            
        source_code = self.coordinator.data.get("source")
        if source_code is None:
            return None
            
        # Return friendly name if available, otherwise return the code
        return SOURCE_MAPPING.get(source_code, source_code)

    @property
    def source_list(self) -> list[str]:
        """List of available input sources."""
        return [SOURCE_MAPPING.get(src, src) for src in AVAILABLE_SOURCES]

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Flag media player features that are supported."""
        return (
            MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
            | MediaPlayerEntityFeature.VOLUME_SET
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.SELECT_SOURCE
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attributes = {}
        
        if self.coordinator.data is not None:
            # Add raw source code for debugging
            raw_source = self.coordinator.data.get("source")
            if raw_source is not None:
                attributes[ATTR_INPUT_SOURCE] = raw_source
                
            # Add device information
            attributes[ATTR_MODEL] = self.coordinator.device_model
            attributes[ATTR_VERSION] = self.coordinator.device_version
            
            # Add zone information if multi-zone
            if self._zone > 1:
                attributes["zone"] = self._zone
                
        return attributes

    async def async_turn_on(self) -> None:
        """Turn the media player on."""
        _LOGGER.debug("Turning on Arcam AVR")
        
        success = await self.coordinator.async_send_command(
            ArcamCommands.power_on, self._zone
        )
        
        if not success:
            _LOGGER.error("Failed to turn on device")

    async def async_turn_off(self) -> None:
        """Turn the media player off."""
        _LOGGER.debug("Turning off Arcam AVR")
        
        success = await self.coordinator.async_send_command(
            ArcamCommands.power_off, self._zone
        )
        
        if not success:
            _LOGGER.error("Failed to turn off device")

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        # Convert HA volume (0.0-1.0) to device volume (0-99)
        device_volume = int(volume * VOLUME_MAX)
        device_volume = max(VOLUME_MIN, min(VOLUME_MAX, device_volume))
        
        _LOGGER.debug("Setting volume to %d (%.1f%%)", device_volume, volume * 100)
        
        success = await self.coordinator.async_send_command(
            ArcamCommands.set_volume, device_volume, self._zone
        )
        
        if not success:
            _LOGGER.error("Failed to set volume to %d", device_volume)

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute (true) or unmute (false) media player."""
        _LOGGER.debug("Setting mute to %s", mute)
        
        # Get current mute status
        current_mute = self.coordinator.data.get("mute") if self.coordinator.data else None
        
        # Only send command if state needs to change
        if current_mute != mute:
            success = await self.coordinator.async_send_command(
                ArcamCommands.toggle_mute, self._zone
            )
            
            if not success:
                _LOGGER.error("Failed to toggle mute")
        else:
            _LOGGER.debug("Mute already in desired state")

    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        _LOGGER.debug("Selecting source: %s", source)
        
        # Find the source code for the given friendly name
        source_code = None
        for code, friendly_name in SOURCE_MAPPING.items():
            if friendly_name == source:
                source_code = code
                break
        
        # If not found in mapping, try using source directly
        if source_code is None:
            if source in AVAILABLE_SOURCES:
                source_code = source
            else:
                _LOGGER.error("Unknown source: %s", source)
                return
        
        success = await self.coordinator.async_send_command(
            ArcamCommands.select_source, source_code, self._zone
        )
        
        if not success:
            _LOGGER.error("Failed to select source: %s", source)

    async def async_update(self) -> None:
        """Update the entity.
        
        Only used when coordinator is not available.
        """
        await self.coordinator.async_request_refresh()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        _LOGGER.debug("Media player entity added: %s", self.entity_id)

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        await super().async_will_remove_from_hass()
        _LOGGER.debug("Media player entity removed: %s", self.entity_id)