# Implementation Plan for Claude Code

## Development Approach

This plan provides step-by-step guidance for implementing the Arcam AVR Home Assistant integration. Each task includes specific files to create/modify, implementation details, and testing requirements.

## Prerequisites

### Environment Setup
1. **Home Assistant Development Environment**
   - Fork Home Assistant core repository
   - Set up development container or local environment
   - Install development dependencies (pytest, black, isort, pylint)

2. **Project Structure Creation**
   ```bash
   mkdir -p homeassistant/components/arcam_avr
   mkdir -p homeassistant/components/arcam_avr/arcam
   mkdir -p tests/components/arcam_avr
   mkdir -p tests/components/arcam_avr/arcam
   mkdir -p homeassistant/components/arcam_avr/translations
   ```

## Phase 1: Core Protocol Implementation

### Task 1: Protocol Foundation
**Files to create:**
- `homeassistant/components/arcam_avr/arcam/__init__.py`
- `homeassistant/components/arcam_avr/arcam/exceptions.py`
- `homeassistant/components/arcam_avr/arcam/protocol.py`

**Implementation Details:**

#### `arcam/exceptions.py`
```python
"""Arcam AVR exceptions."""

class ArcamError(Exception):
    """Base exception for Arcam AVR."""

class ArcamConnectionError(ArcamError):
    """Connection error."""

class ArcamProtocolError(ArcamError):
    """Protocol error."""

class ArcamCommandError(ArcamError):
    """Command execution error."""

class ArcamTimeoutError(ArcamError):
    """Command timeout error."""
```

#### `arcam/protocol.py`
- Implement `ArcamCommand` dataclass for command structure
- Implement `ArcamResponse` dataclass for response structure  
- Create `ArcamProtocol` class with static methods:
  - `encode_command(zone, command_code, data)`
  - `decode_response(raw_bytes)`
  - `validate_response(response, expected_command)`
- Add comprehensive error checking and validation
- Include logging for debugging protocol issues

**Testing Requirements:**
- Test command encoding with known good examples
- Test response decoding with sample device responses
- Test error conditions (malformed data, wrong lengths)
- Verify byte-level protocol accuracy

### Task 2: Command Definitions
**Files to create:**
- `homeassistant/components/arcam_avr/arcam/commands.py`

**Implementation Details:**
- Define all command constants (POWER=0x00, VOLUME=0x0D, etc.)
- Create RC5 command mapping for source selection
- Implement command factory methods:
  - `power_on(zone)`, `power_off(zone)`, `get_power_status(zone)`
  - `set_volume(volume, zone)`, `get_volume(zone)`
  - `get_mute_status(zone)`, `toggle_mute(zone)`
  - `get_source(zone)`, `select_source(source, zone)`
- Add data validation for all parameters
- Include source name to code mapping

**Testing Requirements:**
- Validate all command generation functions
- Test parameter validation and error handling
- Verify RC5 command encoding
- Test edge cases (invalid volumes, unknown sources)

### Task 3: Connection Management
**Files to create:**
- `homeassistant/components/arcam_avr/arcam/connection.py`

**Implementation Details:**
- Implement `ArcamConnection` class with:
  - Async connection management (connect/disconnect)
  - Command sending with timeout handling
  - Response receiving and parsing
  - Broadcast message listening
  - Automatic reconnection logic
  - Connection health monitoring
- Use asyncio for non-blocking operations
- Implement exponential backoff for reconnection
- Add comprehensive logging for debugging

**Key Methods:**
```python
async def connect() -> None
async def disconnect() -> None
async def send_command(command: ArcamCommand) -> ArcamResponse
async def is_connected() -> bool
async def start_broadcast_listener(callback: Callable)
async def stop_broadcast_listener()
```

**Testing Requirements:**
- Mock TCP socket for unit tests
- Test connection establishment and teardown
- Test command/response cycle
- Test error handling and reconnection
- Test broadcast message reception

## Phase 2: Home Assistant Integration

### Task 4: Integration Manifest and Constants
**Files to create:**
- `homeassistant/components/arcam_avr/manifest.json`
- `homeassistant/components/arcam_avr/const.py`

