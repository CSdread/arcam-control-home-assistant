"""Test Arcam AVR integration init."""
import pytest
from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.components.arcam_avr import (
    async_setup_entry,
    async_unload_entry,
    async_reload_entry,
    async_migrate_entry,
)
from homeassistant.components.arcam_avr.const import DOMAIN
from homeassistant.exceptions import ConfigEntryNotReady

from tests.common import MockConfigEntry


async def test_setup_entry_success(hass, mock_config_entry, mock_connection_factory):
    """Test successful setup of config entry."""
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection_class.return_value = await mock_connection_factory("192.168.1.100", 50000)
        
        assert await async_setup_entry(hass, mock_config_entry)
        
        # Check that coordinator is stored in hass.data
        assert DOMAIN in hass.data
        assert mock_config_entry.entry_id in hass.data[DOMAIN]
        
        coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]
        assert coordinator.host == "192.168.1.100"
        assert coordinator.port == 50000


async def test_setup_entry_connection_failed(hass, mock_config_entry):
    """Test setup with connection failure."""
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = AsyncMock()
        mock_connection.async_config_entry_first_refresh.side_effect = ConnectionError("Connection failed")
        mock_connection_class.return_value = mock_connection
        
        with patch(
            "homeassistant.components.arcam_avr.coordinator.ArcamAvrCoordinator.async_config_entry_first_refresh"
        ) as mock_refresh:
            mock_refresh.side_effect = ConnectionError("Connection failed")
            
            with pytest.raises(ConfigEntryNotReady):
                await async_setup_entry(hass, mock_config_entry)


async def test_setup_entry_platform_forward(hass, mock_config_entry, mock_connection_factory):
    """Test that platforms are forwarded correctly."""
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection_class.return_value = await mock_connection_factory("192.168.1.100", 50000)
        
        with patch(
            "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups"
        ) as mock_forward:
            await async_setup_entry(hass, mock_config_entry)
            
            mock_forward.assert_called_once()
            call_args = mock_forward.call_args[0]
            assert call_args[0] == mock_config_entry
            assert "media_player" in call_args[1]


async def test_unload_entry_success(hass, mock_config_entry, mock_coordinator):
    """Test successful unloading of config entry."""
    # Setup initial state
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}
    mock_coordinator.async_shutdown = AsyncMock()
    
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms"
    ) as mock_unload:
        mock_unload.return_value = True
        
        result = await async_unload_entry(hass, mock_config_entry)
        
        assert result is True
        mock_coordinator.async_shutdown.assert_called_once()
        
        # Check that data is cleaned up
        assert mock_config_entry.entry_id not in hass.data.get(DOMAIN, {})


async def test_unload_entry_platform_failed(hass, mock_config_entry, mock_coordinator):
    """Test unload when platform unloading fails."""
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}
    
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms"
    ) as mock_unload:
        mock_unload.return_value = False
        
        result = await async_unload_entry(hass, mock_config_entry)
        
        assert result is False
        # Coordinator should not be cleaned up if platform unload failed
        assert mock_config_entry.entry_id in hass.data[DOMAIN]


async def test_unload_entry_domain_cleanup(hass, mock_config_entry, mock_coordinator):
    """Test that domain data is removed when no entries remain."""
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}
    mock_coordinator.async_shutdown = AsyncMock()
    
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms"
    ) as mock_unload:
        mock_unload.return_value = True
        
        await async_unload_entry(hass, mock_config_entry)
        
        # Domain should be completely removed from hass.data
        assert DOMAIN not in hass.data


async def test_reload_entry(hass, mock_config_entry, mock_coordinator):
    """Test reloading config entry."""
    with patch(
        "homeassistant.components.arcam_avr.async_unload_entry"
    ) as mock_unload:
        mock_unload.return_value = True
        
        with patch(
            "homeassistant.components.arcam_avr.async_setup_entry"
        ) as mock_setup:
            mock_setup.return_value = True
            
            await async_reload_entry(hass, mock_config_entry)
            
            mock_unload.assert_called_once_with(hass, mock_config_entry)
            mock_setup.assert_called_once_with(hass, mock_config_entry)


async def test_migrate_entry_version_1(hass):
    """Test migration for version 1 (no migration needed)."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        data={"host": "192.168.1.100"},
    )
    
    result = await async_migrate_entry(hass, config_entry)
    assert result is True


async def test_migrate_entry_unknown_version(hass):
    """Test migration for unknown version."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=999,
        data={"host": "192.168.1.100"},
    )
    
    result = await async_migrate_entry(hass, config_entry)
    assert result is False


async def test_options_updated(hass, mock_config_entry, mock_coordinator):
    """Test options update handling."""
    from homeassistant.components.arcam_avr import async_options_updated
    
    # Setup coordinator in hass data
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}
    mock_coordinator.async_request_refresh = AsyncMock()
    
    # Update config entry options
    mock_config_entry.options = {"update_interval": 60}
    
    await async_options_updated(hass, mock_config_entry)
    
    # Check that coordinator update interval was updated
    assert mock_coordinator.update_interval.total_seconds() == 60
    mock_coordinator.async_request_refresh.assert_called_once()


async def test_options_updated_no_changes(hass, mock_config_entry, mock_coordinator):
    """Test options update with no changes."""
    from homeassistant.components.arcam_avr import async_options_updated
    
    hass.data[DOMAIN] = {mock_config_entry.entry_id: mock_coordinator}
    mock_coordinator.async_request_refresh = AsyncMock()
    
    # No options set
    mock_config_entry.options = {}
    
    await async_options_updated(hass, mock_config_entry)
    
    # Should still trigger refresh even with no changes
    mock_coordinator.async_request_refresh.assert_called_once()