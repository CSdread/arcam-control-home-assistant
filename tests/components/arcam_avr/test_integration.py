"""Integration tests for Arcam AVR."""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_ON, STATE_OFF, STATE_UNAVAILABLE
from homeassistant.components.media_player import (
    MediaPlayerState,
    DOMAIN as MEDIA_PLAYER_DOMAIN,
)
from homeassistant.components.arcam_avr.const import DOMAIN
from homeassistant.exceptions import ConfigEntryNotReady

from tests.common import MockConfigEntry


async def test_full_integration_lifecycle(hass, mock_connection_factory):
    """Test complete integration lifecycle from setup to teardown."""
    # Create config entry
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        mock_connection_class.return_value = mock_connection
        
        # Test setup
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        
        # Verify integration state
        assert config_entry.state == ConfigEntryState.LOADED
        assert DOMAIN in hass.data
        assert config_entry.entry_id in hass.data[DOMAIN]
        
        # Verify media player entity creation
        await hass.async_block_till_done()
        state = hass.states.get("media_player.test_avr")
        assert state is not None
        assert state.state == STATE_ON
        
        # Test unload
        assert await hass.config_entries.async_unload(config_entry.entry_id)
        assert config_entry.state == ConfigEntryState.NOT_LOADED
        
        # Verify cleanup
        assert config_entry.entry_id not in hass.data.get(DOMAIN, {})


async def test_integration_with_connection_failure(hass):
    """Test integration behavior when connection fails."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = AsyncMock()
        mock_connection.connect.side_effect = ConnectionError("Connection failed")
        mock_connection_class.return_value = mock_connection
        
        config_entry.add_to_hass(hass)
        
        # Setup should fail and raise ConfigEntryNotReady
        assert not await hass.config_entries.async_setup(config_entry.entry_id)
        assert config_entry.state == ConfigEntryState.SETUP_RETRY


async def test_integration_reconnection_behavior(hass, mock_connection_factory):
    """Test integration handles connection losses and reconnections."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        mock_connection_class.return_value = mock_connection
        
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        
        await hass.async_block_till_done()
        
        # Simulate connection loss
        coordinator = hass.data[DOMAIN][config_entry.entry_id]
        coordinator.last_update_success = False
        coordinator.async_update_listeners()
        
        await hass.async_block_till_done()
        
        # Entity should become unavailable
        state = hass.states.get("media_player.test_avr")
        assert state.state == STATE_UNAVAILABLE
        
        # Simulate reconnection
        coordinator.last_update_success = True
        coordinator.data = {"power": True, "available": True}
        coordinator.async_update_listeners()
        
        await hass.async_block_till_done()
        
        # Entity should become available again
        state = hass.states.get("media_player.test_avr")
        assert state.state == STATE_ON


async def test_media_player_service_calls(hass, mock_connection_factory):
    """Test media player service calls through the integration."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        mock_connection_class.return_value = mock_connection
        
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        
        await hass.async_block_till_done()
        
        entity_id = "media_player.test_avr"
        
        # Test turn_on service
        await hass.services.async_call(
            MEDIA_PLAYER_DOMAIN,
            "turn_on",
            {"entity_id": entity_id},
            blocking=True,
        )
        
        # Verify command was sent
        mock_connection.send_command.assert_called()
        
        # Test turn_off service
        await hass.services.async_call(
            MEDIA_PLAYER_DOMAIN,
            "turn_off",
            {"entity_id": entity_id},
            blocking=True,
        )
        
        # Test volume_set service
        await hass.services.async_call(
            MEDIA_PLAYER_DOMAIN,
            "volume_set",
            {"entity_id": entity_id, "volume_level": 0.5},
            blocking=True,
        )
        
        # Test volume_mute service
        await hass.services.async_call(
            MEDIA_PLAYER_DOMAIN,
            "volume_mute",
            {"entity_id": entity_id, "is_volume_muted": True},
            blocking=True,
        )
        
        # Test select_source service
        await hass.services.async_call(
            MEDIA_PLAYER_DOMAIN,
            "select_source",
            {"entity_id": entity_id, "source": "CD Player"},
            blocking=True,
        )


async def test_state_updates_through_coordinator(hass, mock_connection_factory):
    """Test state updates propagate through coordinator to entities."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        mock_connection_class.return_value = mock_connection
        
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        
        await hass.async_block_till_done()
        
        coordinator = hass.data[DOMAIN][config_entry.entry_id]
        entity_id = "media_player.test_avr"
        
        # Test power state update
        coordinator.data = {"power": False, "available": True}
        coordinator.async_update_listeners()
        await hass.async_block_till_done()
        
        state = hass.states.get(entity_id)
        assert state.state == STATE_OFF
        
        # Test volume update
        coordinator.data = {"power": True, "volume": 75, "available": True}
        coordinator.async_update_listeners()
        await hass.async_block_till_done()
        
        state = hass.states.get(entity_id)
        assert state.state == STATE_ON
        assert abs(float(state.attributes["volume_level"]) - 0.757) < 0.01
        
        # Test source update
        coordinator.data = {
            "power": True,
            "source": "BD",
            "available": True
        }
        coordinator.async_update_listeners()
        await hass.async_block_till_done()
        
        state = hass.states.get(entity_id)
        assert state.attributes["source"] == "Blu-ray Player"


