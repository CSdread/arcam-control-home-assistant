# Arcam AVR Technical Guide

Technical documentation for developers and advanced users working with the Arcam AVR integration.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Protocol Specification](#protocol-specification)
3. [Code Structure](#code-structure)
4. [API Reference](#api-reference)
5. [Development Setup](#development-setup)
6. [Testing](#testing)
7. [Performance Considerations](#performance-considerations)
8. [Troubleshooting](#troubleshooting)

## Architecture Overview

### Integration Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Home Assistant Core                      │
├─────────────────────────────────────────────────────────────┤
│  Arcam AVR Integration                                      │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────┐ │
│  │   Config Flow   │  │  Media Player    │  │ Coordinator │ │
│  │   (Setup UI)    │  │    Entity        │  │ (Data Mgmt) │ │
│  └─────────────────┘  └──────────────────┘  └─────────────┘ │
│                             │                       │       │
│                             └───────────────────────┘       │
├─────────────────────────────────────────────────────────────┤
│  Protocol Library                                          │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────┐ │
│  │   Connection    │  │    Commands      │  │  Protocol   │ │
│  │   Management    │  │   & Responses    │  │  Handler    │ │
│  └─────────────────┘  └──────────────────┘  └─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      Network Layer                         │
│           TCP Connection to Arcam AVR (Port 50000)         │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Configuration**: User sets up device via Config Flow
2. **Initialization**: Coordinator establishes connection and queries device
3. **Updates**: Coordinator polls device and processes broadcasts
4. **Commands**: Media Player entity sends commands via Coordinator
5. **State Management**: Updates propagate to UI and automations

### Key Design Principles

- **Async-First**: All operations use asyncio for non-blocking behavior
- **Error Resilience**: Robust error handling with automatic recovery
- **Performance**: Efficient polling with adaptive intervals
- **Extensibility**: Modular design supporting multiple device types

## Protocol Specification

### Binary Protocol Format

Arcam AVR devices use a proprietary binary protocol over TCP:

```
┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┐
│  STX    │ Command │  Data   │  Zone   │  CRC    │  ETX    │
│ (1 byte)│ (1 byte)│ (1 byte)│ (1 byte)│ (1 byte)│ (1 byte)│
└─────────┴─────────┴─────────┴─────────┴─────────┴─────────┘
```

#### Field Descriptions
- **STX**: Start of transmission (0x02)
- **Command**: Command identifier (see command table)
- **Data**: Command parameter (optional, 0x00 if unused)
- **Zone**: Target zone (1-based, typically 1-4)
- **CRC**: Checksum of Command + Data + Zone
- **ETX**: End of transmission (0x03)

### Command Set

#### Power Commands
| Command | Code | Data | Description |
|---------|------|------|-------------|
| Power Status | 0x01 | N/A | Query power state |
| Power On | 0x01 | 0x01 | Turn on device |
| Power Off | 0x01 | 0x00 | Turn off device |

#### Volume Commands
| Command | Code | Data | Description |
|---------|------|------|-------------|
| Volume Status | 0x03 | N/A | Query current volume |
| Set Volume | 0x03 | 0-99 | Set volume level |
| Volume Up | 0x09 | N/A | Increase volume |
| Volume Down | 0x0A | N/A | Decrease volume |

#### Mute Commands
| Command | Code | Data | Description |
|---------|------|------|-------------|
| Mute Status | 0x04 | N/A | Query mute state |
| Mute On | 0x04 | 0x01 | Enable mute |
| Mute Off | 0x04 | 0x00 | Disable mute |

#### Source Commands
| Command | Code | Data | Description |
|---------|------|------|-------------|
| Source Status | 0x05 | N/A | Query current source |
| Set Source | 0x05 | Source ID | Change input source |

#### Source IDs
| ID | Name | Description |
|----|------|-------------|
| 0x00 | BD | Blu-ray Player |
| 0x01 | CD | CD Player |
| 0x02 | DVD | DVD Player |
| 0x03 | SAT | Satellite/Cable |
| 0x04 | PVR | PVR/DVR |
| 0x05 | VCR | VCR |
| 0x06 | TAPE | Tape Deck |
| 0x07 | TUNER | AM/FM Tuner |
| 0x08 | PHONO | Phono/Turntable |
| 0x09 | AUX | Auxiliary Input |
| 0x0A | DISP | Display |
| 0x0B | NET | Network/Streaming |
| 0x0C | USB | USB Input |
| 0x0D | STB | Set-Top Box |

### Response Format

Responses follow the same 6-byte format:
- **STX**: 0x02
- **Command**: Echo of original command
- **Data**: Response data
- **Zone**: Echo of target zone
- **CRC**: Response checksum
- **ETX**: 0x03

### Broadcast Messages

Devices send unsolicited broadcasts for real-time updates:
- Same format as responses
- Triggered by physical controls, remote commands, or state changes
- Enable immediate UI updates without polling

### Error Handling

#### Protocol Errors
- **Invalid CRC**: Request retransmission
- **Timeout**: Retry with exponential backoff
- **Unknown Command**: Log error and continue
- **Invalid Zone**: Return error to caller

#### Connection Errors
- **Network Unreachable**: Attempt reconnection
- **Connection Refused**: Device may be off or busy
- **Socket Errors**: Close and reestablish connection

## Code Structure

### Directory Layout
```
homeassistant/components/arcam_avr/
├── __init__.py              # Integration entry point
├── manifest.json            # Integration metadata
├── const.py                # Constants and configuration
├── config_flow.py          # Setup UI and configuration
├── coordinator.py          # Data update coordinator
├── media_player.py         # Media player entity
├── arcam/                  # Protocol library
│   ├── __init__.py
│   ├── exceptions.py       # Custom exceptions
│   ├── protocol.py         # Protocol implementation
│   ├── commands.py         # Command definitions
│   └── connection.py       # Connection management
├── translations/           # Localization files
│   ├── en.json
│   ├── es.json
│   ├── fr.json
│   └── de.json
└── strings.json           # UI strings
```

### Key Classes

#### ArcamConnection
Manages TCP connection and protocol communication:
```python
class ArcamConnection:
    async def connect(self) -> None
    async def disconnect(self) -> None
    async def send_command(self, command: ArcamCommand) -> ArcamResponse
    def start_broadcast_listener(self, callback: Callable) -> None
```

#### ArcamAvrCoordinator
Coordinates data updates and command execution:
```python
class ArcamAvrCoordinator(DataUpdateCoordinator):
    async def async_send_command(self, command_func, *args) -> bool
    async def _async_update_data(self) -> dict[str, Any]
    def _handle_broadcast_message(self, message: dict) -> None
```

#### ArcamAvrMediaPlayer
Home Assistant media player entity:
```python
class ArcamAvrMediaPlayer(MediaPlayerEntity):
    async def async_turn_on(self) -> None
    async def async_turn_off(self) -> None
    async def async_set_volume_level(self, volume: float) -> None
    async def async_select_source(self, source: str) -> None
```

## API Reference

### Configuration Data Schema

#### Config Entry Data
```python
{
    "host": str,           # Device IP address
    "port": int,           # TCP port (default: 50000)
    "name": str,           # Device name
    "zones": list[int],    # Enabled zones (default: [1])
}
```

#### Options Schema
```python
{
    "update_interval": int,    # Polling interval (30-300 seconds)
    "fast_polling": bool,      # Faster polling when device is on
    "zones": list[int],        # Enabled zones
}
```

### Service Definitions

#### media_player.select_source
```yaml
service: media_player.select_source
target:
  entity_id: media_player.arcam_avr
data:
  source: str  # Source name or ID
```

#### arcam_avr.send_command
```yaml
service: arcam_avr.send_command
target:
  entity_id: media_player.arcam_avr
data:
  command: str    # Hex command code (e.g., "0x01")
  data: int       # Optional data parameter
  zone: int       # Target zone (default: 1)
```

### Entity Attributes

#### Media Player Attributes
```python
{
    "state": str,                    # on, off, unavailable
    "volume_level": float,           # 0.0 - 1.0
    "is_volume_muted": bool,         # Mute state
    "source": str,                   # Current source name
    "source_list": list[str],        # Available sources
    "supported_features": int,       # Feature bitmask
    
    # Custom attributes
    "model": str,                    # Device model
    "version": str,                  # Firmware version
    "zone": int,                     # Zone number (if multi-zone)
}
```

### Device Registry Information
```python
{
    "identifiers": {(DOMAIN, config_entry.entry_id)},
    "name": str,                     # Device name
    "manufacturer": "Arcam",
    "model": str,                    # Device model
    "sw_version": str,               # Firmware version
    "configuration_url": str,        # Device web interface
}
```

## Development Setup

### Prerequisites
- Python 3.11+
- Home Assistant development environment
- UV package manager (recommended)

### Environment Setup
```bash
# Clone repository
git clone https://github.com/your-repo/arcam-control-home-assistant.git
cd arcam-control-home-assistant

# Setup virtual environment with UV
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
uv sync --dev

# Install pre-commit hooks
pre-commit install
```

### Development Tools

#### Code Quality
```bash
# Run linting
ruff check homeassistant/components/arcam_avr/
ruff format homeassistant/components/arcam_avr/

# Type checking
mypy homeassistant/components/arcam_avr/

# Security analysis
bandit -r homeassistant/components/arcam_avr/
```

#### Testing
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=homeassistant.components.arcam_avr tests/

# Run specific test categories
pytest -m "not slow" tests/              # Fast tests only
pytest -m "integration" tests/           # Integration tests
pytest -m "performance" tests/           # Performance tests
```

### Mock Device for Testing
```python
# Create mock device for development
from tests.components.arcam_avr.test_config import MockArcamDevice

mock_device = MockArcamDevice("192.168.1.100", 50000)
await mock_device.connect()

# Simulate commands
response = await mock_device.send_command(
    ArcamCommand(command=0x01, data=0x01, zone=1)
)
```

## Testing

### Test Categories

#### Unit Tests
- **Protocol Tests**: Command encoding/decoding, connection handling
- **Entity Tests**: Media player functionality, state management
- **Config Tests**: Setup flow, options handling

#### Integration Tests
- **Lifecycle Tests**: Full setup/teardown cycles
- **Communication Tests**: Device interaction scenarios
- **Error Tests**: Failure and recovery scenarios

#### Performance Tests
- **Timing Tests**: Response time validation
- **Load Tests**: Concurrent operation testing
- **Memory Tests**: Memory usage monitoring

### Test Infrastructure

#### Mock Device
Realistic device simulation with:
- State persistence across commands
- Configurable response delays
- Broadcast message generation
- Error injection capabilities

#### Test Fixtures
```python
@pytest.fixture
async def mock_connection_factory():
    """Factory for creating mock connections."""
    # Implementation details...

@pytest.fixture
def test_config():
    """Standard test configuration."""
    return {
        "host": "192.168.1.100",
        "port": 50000,
        "name": "Test AVR",
    }
```

### Running Tests

#### Quick Test Run
```bash
# All tests
python -m pytest tests/components/arcam_avr/

# Fast tests only
python -m pytest tests/components/arcam_avr/ -m "not slow"

# With verbose output
python -m pytest tests/components/arcam_avr/ -v
```

#### Coverage Analysis
```bash
# Generate coverage report
pytest --cov=homeassistant.components.arcam_avr \
       --cov-report=html \
       --cov-report=term-missing \
       tests/

# View HTML report
open htmlcov/index.html
```

#### Performance Testing
```bash
# Run performance tests
python tests/components/arcam_avr/run_integration_tests.py --performance

# Memory profiling
python -m pytest tests/components/arcam_avr/test_performance.py::test_memory_usage_stability -v
```

## Performance Considerations

### Optimization Strategies

#### Polling Optimization
- **Adaptive Intervals**: Faster polling when device is active
- **State-Based Polling**: Adjust frequency based on device state
- **Broadcast Prioritization**: Use broadcasts over polling when possible

#### Connection Management
- **Connection Pooling**: Reuse connections efficiently
- **Timeout Optimization**: Balanced timeouts for reliability vs. speed
- **Retry Logic**: Exponential backoff for failed operations

#### Memory Management
- **Data Structures**: Efficient state storage
- **Event Handling**: Proper cleanup of listeners and callbacks
- **Resource Cleanup**: Timely connection and resource disposal

### Performance Metrics

#### Target Benchmarks
- **Startup Time**: < 3 seconds for integration load
- **Command Latency**: < 1 second for command execution
- **Update Frequency**: < 0.5 seconds for status updates
- **Memory Usage**: < 10MB growth over extended operation

#### Monitoring
```python
# Performance monitoring in code
import time
import psutil

start_time = time.time()
# ... operation ...
execution_time = time.time() - start_time

memory_usage = psutil.Process().memory_info().rss
```

### Scalability Considerations

#### Multiple Devices
- **Connection Limits**: Manage TCP connection count
- **Resource Sharing**: Efficient resource allocation
- **Update Coordination**: Stagger updates across devices

#### High-Frequency Operations
- **Rate Limiting**: Respect device command limits
- **Queueing**: Queue rapid commands appropriately
- **Buffering**: Buffer state updates for efficiency

## Troubleshooting

### Common Development Issues

#### Import Errors
```python
# Ensure proper path setup
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from homeassistant.components.arcam_avr import ...
```

#### Async Issues
```python
# Proper async context
import asyncio

async def test_function():
    # Use proper async patterns
    await some_async_operation()

# Run with proper event loop
asyncio.run(test_function())
```

#### Mock Device Issues
```python
# Ensure mock device is properly configured
mock_device = MockArcamDevice()
await mock_device.connect()  # Always connect before use
mock_device.set_command_delay(0.01)  # Realistic delays
```

### Debug Tools

#### Protocol Analyzer
```python
# Enable protocol debugging
import logging
logging.getLogger('homeassistant.components.arcam_avr.arcam.protocol').setLevel(logging.DEBUG)
```

#### Network Testing
```bash
# Test TCP connectivity
nc -v 192.168.1.100 50000

# Monitor network traffic
tcpdump -i en0 host 192.168.1.100 and port 50000
```

#### Home Assistant Debug
```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    homeassistant.components.arcam_avr: debug
    custom_components.arcam_avr: debug
```

### Performance Debugging

#### Profiling
```python
import cProfile
import pstats

# Profile specific function
profiler = cProfile.Profile()
profiler.enable()
# ... code to profile ...
profiler.disable()

# Analyze results
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative').print_stats(10)
```

#### Memory Analysis
```python
import tracemalloc

# Start memory tracing
tracemalloc.start()

# ... code to analyze ...

# Get memory statistics
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.2f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.2f} MB")
```

---

## Additional Resources

- [Home Assistant Integration Development](https://developers.home-assistant.io/)
- [Python AsyncIO Documentation](https://docs.python.org/3/library/asyncio.html)
- [Pytest Documentation](https://docs.pytest.org/)
- [UV Package Manager](https://github.com/astral-sh/uv)

---

*This technical guide is maintained alongside the codebase and updated with each release.*