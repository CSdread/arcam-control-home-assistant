"""Test Arcam command definitions."""
import pytest

from homeassistant.components.arcam_avr.arcam.commands import (
    ArcamCommands,
    get_source_name,
    get_source_code,
    get_available_sources,
    is_valid_source,
    decode_volume_response,
    decode_power_response,
    decode_mute_response,
    decode_source_response,
    decode_version_response,
    POWER,
    VOLUME,
    MUTE,
    SOURCE,
    RC5_SIMULATE,
)


class TestArcamCommands:
    """Test command factory methods."""
    
    def test_power_on(self):
        """Test power on command creation."""
        command = ArcamCommands.power_on(1)
        assert command.zone == 1
        assert command.command_code == POWER
        assert command.data == bytes([0x01])
    
    def test_power_off(self):
        """Test power off command creation."""
        command = ArcamCommands.power_off(1)
        assert command.zone == 1
        assert command.command_code == POWER
        assert command.data == bytes([0x00])
    
    def test_get_power_status(self):
        """Test get power status command creation."""
        command = ArcamCommands.get_power_status(1)
        assert command.zone == 1
        assert command.command_code == POWER
        assert command.data == bytes([0xF0])
    
    def test_set_volume(self):
        """Test set volume command creation."""
        command = ArcamCommands.set_volume(50, 1)
        assert command.zone == 1
        assert command.command_code == VOLUME
        assert command.data == bytes([50])
    
    def test_set_volume_validation(self):
        """Test volume validation."""
        with pytest.raises(ValueError, match="Invalid volume"):
            ArcamCommands.set_volume(-1, 1)
        
        with pytest.raises(ValueError, match="Invalid volume"):
            ArcamCommands.set_volume(100, 1)
    
    def test_get_volume(self):
        """Test get volume command creation."""
        command = ArcamCommands.get_volume(1)
        assert command.zone == 1
        assert command.command_code == VOLUME
        assert command.data == bytes([0xF0])
    
    def test_get_mute_status(self):
        """Test get mute status command creation."""
        command = ArcamCommands.get_mute_status(1)
        assert command.zone == 1
        assert command.command_code == MUTE
        assert command.data == bytes([0xF0])
    
    def test_toggle_mute(self):
        """Test toggle mute command creation."""
        command = ArcamCommands.toggle_mute(1)
        assert command.zone == 1
        assert command.command_code == RC5_SIMULATE
        assert command.data == bytes([0x10, 0x0D])
    
    def test_get_source(self):
        """Test get source command creation."""
        command = ArcamCommands.get_source(1)
        assert command.zone == 1
        assert command.command_code == SOURCE
        assert command.data == bytes([0xF0])
    
    def test_select_source(self):
        """Test select source command creation."""
        command = ArcamCommands.select_source("CD", 1)
        assert command.zone == 1
        assert command.command_code == RC5_SIMULATE
        assert command.data == bytes([0x10, 0x76])
    
    def test_select_source_case_insensitive(self):
        """Test select source is case insensitive."""
        command = ArcamCommands.select_source("cd", 1)
        assert command.data == bytes([0x10, 0x76])
    
    def test_select_source_invalid(self):
        """Test invalid source selection."""
        with pytest.raises(ValueError, match="Invalid source"):
            ArcamCommands.select_source("INVALID", 1)
    
    def test_get_software_version(self):
        """Test get software version command creation."""
        command = ArcamCommands.get_software_version(1)
        assert command.zone == 1
        assert command.command_code == 0x04
        assert command.data == bytes([0xF0])
    
    def test_simulate_rc5(self):
        """Test generic RC5 simulation."""
        command = ArcamCommands.simulate_rc5(0x10, 0x76, 1)
        assert command.zone == 1
        assert command.command_code == RC5_SIMULATE
        assert command.data == bytes([0x10, 0x76])
    
    def test_simulate_rc5_validation(self):
        """Test RC5 simulation validation."""
        with pytest.raises(ValueError, match="Invalid RC5 data1"):
            ArcamCommands.simulate_rc5(-1, 0x76, 1)
        
        with pytest.raises(ValueError, match="Invalid RC5 data2"):
            ArcamCommands.simulate_rc5(0x10, 256, 1)
    
    def test_zone_validation(self):
        """Test zone validation across all commands."""
        with pytest.raises(ValueError, match="Invalid zone"):
            ArcamCommands.power_on(0)
        
        with pytest.raises(ValueError, match="Invalid zone"):
            ArcamCommands.power_on(3)


class TestSourceMapping:
    """Test source mapping functions."""
    
    def test_get_source_name(self):
        """Test getting source name from code."""
        assert get_source_name(0x00) == "CD"
        assert get_source_name(0x01) == "BD"
        assert get_source_name(0xFF) is None
    
    def test_get_source_code(self):
        """Test getting source code from name."""
        assert get_source_code("CD") == 0x00
        assert get_source_code("BD") == 0x01
        assert get_source_code("cd") == 0x00  # Case insensitive
        assert get_source_code("INVALID") is None
    
    def test_get_available_sources(self):
        """Test getting available sources."""
        sources = get_available_sources()
        assert isinstance(sources, list)
        assert "CD" in sources
        assert "BD" in sources
        assert len(sources) > 0
    
    def test_is_valid_source(self):
        """Test source validation."""
        assert is_valid_source("CD") is True
        assert is_valid_source("cd") is True  # Case insensitive
        assert is_valid_source("INVALID") is False


class TestResponseDecoding:
    """Test response decoding functions."""
    
    def test_decode_volume_response(self):
        """Test volume response decoding."""
        assert decode_volume_response(bytes([50])) == 50
        assert decode_volume_response(bytes([0])) == 0
        assert decode_volume_response(bytes([99])) == 99
        assert decode_volume_response(bytes()) is None
        assert decode_volume_response(bytes([1, 2])) is None
    
    def test_decode_power_response(self):
        """Test power response decoding."""
        assert decode_power_response(bytes([0x01])) is True
        assert decode_power_response(bytes([0x00])) is False
        assert decode_power_response(bytes()) is None
        assert decode_power_response(bytes([1, 2])) is None
    
    def test_decode_mute_response(self):
        """Test mute response decoding."""
        assert decode_mute_response(bytes([0x01])) is True
        assert decode_mute_response(bytes([0x00])) is False
        assert decode_mute_response(bytes()) is None
        assert decode_mute_response(bytes([1, 2])) is None
    
    def test_decode_source_response(self):
        """Test source response decoding."""
        assert decode_source_response(bytes([0x00])) == "CD"
        assert decode_source_response(bytes([0x01])) == "BD"
        assert decode_source_response(bytes([0xFF])) is None
        assert decode_source_response(bytes()) is None
        assert decode_source_response(bytes([1, 2])) is None
    
    def test_decode_version_response(self):
        """Test version response decoding."""
        version_bytes = bytes([0x32, 0x2E, 0x30, 0x31, 0x2F, 0x30, 0x2E, 0x30, 0x33, 0x2F, 0x31, 0x2E])
        assert decode_version_response(version_bytes) == "2.01/0.03/1."
        
        # Test with null termination
        version_with_null = version_bytes + bytes([0x00])
        assert decode_version_response(version_with_null) == "2.01/0.03/1."
        
        # Test invalid length
        assert decode_version_response(bytes([1, 2, 3])) is None
        
        # Test non-ASCII
        invalid_bytes = bytes([0xFF] * 12)
        assert decode_version_response(invalid_bytes) is None