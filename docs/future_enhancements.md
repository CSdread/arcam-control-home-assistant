# Future Enhancement Roadmap

## Overview

This document outlines potential future enhancements for the Arcam AVR Home Assistant integration beyond the initial Phase 1 implementation. These features are documented to ensure the initial architecture supports extensibility.

## Phase 2: Extended Audio Control

### Audio Processing Entities

#### Select Entities for Audio Modes
```python
# decode_mode entity (select.py)
class ArcamDecodeMode(CoordinatorEntity, SelectEntity):
    """Decode mode selection entity."""
    
    @property
    def options(self) -> list[str]:
        return [
            "Stereo",
            "Stereo Direct", 
            "Dolby Surround",
            "DTS Neural:X",
            "Virtual Height",
            "Multi Channel Stereo",
            "Auro 2D Surround",
            "Auro 3D",
            "Auro Native"
        ]
```

#### Number Entities for Adjustments
```python
# number.py
class ArcamBassControl(CoordinatorEntity, NumberEntity):
    """Bass adjustment entity."""
    
    @property
    def native_min_value(self) -> float:
        return -12.0
        
    @property
    def native_max_value(self) -> float:
        return 12.0
        
    @property 
    def native_step(self) -> float:
        return 1.0
        
class ArcamTrebleControl(CoordinatorEntity, NumberEntity):
    """Treble adjustment entity."""
    # Similar implementation
    
class ArcamBalanceControl(CoordinatorEntity, NumberEntity):
    """Balance adjustment entity."""
    
    @property
    def native_min_value(self) -> float:
        return -6.0
        
    @property
    def native_max_value(self) -> float:
        return 6.0
```

### New Protocol Commands (Input Config 0x28)

```python
# Additional commands for audio control
class ArcamAudioCommands:
    """Extended audio control commands."""
    
    INPUT_CONFIG = 0x28
    
    @classmethod
    def set_decode_mode(cls, mode: str, zone: int = 1) -> ArcamCommand:
        """Set decode mode for 2-channel content."""
        mode_map = {
            "Stereo": 0x01,
            "Stereo Direct": 0x02,
            "Dolby Surround": 0x03,
            "DTS Neural:X": 0x04,
            "Virtual Height": 0x05,
            "Multi Channel Stereo": 0x06,
            "Auro 2D Surround": 0x07,
            "Auro 3D": 0x09,
            "Auro Native": 0x0A
        }
        # Implementation details...
        
    @classmethod
    def set_bass(cls, level: int, zone: int = 1) -> ArcamCommand:
        """Set bass level (-12 to +12 dB)."""
        # Implementation details...
        
    @classmethod
    def set_treble(cls, level: int, zone: int = 1) -> ArcamCommand:
        """Set treble level (-12 to +12 dB)."""
        # Implementation details...
```

## Phase 3: Video and HDMI Control

### HDMI Configuration Entity
```python
# Additional entities for HDMI settings
class ArcamHdmiSettings(CoordinatorEntity, Entity):
    """HDMI configuration entity."""
    
    async def async_set_hdmi_output(self, output: str):
        """Set HDMI output configuration."""
        # Output options: "Out 1 & 2", "Out 1", "Out 2"
        
    async def async_set_cec_control(self, enabled: bool):
        """Enable/disable CEC control."""
        
    async def async_set_arc_control(self, mode: str):
        """Set ARC control mode."""
        # Modes: "Off", "Auto"
```

### Video Processing Commands (0x2E, 0x42)
```python
class ArcamVideoCommands:
    """Video processing commands."""
    
    HDMI_SETTINGS = 0x2E
    VIDEO_PARAMS = 0x42
    
    @classmethod
    def get_video_info(cls, zone: int = 1) -> ArcamCommand:
        """Get current video parameters."""
        # Returns resolution, refresh rate, aspect ratio, color space
        
    @classmethod
    def set_hdmi_config(cls, config: dict, zone: int = 1) -> ArcamCommand:
        """Set HDMI configuration."""
        # OSD on/off, output selection, CEC, ARC settings
```

## Phase 4: Speaker Management

