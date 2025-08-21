"""Arcam AVR integration for Home Assistant."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import ArcamAvrCoordinator

_LOGGER = logging.getLogger(__name__)

# Platforms supported by this integration
PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Arcam AVR from a config entry."""
    _LOGGER.debug("Setting up Arcam AVR integration for %s", entry.data["host"])
    
    # Initialize the coordinator
    coordinator = ArcamAvrCoordinator(hass, entry)
    
    try:
        # Perform first refresh and setup
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        _LOGGER.error("Failed to setup Arcam AVR coordinator: %s", err)
        raise ConfigEntryNotReady(f"Failed to connect to device: {err}") from err
    
    # Store coordinator in hass data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    _LOGGER.info(
        "Successfully setup Arcam AVR integration for %s (%s)",
        entry.data["host"],
        coordinator.device_model,
    )
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Arcam AVR integration for %s", entry.data["host"])
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Clean up coordinator
        coordinator: ArcamAvrCoordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.async_shutdown()
        
        # Remove entry from hass data
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # Remove domain data if no more entries
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
            
        _LOGGER.info("Successfully unloaded Arcam AVR integration for %s", entry.data["host"])
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    _LOGGER.debug("Reloading Arcam AVR integration for %s", entry.data["host"])
    
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
    
    _LOGGER.info("Successfully reloaded Arcam AVR integration for %s", entry.data["host"])


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating Arcam AVR config entry from version %s", config_entry.version)
    
    # Migration logic for future version updates
    if config_entry.version == 1:
        # No migration needed for version 1
        return True
    
    # If we get here, we don't know how to migrate
    _LOGGER.error("Cannot migrate config entry version %s", config_entry.version)
    return False


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove config entry."""
    _LOGGER.debug("Removing Arcam AVR integration for %s", entry.data["host"])
    
    # Clean up any persistent data if needed
    # This is called when the integration is completely removed
    
    _LOGGER.info("Successfully removed Arcam AVR integration for %s", entry.data["host"])


async def async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug("Options updated for Arcam AVR integration %s", entry.data["host"])
    
    # Get coordinator
    coordinator: ArcamAvrCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Update coordinator with new options
    if "update_interval" in entry.options:
        from datetime import timedelta
        new_interval = timedelta(seconds=entry.options["update_interval"])
        coordinator.update_interval = new_interval
        _LOGGER.debug("Updated update interval to %s seconds", entry.options["update_interval"])
    
    # Trigger a refresh to apply any changes
    await coordinator.async_request_refresh()
    
    _LOGGER.info("Successfully updated options for Arcam AVR integration %s", entry.data["host"])


# Register options update listener
async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Arcam AVR integration."""
    # This function is called when the integration is loaded
    # It's used for YAML-based configuration (legacy support)
    
    _LOGGER.debug("Arcam AVR integration loaded")
    return True