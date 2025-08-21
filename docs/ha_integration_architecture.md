# Home Assistant Integration Architecture

## Integration Overview

The Arcam AVR integration follows Home Assistant's modern integration patterns using the coordinator model for efficient data updates and proper entity management.

## Core Components

### 1. Integration Entry Point (`__init__.py`)

```python
"""Arcam AVR integration for Home Assistant."""
DOMAIN = "arcam_avr"
PLATFORMS = ["media_player"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Arcam AVR from a config entry."""
    # Initialize coordinator
    # Store coordinator in hass.data
    # Forward setup to platforms
    
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Cleanup coordinator
    # Unload platforms
```

### 2. Configuration Flow (`config_flow.py`)

```python
class ArcamAvrConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Arcam AVR."""
    
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        # Validate IP address
        # Test connection to device
        # Create config entry
    
    async def async_step_import(self, import_config):
        """Handle import from configuration.yaml."""
        # Support legacy YAML configuration
```

### 3. Data Update Coordinator (`coordinator.py`)

```python
class ArcamAvrCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Arcam AVR data."""
    
    def __init__(self, hass: HomeAssistant, host: str, port: int):
        """Initialize coordinator."""
        self.arcam = ArcamAvrClient(host, port)
        super().__init__(
            hass,
            logger,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
    
    async def _async_update_data(self):
        """Fetch data from device."""
        # Get current state from device
        # Return structured data
        
    async def async_send_command(self, command: str, *args):
        """Send command to device."""
        # Execute command
        # Trigger immediate update
```

## Entity Architecture

### Media Player Entity (`media_player.py`)

```python
class ArcamAvrMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Representation of an Arcam AVR as a media player."""
    
    def __init__(self, coordinator: ArcamAvrCoordinator, zone: int = 1):
        """Initialize the media player."""
        super().__init__(coordinator)
        self._zone = zone
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_zone_{zone}"
        
    @property
    def state(self) -> str:
        """Return the state of the device."""
        # Map device power state to HA states
        
    @property
    def volume_level(self) -> float:
        """Volume level of the media player (0..1)."""
        # Convert device volume (0-99) to HA volume (0.0-1.0)
        
    @property
    def source(self) -> str:
        """Return the current input source."""
        # Map device source codes to friendly names
        
    @property
    def source_list(self) -> list[str]:
        """List of available input sources."""
        # Return list of available sources
        
    async def async_turn_on(self):
        """Turn the media player on."""
        await self.coordinator.async_send_command("power_on")
        
    async def async_turn_off(self):
        """Turn the media player off."""
        await self.coordinator.async_send_command("power_off")
        
    async def async_set_volume_level(self, volume: float):
        """Set volume level."""
        device_volume = int(volume * 99)
        await self.coordinator.async_send_command("set_volume", device_volume)
        
    async def async_mute_volume(self, mute: bool):
        """Mute/unmute volume."""
        await self.coordinator.async_send_command("set_mute", mute)
        
    async def async_select_source(self, source: str):
        """Select input source."""
        await self.coordinator.async_send_command("select_source", source)
```

## Protocol Library Structure

### Connection Manager (`arcam/connection.py`)

```python
class ArcamConnection:
    """Manages TCP connection to Arcam device."""
    
    def __init__(self, host: str, port: int = 50000):
        """Initialize connection."""
        
    async def connect(self) -> None:
        """Establish connection to device."""
        
    async def disconnect(self) -> None:
        """Close connection to device."""
        
    async def send_command(self, command: ArcamCommand) -> ArcamResponse:
        """Send command and wait for response."""
        
    async def listen_for_broadcasts(self, callback: Callable):
        """Listen for unsolicited device updates."""
```

### Protocol Implementation (`arcam/protocol.py`)

```python
class ArcamProtocol:
    """Implements Arcam binary protocol."""
    
    @staticmethod
    def encode_command(zone: int, command_code: int, data: bytes = b"") -> bytes:
        """Encode command to binary format."""
        
    @staticmethod
    def decode_response(data: bytes) -> ArcamResponse:
        """Decode binary response."""
        
    @staticmethod
    def validate_response(response: ArcamResponse, expected_command: int) -> bool:
        """Validate response matches expected command."""
```