### Speaker Configuration Entities
```python
# Speaker setup entities
class ArcamSpeakerConfig(CoordinatorEntity, Entity):
    """Speaker configuration management."""
    
    async def async_set_speaker_size(self, channel: str, size: str):
        """Set speaker size (Large/Small/None)."""
        # Channels: L/R, Centre, Surround, Back, Height, Subwoofer
        
    async def async_set_speaker_distance(self, channel: str, distance: float):
        """Set speaker distance."""
        
    async def async_run_speaker_test(self, channel: str):
        """Run test tone for speaker."""

class ArcamRoomEQ(CoordinatorEntity, SelectEntity):
    """Room EQ selection."""
    
    @property
    def options(self) -> list[str]:
        return ["Off", "Room EQ 1", "Room EQ 2", "Room EQ 3"]
```

### Speaker Commands (0x2A, 0x2B, 0x2C)
```python
class ArcamSpeakerCommands:
    """Speaker management commands."""
    
    SPEAKER_TYPES = 0x2A
    SPEAKER_DISTANCES = 0x2B  
    SPEAKER_LEVELS = 0x2C
    
    @classmethod
    def set_speaker_type(cls, channel: int, speaker_type: int, zone: int = 1):
        """Set speaker type and crossover frequency."""
        
    @classmethod
    def set_speaker_level(cls, channel: int, level: float, zone: int = 1):
        """Set speaker level trim (-10dB to +10dB)."""
```

## Phase 5: Network and Streaming

### Network Playback Support
```python
class ArcamNetworkPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Network playback control entity."""
    
    @property
    def media_content_type(self) -> str:
        """Content type of current playing media."""
        
    @property
    def media_title(self) -> str:
        """Title of current playing media."""
        
    async def async_media_play(self):
        """Send play command."""
        
    async def async_media_pause(self):
        """Send pause command."""
        
    async def async_media_stop(self):
        """Send stop command."""
```

### Network Commands (0x1C, 0x64)
```python
class ArcamNetworkCommands:
    """Network playback commands."""
    
    NETWORK_STATUS = 0x1C
    NOW_PLAYING = 0x64
    
    @classmethod
    def get_playback_status(cls, zone: int = 1) -> ArcamCommand:
        """Get network playback status."""
        
    @classmethod
    def get_now_playing(cls, zone: int = 1) -> ArcamCommand:
        """Get current track information."""
```

## Phase 6: Tuner Control

### Radio Entities
```python
class ArcamTunerControl(CoordinatorEntity, MediaPlayerEntity):
    """FM/DAB tuner control."""
    
    async def async_select_preset(self, preset: int):
        """Select radio preset (1-50)."""
        
    async def async_scan_up(self):
        """Scan for next station."""
        
    async def async_scan_down(self):
        """Scan for previous station."""

class ArcamPresetSelect(CoordinatorEntity, SelectEntity):
    """Radio preset selection."""
    
    @property
    def options(self) -> list[str]:
        """Return available presets."""
        # Load from device preset list
```

### Tuner Commands (0x15, 0x16, 0x1B)
```python
class ArcamTunerCommands:
    """Tuner control commands."""
    
    TUNER_PRESET = 0x15
    TUNE = 0x16
    PRESET_DETAILS = 0x1B
    
    @classmethod
    def select_preset(cls, preset_num: int, zone: int = 1) -> ArcamCommand:
        """Select tuner preset."""
        
    @classmethod
    def tune_frequency(cls, frequency: float, band: str, zone: int = 1) -> ArcamCommand:
        """Tune to specific frequency."""
```

## Phase 7: Zone 2 Support

### Multi-Zone Architecture
```python
class ArcamZone2MediaPlayer(ArcamAvrMediaPlayer):
    """Zone 2 media player entity."""
    
    def __init__(self, coordinator: ArcamAvrCoordinator):
        super().__init__(coordinator, zone=2)
        
    @property
    def available(self) -> bool:
        """Zone 2 availability depends on model."""
        # Not available on AVR5, AVR10
        return self.coordinator.data.get("model") not in ["AVR5", "AVR10"]
```

### Zone-Specific Commands
```python
# Zone 2 RC5 commands (system 23)
ZONE2_RC5_COMMANDS = {
    "power_on": (0x17, 0x7B),
    "power_off": (0x17, 0x7C), 
    "volume_up": (0x17, 0x01),
    "volume_down": (0x17, 0x02),
    "mute": (0x17, 0x03),
    # Source selection commands...
}
```

## Phase 8: Advanced Features

### Diagnostic Support
```python
class ArcamDiagnostics:
    """Diagnostic information for integration."""
    
    async def async_get_diagnostics(self) -> dict:
        """Return diagnostic information."""
        return {
            "device_info": await self._get_device_info(),
            "connection_status": await self._get_connection_status(),
            "recent_commands": self._get_command_history(),
            "error_log": self._get_error_log(),
            "performance_metrics": self._get_performance_metrics()
        }
```