#### `manifest.json`
```json
{
  "domain": "arcam_avr",
  "name": "Arcam AVR",
  "codeowners": ["@yourusername"],
  "config_flow": true,
  "documentation": "https://www.home-assistant.io/integrations/arcam_avr",
  "iot_class": "local_push",
  "requirements": [],
  "version": "1.0.0"
}
```

#### `const.py`
- Define DOMAIN constant
- Configuration schema constants
- Default values (port, update intervals)
- Entity name templates
- Source mappings and friendly names

### Task 5: Configuration Flow
**Files to create:**
- `homeassistant/components/arcam_avr/config_flow.py`

**Implementation Details:**
- Implement `ArcamAvrConfigFlow` class
- User input step for IP address and port
- Connection validation before creating entry
- Device information retrieval (model, version)
- Error handling for connection failures
- Import step for YAML configuration migration
- Options flow for advanced settings (future)

**Key Methods:**
```python
async def async_step_user(self, user_input=None)
async def async_step_import(self, import_config)
async def _test_connection(self, host: str, port: int) -> dict
```

**Testing Requirements:**
- Test successful configuration flow
- Test invalid IP addresses
- Test connection failures
- Test duplicate device detection

### Task 6: Data Update Coordinator
**Files to create:**
- `homeassistant/components/arcam_avr/coordinator.py`

**Implementation Details:**
- Implement `ArcamAvrCoordinator` class extending `DataUpdateCoordinator`
- Manage connection to device
- Periodic status polling (30-second intervals)
- Immediate updates on command execution
- Broadcast message handling for real-time updates
- Device state caching and validation
- Error recovery and availability tracking

**Key Methods:**
```python
async def _async_update_data() -> dict
async def async_send_command(self, command_func: Callable, *args)
async def _handle_broadcast_message(self, response: ArcamResponse)
async def async_refresh_status()
```

**State Data Structure:**
```python
{
    "power": bool,
    "volume": int,  # 0-99
    "mute": bool,
    "source": str,  # Source code
    "available": bool,
    "model": str,
    "version": str
}
```

**Testing Requirements:**
- Mock coordinator updates
- Test command execution and immediate refresh
- Test error handling and availability
- Test broadcast message integration

### Task 7: Media Player Entity
**Files to create:**
- `homeassistant/components/arcam_avr/media_player.py`

**Implementation Details:**
- Implement `ArcamAvrMediaPlayer` class extending `CoordinatorEntity` and `MediaPlayerEntity`
- Map device state to Home Assistant media player states
- Implement all required media player methods
- Handle volume conversion (device 0-99 ↔ HA 0.0-1.0)
- Source selection with friendly names
- Proper device info and unique ID generation

**Required Properties:**
```python
@property
def state(self) -> str  # STATE_ON, STATE_OFF, STATE_UNAVAILABLE
def volume_level(self) -> float | None  # 0.0-1.0
def is_volume_muted(self) -> bool
def source(self) -> str | None
def source_list(self) -> list[str]
def supported_features(self) -> int
def device_info(self) -> DeviceInfo
```

**Required Methods:**
```python
async def async_turn_on()
async def async_turn_off()
async def async_set_volume_level(volume: float)
async def async_mute_volume(mute: bool)
async def async_select_source(source: str)
```

**Testing Requirements:**
- Test all media player functionality
- Test state mapping and volume conversion
- Test source selection and validation
- Test error handling and coordinator integration

### Task 8: Integration Entry Point
**Files to create:**
- `homeassistant/components/arcam_avr/__init__.py`

**Implementation Details:**
- Implement `async_setup_entry` function
- Initialize coordinator with config entry data
- Store coordinator in `hass.data`
- Forward setup to media_player platform
- Implement `async_unload_entry` for cleanup
- Add diagnostics support (optional)

**Key Functions:**
```python
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool
async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None
```

## Phase 3: Testing and Validation

### Task 9: Unit Tests
**Files to create:**
- `tests/components/arcam_avr/test_config_flow.py`
- `tests/components/arcam_avr/test_coordinator.py`
- `tests/components/arcam_avr/test_media_player.py`
- `tests/components/arcam_avr/arcam/test_protocol.py`
- `tests/components/arcam_avr/arcam/test_connection.py`
- `tests/components/arcam_avr/arcam/test_commands.py`

