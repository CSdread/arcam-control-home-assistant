"""Test Arcam AVR media player."""
import pytest
from unittest.mock import AsyncMock

from homeassistant.components.media_player import (
    MediaPlayerState,
    MediaPlayerEntityFeature,
)
from homeassistant.components.arcam_avr.media_player import ArcamAvrMediaPlayer


class TestArcamAvrMediaPlayer:
    """Test the media player entity."""
    
    @pytest.fixture
    def media_player(self, mock_coordinator, mock_config_entry):
        """Create media player entity."""
        return ArcamAvrMediaPlayer(mock_coordinator, mock_config_entry, zone=1)
    
    def test_device_info(self, media_player, mock_coordinator):
        """Test device info properties."""
        device_info = media_player.device_info
        assert device_info["name"] == "Arcam AVR11"
        assert device_info["manufacturer"] == "Arcam"
        assert device_info["model"] == "AVR11"
        assert device_info["sw_version"] == "2.01"
    
    def test_unique_id(self, media_player):
        """Test unique ID generation."""
        assert media_player.unique_id == "test_entry_id_zone_1"
    
    def test_name(self, media_player):
        """Test entity name."""
        assert media_player.name == "Test AVR"
    
    def test_state_on(self, media_player, mock_coordinator):
        """Test power on state."""
        mock_coordinator.data = {"power": True, "available": True}
        mock_coordinator.last_update_success = True
        assert media_player.state == MediaPlayerState.ON
    
    def test_state_off(self, media_player, mock_coordinator):
        """Test power off state."""
        mock_coordinator.data = {"power": False, "available": True}
        mock_coordinator.last_update_success = True
        assert media_player.state == MediaPlayerState.OFF
    
    def test_state_unavailable(self, media_player, mock_coordinator):
        """Test unavailable state."""
        mock_coordinator.last_update_success = False
        assert media_player.state == MediaPlayerState.OFF
        assert media_player.available is False
    
    def test_volume_level(self, media_player, mock_coordinator):
        """Test volume level conversion."""
        mock_coordinator.data = {"volume": 50}
        # Device volume 50 -> HA volume 50/99 ≈ 0.505
        assert abs(media_player.volume_level - 0.505) < 0.01
        
        mock_coordinator.data = {"volume": 0}
        assert media_player.volume_level == 0.0
        
        mock_coordinator.data = {"volume": 99}
        assert media_player.volume_level == 1.0
    
    def test_volume_level_none(self, media_player, mock_coordinator):
        """Test volume level when data is None."""
        mock_coordinator.data = {"volume": None}
        assert media_player.volume_level is None
        
        mock_coordinator.data = None
        assert media_player.volume_level is None
    
    def test_is_volume_muted(self, media_player, mock_coordinator):
        """Test mute property."""
        mock_coordinator.data = {"mute": True}
        assert media_player.is_volume_muted is True
        
        mock_coordinator.data = {"mute": False}
        assert media_player.is_volume_muted is False
        
        mock_coordinator.data = {"mute": None}
        assert media_player.is_volume_muted is None
    
    def test_source(self, media_player, mock_coordinator):
        """Test source property."""
        mock_coordinator.data = {"source": "BD"}
        assert media_player.source == "Blu-ray Player"
        
        mock_coordinator.data = {"source": "CD"}
        assert media_player.source == "CD Player"
        
        mock_coordinator.data = {"source": "UNKNOWN"}
        assert media_player.source == "UNKNOWN"
    
    def test_source_list(self, media_player):
        """Test source list property."""
        source_list = media_player.source_list
        assert isinstance(source_list, list)
        assert "CD Player" in source_list
        assert "Blu-ray Player" in source_list
        assert len(source_list) > 0
    
    def test_supported_features(self, media_player):
        """Test supported features."""
        features = media_player.supported_features
        assert features & MediaPlayerEntityFeature.TURN_ON
        assert features & MediaPlayerEntityFeature.TURN_OFF
        assert features & MediaPlayerEntityFeature.VOLUME_SET
        assert features & MediaPlayerEntityFeature.VOLUME_MUTE
        assert features & MediaPlayerEntityFeature.SELECT_SOURCE
    
    def test_extra_state_attributes(self, media_player, mock_coordinator):
        """Test extra state attributes."""
        mock_coordinator.data = {"source": "BD"}
        attributes = media_player.extra_state_attributes
        
        assert attributes["source"] == "BD"
        assert attributes["model"] == "AVR11"
        assert attributes["version"] == "2.01"
    
    async def test_turn_on(self, media_player, mock_coordinator):
        """Test turn on command."""
        mock_coordinator.async_send_command = AsyncMock(return_value=True)
        
        await media_player.async_turn_on()
        
        mock_coordinator.async_send_command.assert_called_once()
        args = mock_coordinator.async_send_command.call_args[0]
        # Check that power_on command function was called
        assert args[1] == 1  # zone parameter
    
    async def test_turn_off(self, media_player, mock_coordinator):
        """Test turn off command."""
        mock_coordinator.async_send_command = AsyncMock(return_value=True)
        
        await media_player.async_turn_off()
        
        mock_coordinator.async_send_command.assert_called_once()
        args = mock_coordinator.async_send_command.call_args[0]
        assert args[1] == 1  # zone parameter
    
    async def test_set_volume_level(self, media_player, mock_coordinator):
        """Test volume setting."""
        mock_coordinator.async_send_command = AsyncMock(return_value=True)
        
        await media_player.async_set_volume_level(0.75)
        
        mock_coordinator.async_send_command.assert_called_once()
        args = mock_coordinator.async_send_command.call_args[0]
        # Volume should be converted from 0.75 to ~74 (device scale)
        assert args[1] == 74  # 0.75 * 99 = 74.25 -> 74
        assert args[2] == 1   # zone parameter
    
    async def test_set_volume_level_boundaries(self, media_player, mock_coordinator):
        """Test volume setting at boundaries."""
        mock_coordinator.async_send_command = AsyncMock(return_value=True)
        
        # Test minimum
        await media_player.async_set_volume_level(0.0)
        args = mock_coordinator.async_send_command.call_args[0]
        assert args[1] == 0
        
        # Test maximum
        await media_player.async_set_volume_level(1.0)
        args = mock_coordinator.async_send_command.call_args[0]
        assert args[1] == 99
    
    async def test_mute_volume_change_state(self, media_player, mock_coordinator):
        """Test mute volume when state changes."""
        mock_coordinator.data = {"mute": False}
        mock_coordinator.async_send_command = AsyncMock(return_value=True)
        
        await media_player.async_mute_volume(True)
        
        mock_coordinator.async_send_command.assert_called_once()
    
    async def test_mute_volume_same_state(self, media_player, mock_coordinator):
        """Test mute volume when state is already correct."""
        mock_coordinator.data = {"mute": True}
        mock_coordinator.async_send_command = AsyncMock(return_value=True)
        
        await media_player.async_mute_volume(True)
        
        # Should not call send_command when state is already correct
        mock_coordinator.async_send_command.assert_not_called()
    
    async def test_select_source_friendly_name(self, media_player, mock_coordinator):
        """Test source selection with friendly name."""
        mock_coordinator.async_send_command = AsyncMock(return_value=True)
        
        await media_player.async_select_source("CD Player")
        
        mock_coordinator.async_send_command.assert_called_once()
        args = mock_coordinator.async_send_command.call_args[0]
        assert args[1] == "CD"  # Should convert friendly name to source code
        assert args[2] == 1     # zone parameter
    
    async def test_select_source_direct_code(self, media_player, mock_coordinator):
        """Test source selection with direct source code."""
        mock_coordinator.async_send_command = AsyncMock(return_value=True)
        
        await media_player.async_select_source("BD")
        
        mock_coordinator.async_send_command.assert_called_once()
        args = mock_coordinator.async_send_command.call_args[0]
        assert args[1] == "BD"  # Should use direct source code
        assert args[2] == 1     # zone parameter
    
    async def test_select_source_invalid(self, media_player, mock_coordinator):
        """Test invalid source selection."""
        mock_coordinator.async_send_command = AsyncMock(return_value=True)
        
        # Should not raise exception, just log error
        await media_player.async_select_source("INVALID_SOURCE")
        
        # Should not call send_command for invalid source
        mock_coordinator.async_send_command.assert_not_called()
    
    async def test_async_update(self, media_player, mock_coordinator):
        """Test manual update."""
        mock_coordinator.async_request_refresh = AsyncMock()
        
        await media_player.async_update()
        
        mock_coordinator.async_request_refresh.assert_called_once()
    
    def test_zone_2_entity_name(self, mock_coordinator, mock_config_entry):
        """Test Zone 2 entity naming."""
        media_player = ArcamAvrMediaPlayer(mock_coordinator, mock_config_entry, zone=2)
        assert media_player.name == "Test AVR Zone 2"
        assert media_player.unique_id == "test_entry_id_zone_2"
    
    def test_extra_attributes_zone_2(self, mock_coordinator, mock_config_entry):
        """Test extra attributes include zone for Zone 2."""
        media_player = ArcamAvrMediaPlayer(mock_coordinator, mock_config_entry, zone=2)
        mock_coordinator.data = {"source": "BD"}
        
        attributes = media_player.extra_state_attributes
        assert attributes["zone"] == 2