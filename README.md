# Arcam AVR Home Assistant Integration

A comprehensive Home Assistant integration for Arcam AVR amplifiers and receivers, providing seamless control and monitoring of your audio system.

## Overview

This integration enables Home Assistant to communicate with Arcam AVR devices over IP networks, offering complete control over power, volume, source selection, and monitoring of device status. It supports all documented Arcam AVR models including AVR5, AVR10, AVR20, AVR30, AVR40, AVR11, AVR21, AVR31, and AVR41.

## Features

### Phase 1 (Core Functionality)
- **Power Control**: Turn device on/off and monitor power state
- **Volume Control**: Set volume levels (0-99) and mute/unmute
- **Source Selection**: Switch between available input sources (CD, BD, STB, Game, etc.)
- **Real-time Updates**: Immediate status updates via device broadcasts
- **Connection Management**: Automatic reconnection with robust error handling
- **Home Assistant Integration**: Full media_player entity with proper device registry

### Supported Sources
- CD, Blu-ray (BD), AV, Set-top Box (STB)
- Satellite (SAT), PVR, VCR, Auxiliary (Aux)  
- Game, Network (NET), FM Radio, DAB Radio
- Bluetooth (BT), USB, UHD

## Prerequisites

### Device Requirements
- Arcam AVR amplifier with IP control enabled
- Device connected to same network as Home Assistant
- IP control enabled in device settings (General Setup → Control → On)

### Network Configuration
- TCP port 50000 must be accessible
- Static IP address recommended for device
- Firewall rules configured if necessary

## Installation

### Using UV (Recommended)
```bash
# Install dependencies
uv pip install -r requirements.txt

# Run development setup
uv run python -m homeassistant --config config
```

### Traditional pip
```bash
pip install -r requirements.txt
```

## Configuration

The integration uses Home Assistant's modern configuration flow for easy setup:

1. Navigate to **Settings** → **Devices & Services**
2. Click **Add Integration** 
3. Search for "Arcam AVR"
4. Enter your device's IP address and port (default: 50000)
5. The integration will automatically detect your device model and version

### Manual Configuration (Legacy)
If migrating from YAML configuration:
```yaml
# configuration.yaml (legacy support)
media_player:
  - platform: arcam_avr
    host: 192.168.1.100
    port: 50000
    name: "Living Room AVR"
```

## Usage

Once configured, your Arcam AVR will appear as a media player entity in Home Assistant:

### Basic Controls
- **Power**: Turn on/off via the power button
- **Volume**: Adjust volume with slider (0-100%)
- **Mute**: Toggle mute state
- **Source**: Select input source from dropdown

### Automation Examples

```yaml
# Turn on AVR and set volume when TV turns on
automation:
  - alias: "Living Room AVR On"
    trigger:
      - platform: device
        device_id: your_tv_device_id
        domain: media_player
        entity_id: media_player.tv
        type: turned_on
    action:
      - service: media_player.turn_on
        target:
          entity_id: media_player.arcam_avr
      - service: media_player.volume_set
        target:
          entity_id: media_player.arcam_avr
        data:
          volume_level: 0.3

# Scene for movie watching
scene:
  - name: "Movie Night"
    entities:
      media_player.arcam_avr:
        state: "on"
        volume_level: 0.4
        source: "BD"
```

## Architecture

The integration follows Home Assistant's modern patterns:

- **Coordinator Pattern**: Efficient data updates and command handling
- **Binary Protocol**: Native implementation of Arcam's TCP protocol
- **Async/Await**: Non-blocking operations for better performance
- **Device Registry**: Proper device identification and management
- **Entity Platform**: Full media_player entity with all features

For detailed architecture information, see [docs/ha_integration_architecture.md](./docs/ha_integration_architecture.md).

## Protocol Implementation

This integration implements Arcam's proprietary binary protocol over TCP:

- **Connection**: TCP port 50000 with persistent connection
- **Commands**: 6-byte binary command structure with response validation
- **Broadcasting**: Real-time status updates from device
- **Error Handling**: Comprehensive error codes and recovery mechanisms

For complete protocol details, see [docs/arcam_protocol_spec.md](./docs/arcam_protocol_spec.md).

## Development

### Environment Setup