**Testing Strategy:**
- Mock all external dependencies (TCP sockets, time.sleep)
- Test both success and failure scenarios
- Achieve 90%+ code coverage
- Use pytest fixtures for common setup
- Include integration tests with mock responses

**Mock Data Requirements:**
- Sample device responses for all commands
- Error response examples
- Broadcast message samples
- Connection failure scenarios

### Task 10: Integration Testing
**Files to create:**
- `tests/components/arcam_avr/test_init.py`
- Test fixtures with mock device responses
- Integration test with real device (optional, for validation)

**Testing Focus:**
- Full integration setup and teardown
- Configuration flow end-to-end
- Media player entity functionality
- Error recovery scenarios
- Performance and memory usage

## Phase 4: Documentation and Finalization

### Task 11: Documentation
**Files to create:**
- `homeassistant/components/arcam_avr/translations/en.json`
- Update `README.md` with project description
- Add code documentation and type hints
- Create user setup instructions

#### `translations/en.json`
```json
{
  "config": {
    "step": {
      "user": {
        "title": "Arcam AVR",
        "description": "Configure your Arcam AVR amplifier",
        "data": {
          "host": "IP Address",
          "port": "Port",
          "name": "Name"
        }
      }
    },
    "error": {
      "cannot_connect": "Failed to connect to device",
      "invalid_host": "Invalid IP address",
      "timeout": "Connection timeout",
      "unknown": "Unexpected error occurred"
    }
  }
}
```

### Task 12: Code Quality and Compliance
**Quality Checklist:**
- [ ] All files have proper type hints
- [ ] Code passes pylint with score > 9.0
- [ ] Code formatted with black and isort
- [ ] All functions have docstrings
- [ ] Error handling is comprehensive
- [ ] Logging is appropriate and helpful
- [ ] Constants are properly defined
- [ ] No hardcoded values in code

## Validation Steps

### Pre-Submit Checklist
1. **Functionality Testing**
   - [ ] All basic functions work (power, volume, mute, source)
   - [ ] Configuration flow works end-to-end
   - [ ] Error handling works correctly
   - [ ] Unit tests pass with 90%+ coverage

2. **Code Quality**
   - [ ] Passes all linters (pylint, black, isort)
   - [ ] Type checking passes (mypy)
   - [ ] Documentation is complete
   - [ ] Follows Home Assistant coding standards

3. **Integration Testing**
   - [ ] Works with real Arcam AVR11 device
   - [ ] Integration can be loaded/unloaded cleanly
   - [ ] Performance is acceptable
   - [ ] Memory usage is reasonable

4. **Home Assistant Compliance**
   - [ ] Follows integration best practices
   - [ ] Uses coordinator pattern correctly
   - [ ] Proper entity registration
   - [ ] Configuration flow follows guidelines

## Success Metrics

### Phase 1 Complete
- [ ] Protocol library can communicate with device
- [ ] All basic commands work reliably
- [ ] Unit tests achieve target coverage
- [ ] Code quality standards met

### Phase 2 Complete
- [ ] Integration loads successfully in Home Assistant
- [ ] Configuration flow works
- [ ] Media player entity appears and functions
- [ ] State updates work correctly

### Phase 3 Complete
- [ ] All tests pass
- [ ] Integration tested with real hardware
- [ ] Error scenarios handled gracefully
- [ ] Performance meets requirements

### Final Delivery
- [ ] Code ready for Home Assistant core submission
- [ ] Documentation complete
- [ ] All quality checks pass
- [ ] Real-world testing validated

## Estimated Timeline

- **Phase 1**: 3-4 days (Protocol implementation)
- **Phase 2**: 4-5 days (Home Assistant integration)
- **Phase 3**: 2-3 days (Testing and validation)
- **Phase 4**: 1-2 days (Documentation and finalization)

**Total Estimated Time**: 10-14 days

## Risk Mitigation

### Technical Risks
- **Protocol Complexity**: Start with basic commands, expand gradually
- **Connection Reliability**: Implement robust error handling and reconnection
- **Home Assistant Changes**: Follow current development patterns
- **Device Compatibility**: Test with available hardware, use protocol documentation

### Development Risks
- **Scope Creep**: Stick to Phase 1 features initially
- **Quality Standards**: Maintain high code quality from start
- **Testing Coverage**: Write tests alongside implementation
- **Documentation**: Document as you develop, not after