### Configuration Options
```python
class ArcamOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for advanced settings."""
    
    async def async_step_init(self, user_input=None):
        """Manage advanced options."""
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional("update_interval", default=30): int,
                vol.Optional("command_timeout", default=3): int,
                vol.Optional("enable_zone2", default=False): bool,
                vol.Optional("enable_diagnostics", default=False): bool,
            })
        )
```

## Implementation Considerations

### Architecture Extensions

#### Entity Platform Registration
```python
# Extended __init__.py platform list
PLATFORMS = [
    "media_player",  # Phase 1
    "select",        # Phase 2: Decode modes, presets
    "number",        # Phase 2: Bass/treble/balance
    "switch",        # Phase 3: HDMI features
    "sensor",        # Phase 4: Video info, signal status
]
```

#### Command Organization
```python
# Organized command structure
arcam/
├── commands/
│   ├── __init__.py
│   ├── basic.py          # Phase 1 commands
│   ├── audio.py          # Phase 2 audio commands  
│   ├── video.py          # Phase 3 video commands
│   ├── speaker.py        # Phase 4 speaker commands
│   ├── network.py        # Phase 5 network commands
│   └── tuner.py          # Phase 6 tuner commands
```

### Data Model Extensions

#### Enhanced Coordinator Data
```python
# Extended data structure for advanced features
EXTENDED_DATA_MODEL = {
    # Phase 1 (current)
    "power": bool,
    "volume": int,
    "mute": bool, 
    "source": str,
    "available": bool,
    "model": str,
    "version": str,
    
    # Phase 2 additions
    "decode_mode": str,
    "bass": int,
    "treble": int,
    "balance": int,
    "room_eq": str,
    
    # Phase 3 additions  
    "hdmi_output": str,
    "video_resolution": str,
    "video_refresh_rate": int,
    "cec_enabled": bool,
    
    # Phase 4 additions
    "speaker_config": dict,
    "speaker_levels": dict,
    "test_tone_active": bool,
    
    # Phase 5 additions
    "network_playing": bool,
    "current_track": str,
    "track_time": int,
    
    # Phase 6 additions
    "tuner_frequency": float,
    "tuner_preset": int,
    "rds_info": str,
    
    # Phase 7 additions
    "zone2": dict,  # Separate zone 2 state
}
```

### Backwards Compatibility

#### Version Management
```python
class ArcamIntegrationVersion:
    """Manage integration version compatibility."""
    
    FEATURE_SUPPORT = {
        "basic_control": ["AVR5", "AVR10", "AVR20", "AVR30", "AVR40", 
                         "AVR11", "AVR21", "AVR31", "AVR41"],
        "imax_enhanced": ["AVR10", "AVR20", "AVR30", "AVR40",
                         "AVR11", "AVR21", "AVR31", "AVR41"],  # Not AVR5
        "zone2_support": ["AVR20", "AVR30", "AVR40", 
                         "AVR21", "AVR31", "AVR41"],  # Not AVR5, AVR10
        "auro_3d": ["AVR20", "AVR30", "AVR40",
                   "AVR21", "AVR31", "AVR41"],  # Not AVR5
    }
```

## Priority Implementation Order

### High Priority (Phase 2)
1. **Audio Processing Controls** - Decode modes, bass/treble
2. **Enhanced Source Management** - Better source naming and management
3. **Basic HDMI Configuration** - Output selection, CEC control

### Medium Priority (Phase 3-4)  
1. **Video Processing** - Resolution info, video settings
2. **Speaker Configuration** - Basic speaker setup
3. **Room EQ Support** - EQ selection and management

### Lower Priority (Phase 5-7)
1. **Network Playback** - Streaming control
2. **Tuner Control** - FM/DAB functionality  
3. **Zone 2 Support** - Multi-zone control
4. **Advanced Diagnostics** - Comprehensive status reporting

### Future Considerations (Phase 8+)
1. **Mobile App Integration** - Companion mobile app
2. **Voice Control** - Enhanced voice assistant integration
3. **Automation Triggers** - Source-based automations
4. **Energy Monitoring** - Power consumption tracking

This roadmap ensures the initial implementation provides a solid foundation for future enhancements while maintaining code quality and user experience standards.