```bash
# Clone repository
git clone https://github.com/yourusername/arcam-control-home-assistant.git
cd arcam-control-home-assistant

# Install development dependencies with UV
uv pip install -r requirements.txt -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Project Structure
```
homeassistant/components/arcam_avr/
├── __init__.py                 # Integration entry point
├── manifest.json              # Integration manifest  
├── config_flow.py             # Configuration flow
├── const.py                   # Constants and definitions
├── coordinator.py             # Data update coordinator
├── media_player.py            # Media player entity
├── arcam/                     # Protocol library
│   ├── __init__.py
│   ├── protocol.py           # Binary protocol implementation
│   ├── connection.py         # TCP connection management
│   ├── commands.py           # Command definitions
│   └── exceptions.py         # Custom exceptions
└── translations/              # Internationalization
    └── en.json
```

### Testing

The integration includes comprehensive unit tests that don't require physical hardware:

```bash
# Run all tests
pytest tests/components/arcam_avr/

# Run with coverage
pytest --cov=homeassistant.components.arcam_avr tests/components/arcam_avr/

# Run specific test file  
pytest tests/components/arcam_avr/test_media_player.py -v
```

For testing strategy and mock implementation details, see [docs/testing_strategy.md](./docs/testing_strategy.md).

### Code Quality

This project maintains high code quality standards:

```bash
# Format code
black homeassistant/components/arcam_avr/
isort homeassistant/components/arcam_avr/

# Lint code
pylint homeassistant/components/arcam_avr/

# Type checking
mypy homeassistant/components/arcam_avr/
```

## Implementation Plan

Development follows a structured phase approach for quality and reliability:

**Phase 1**: Core protocol implementation and basic Home Assistant integration  
**Phase 2**: Extended audio controls (decode modes, bass/treble adjustment)  
**Phase 3**: Video and HDMI features  
**Phase 4**: Speaker management and room correction  

For the complete implementation plan, see [docs/implementation_plan.md](./docs/implementation_plan.md).

## Future Enhancements

The integration is designed for extensibility with planned features including:

- **Audio Processing**: Decode mode control, bass/treble adjustment
- **HDMI Control**: Output configuration, CEC control  
- **Speaker Setup**: Configuration and level adjustment
- **Network Playback**: Streaming source control
- **Zone 2 Support**: Multi-zone control for compatible models
- **Advanced Diagnostics**: Comprehensive status and debugging

See [docs/future_enhancements.md](./docs/future_enhancements.md) for detailed feature roadmap.

## Supported Models

All documented Arcam AVR models are supported:

| Model | Features | Zone 2 | Notes |
|-------|----------|--------|-------|  
| AVR5 | Basic | No | Entry level |
| AVR10 | Basic | No | |
| AVR20 | Full | Yes | |
| AVR30 | Full | Yes | |
| AVR40 | Full | Yes | Flagship |
| AVR11 | Basic | No | Newer generation |
| AVR21 | Full | Yes | |
| AVR31 | Full | Yes | |
| AVR41 | Full | Yes | Flagship |

## Troubleshooting

### Common Issues

**Connection Failed**
- Verify device IP address and network connectivity
- Ensure IP control is enabled on device
- Check firewall settings for port 50000

**Commands Not Working**
- Confirm device is powered on and responsive
- Check for firmware updates on device
- Verify integration logs for error messages

**State Not Updating**
- Device may be controlled by other sources (IR remote, front panel)
- Integration will sync state within 30 seconds
- Restart integration if persistent issues

### Debug Logging

Enable debug logging for troubleshooting:

```yaml
# configuration.yaml
logger:
  logs:
    homeassistant.components.arcam_avr: debug
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Follow code quality standards (black, isort, pylint)
4. Add tests for new functionality  
5. Update documentation as needed
6. Submit a pull request

### Development Workflow

Each major feature should be developed as individual commits following the implementation plan:

1. **Protocol Foundation**: Core protocol implementation
2. **Home Assistant Integration**: Entity and coordinator setup
3. **Testing**: Comprehensive unit and integration tests
4. **Documentation**: User guides and API documentation

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Arcam for providing protocol documentation
- Home Assistant community for integration patterns
- Contributors and testers who help improve the integration

## Support

For issues, feature requests, or questions:

- **GitHub Issues**: [Project Issues](https://github.com/yourusername/arcam-control-home-assistant/issues)
- **Home Assistant Community**: [Community Forum](https://community.home-assistant.io/)
- **Documentation**: See [docs/](./docs/) directory for detailed documentation

---

*This integration is not affiliated with Arcam. All trademarks are property of their respective owners.*