### Command Definitions (`arcam/commands.py`)

```python
class ArcamCommands:
    """Arcam command constants and helpers."""
    
    # Command codes
    POWER = 0x00
    VOLUME = 0x0D
    MUTE = 0x0E
    SOURCE = 0x1D
    RC5_SIMULATE = 0x08
    
    # RC5 codes for source selection
    RC5_SOURCES = {
        "CD": (0x10, 0x76),
        "BD": (0x10, 0x62),
        "STB": (0x10, 0x64),
        # ... etc
    }
    
    @classmethod
    def power_on(cls, zone: int = 1) -> ArcamCommand:
        """Create power on command."""
        
    @classmethod
    def power_off(cls, zone: int = 1) -> ArcamCommand:
        """Create power off command."""
        
    @classmethod
    def set_volume(cls, volume: int, zone: int = 1) -> ArcamCommand:
        """Create set volume command."""
```

## Device Discovery and Configuration

### Configuration Schema

```python
CONFIG_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default=50000): cv.port,
    vol.Optional(CONF_NAME, default="Arcam AVR"): cv.string,
})
```

### Device Information

```python
class ArcamDeviceInfo:
    """Device information for Arcam AVR."""
    
    def __init__(self, host: str, model: str, version: str):
        self.host = host
        self.model = model
        self.version = version
        
    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for device registry."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.host)},
            name=f"Arcam {self.model}",
            manufacturer="Arcam",
            model=self.model,
            sw_version=self.version,
        )
```

## Data Flow

### Initialization Flow
1. User enters IP address in configuration flow
2. Integration tests connection and retrieves device info
3. Config entry created with device details
4. Coordinator initialized with connection
5. Media player entity created and registered

### Update Flow
1. Coordinator polls device every 30 seconds
2. Status broadcasts trigger immediate updates
3. Entity state updated via coordinator data
4. Home Assistant notifies listeners of state changes

### Command Flow
1. User triggers action in Home Assistant
2. Entity calls coordinator command method
3. Coordinator sends command via protocol library
4. Device responds with status
5. Coordinator triggers immediate data refresh
6. Entity state updated with new values

## Error Handling Strategy

### Connection Errors
- Automatic reconnection with exponential backoff
- Mark integration as unavailable during disconnection
- Retry failed commands up to 3 times
- Log connection issues for debugging

### Protocol Errors
- Validate all responses for correct format
- Handle unknown/unexpected responses gracefully
- Log protocol errors with hex dump for analysis
- Continue operation despite non-critical errors

### State Synchronization
- Poll device state on reconnection
- Handle external state changes (front panel, IR remote)
- Maintain consistency between HA state and device state
- Implement optimistic updates for better responsiveness

## Testing Architecture

### Unit Tests Structure
```
tests/
├── test_config_flow.py         # Configuration flow tests
├── test_coordinator.py         # Coordinator functionality tests
├── test_media_player.py        # Media player entity tests
└── arcam/
    ├── test_protocol.py        # Protocol encoding/decoding tests
    ├── test_connection.py      # Connection management tests
    └── test_commands.py        # Command generation tests
```

### Mock Strategy
- Mock TCP connections for unit tests
- Simulate device responses for state testing
- Test error conditions and recovery
- Validate command encoding without real hardware

## Performance Considerations

### Efficient Updates
- Use coordinator pattern to prevent redundant polling
- Implement smart update intervals based on activity
- Cache frequently accessed data
- Batch commands when possible

### Memory Management
- Clean up connections on integration unload
- Avoid memory leaks in long-running connections
- Implement proper resource cleanup
- Monitor memory usage in long-term testing

### Responsiveness
- Prioritize user commands over status polling
- Implement command queuing for reliability
- Use async/await for non-blocking operations
- Optimize critical path performance