async def test_multiple_zones_integration(hass, mock_connection_factory):
    """Test integration with multiple zones."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
            "zones": [1, 2],
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        mock_connection_class.return_value = mock_connection
        
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        
        await hass.async_block_till_done()
        
        # Both zone entities should be created
        zone1_state = hass.states.get("media_player.test_avr")
        zone2_state = hass.states.get("media_player.test_avr_zone_2")
        
        assert zone1_state is not None
        assert zone2_state is not None
        
        # Test zone-specific updates
        coordinator = hass.data[DOMAIN][config_entry.entry_id]
        coordinator.data = {"power": True, "available": True}
        coordinator.async_update_listeners()
        await hass.async_block_till_done()
        
        # Both entities should reflect the update
        zone1_state = hass.states.get("media_player.test_avr")
        zone2_state = hass.states.get("media_player.test_avr_zone_2")
        
        assert zone1_state.state == STATE_ON
        assert zone2_state.state == STATE_ON


async def test_broadcast_message_handling(hass, mock_connection_factory):
    """Test integration handles broadcast messages properly."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        mock_connection_class.return_value = mock_connection
        
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        
        await hass.async_block_till_done()
        
        coordinator = hass.data[DOMAIN][config_entry.entry_id]
        entity_id = "media_player.test_avr"
        
        # Simulate broadcast message reception
        # This would normally come from the connection's broadcast listener
        coordinator.data = {"power": False, "available": True}
        coordinator.async_update_listeners()
        await hass.async_block_till_done()
        
        state = hass.states.get(entity_id)
        assert state.state == STATE_OFF
        
        # Simulate another broadcast message
        coordinator.data = {"power": True, "volume": 25, "mute": True, "available": True}
        coordinator.async_update_listeners()
        await hass.async_block_till_done()
        
        state = hass.states.get(entity_id)
        assert state.state == STATE_ON
        assert state.attributes["is_volume_muted"] is True


async def test_error_recovery_integration(hass, mock_connection_factory):
    """Test integration recovery from various error conditions."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        mock_connection_class.return_value = mock_connection
        
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        
        await hass.async_block_till_done()
        
        coordinator = hass.data[DOMAIN][config_entry.entry_id]
        entity_id = "media_player.test_avr"
        
        # Simulate command failure
        mock_connection.send_command.side_effect = ConnectionError("Command failed")
        
        # Service call should not crash the integration
        await hass.services.async_call(
            MEDIA_PLAYER_DOMAIN,
            "turn_on",
            {"entity_id": entity_id},
            blocking=True,
        )
        
        # Entity should still be available
        state = hass.states.get(entity_id)
        assert state is not None
        
        # Recovery: connection works again
        mock_connection.send_command.side_effect = None
        mock_connection.send_command.return_value = AsyncMock()
        
        # Subsequent commands should work
        await hass.services.async_call(
            MEDIA_PLAYER_DOMAIN,
            "turn_off",
            {"entity_id": entity_id},
            blocking=True,
        )


async def test_config_entry_reload(hass, mock_connection_factory):
    """Test config entry reload functionality."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        mock_connection_class.return_value = mock_connection
        
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        
        await hass.async_block_till_done()
        
        # Verify initial state
        state = hass.states.get("media_player.test_avr")
        assert state is not None
        
        # Reload the config entry
        assert await hass.config_entries.async_reload(config_entry.entry_id)
        
        await hass.async_block_till_done()
        
        # Verify entity is still available after reload
        state = hass.states.get("media_player.test_avr")
        assert state is not None
        assert config_entry.state == ConfigEntryState.LOADED


async def test_options_update_integration(hass, mock_connection_factory):
    """Test integration options updates."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
        options={"update_interval": 30},
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        mock_connection_class.return_value = mock_connection
        
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        
        await hass.async_block_till_done()
        
        coordinator = hass.data[DOMAIN][config_entry.entry_id]
        initial_interval = coordinator.update_interval
        
        # Update options
        hass.config_entries.async_update_entry(
            config_entry,
            options={"update_interval": 60}
        )
        
        await hass.async_block_till_done()
        
        # Verify update interval changed
        assert coordinator.update_interval != initial_interval
        assert coordinator.update_interval.total_seconds() == 60


async def test_device_info_integration(hass, mock_connection_factory):
    """Test device info is properly set up in integration."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        mock_connection_class.return_value = mock_connection
        
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        
        await hass.async_block_till_done()
        
        # Get device registry
        device_registry = hass.helpers.device_registry.async_get(hass)
        devices = device_registry.devices
        
        # Find our device
        our_device = None
        for device in devices.values():
            if device.name == "Arcam AVR11":
                our_device = device
                break
        
        assert our_device is not None
        assert our_device.manufacturer == "Arcam"
        assert our_device.model == "AVR11"
        assert our_device.sw_version == "2.01"
        assert (DOMAIN, config_entry.entry_id) in our_device.identifiers