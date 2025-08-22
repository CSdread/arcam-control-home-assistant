# CLAUDE.md - Arcam AVR Home Assistant Integration

This file contains important context and instructions for Claude Code when working with this project.

## Project Overview

This is a comprehensive Home Assistant integration for Arcam AVR (Audio Video Receiver) devices. The integration provides full control over Arcam AVR receivers through Home Assistant's media player interface, supporting multiple zones, source selection, volume control, and power management.

## Project Structure

```
arcam-control-home-assistant/
├── homeassistant/components/arcam_avr/     # Main integration code
│   ├── arcam/                             # Protocol library
│   │   ├── __init__.py
│   │   ├── exceptions.py                  # Custom exceptions
│   │   ├── protocol.py                    # Core protocol implementation
│   │   ├── commands.py                    # Command definitions
│   │   └── connection.py                  # TCP connection handling
│   ├── translations/                      # Internationalization
│   │   ├── en.json                       # English (base)
│   │   ├── fr.json                       # French
│   │   ├── es.json                       # Spanish
│   │   └── de.json                       # German
│   ├── __init__.py                       # Integration entry point
│   ├── config_flow.py                    # Configuration flow
│   ├── const.py                          # Constants
│   ├── coordinator.py                    # Data update coordinator
│   ├── manifest.json                     # Integration manifest
│   ├── media_player.py                   # Media player entity
│   ├── services.yaml                     # Service definitions
│   └── strings.json                      # UI strings
├── tests/                                # Test suite
│   ├── components/arcam_avr/            # Integration tests
│   │   ├── __init__.py
│   │   ├── conftest.py                  # Test fixtures
│   │   ├── test_config_flow.py          # Config flow tests
│   │   ├── test_coordinator.py          # Coordinator tests
│   │   ├── test_init.py                 # Integration tests
│   │   ├── test_integration.py          # End-to-end tests
│   │   └── test_media_player.py         # Media player tests
│   └── test_protocol.py                 # Protocol library tests
├── docs/                                # Documentation
│   ├── DEVELOPMENT.md                   # Development guide
│   ├── TROUBLESHOOTING.md               # Troubleshooting guide
│   └── USER_GUIDE.md                    # User documentation
├── config/                              # Example configuration
│   └── configuration.yaml               # Example HA config
├── scripts/                             # Build and utility scripts
│   └── build-docker.sh                 # Docker build script
├── .github/workflows/                   # CI/CD workflows
│   ├── ci.yml                          # Continuous integration
│   ├── quality.yml                     # Code quality checks
│   └── release.yml                     # Release automation
├── Dockerfile                           # Container build
├── docker-compose.yml                  # Docker Compose setup
├── k8s-deployment.yaml                 # Kubernetes deployment
├── pyproject.toml                      # Project configuration
├── requirements.txt                    # Python dependencies
└── README.md                           # Project documentation
```

## Development Guidelines

### Code Quality Standards
- **Linting**: Use Ruff for code formatting and linting
- **Type Checking**: Use MyPy for static type analysis
- **Security**: Use Bandit for security analysis
- **Testing**: Maintain >90% test coverage
- **Documentation**: All public APIs must be documented

### Key Commands
```bash
# Install dependencies (prefer UV when available)
uv sync --dev
# Fallback: pip install -r requirements.txt

# Run linting and formatting
ruff check --fix
ruff format

# Run type checking
mypy homeassistant/components/arcam_avr/

# Run security analysis
bandit -r homeassistant/components/arcam_avr/

# Run tests
python -m pytest tests/ -v --cov=homeassistant.components.arcam_avr

# Build Docker image
./scripts/build-docker.sh

# Deploy to Kubernetes
kubectl apply -f k8s-deployment.yaml
```

### Git Workflow
- Always pull main branch before creating feature branches
- Use descriptive commit messages following conventional commits
- Create PRs using `gh pr create` with detailed descriptions
- Include 🤖 Generated with [Claude Code](https://claude.ai/code) in commit messages

## Technical Architecture

### Protocol Implementation
- **Binary Protocol**: Uses Arcam's proprietary binary protocol over TCP port 50000
- **Async/Await**: All network operations use asyncio for non-blocking I/O
- **Connection Management**: Automatic reconnection with exponential backoff
- **Broadcast Listening**: Real-time status updates via broadcast messages

### Home Assistant Integration
- **DataUpdateCoordinator**: Centralized data management with adaptive polling
- **ConfigFlow**: User-friendly setup with discovery support
- **MediaPlayerEntity**: Full feature implementation with proper state management
- **Services**: Custom services for advanced control

### Key Classes and Files

#### Core Protocol (`homeassistant/components/arcam_avr/arcam/`)
- `protocol.py:ArcamProtocol` - Main protocol implementation
- `connection.py:ArcamConnection` - TCP connection management
- `commands.py` - Command constants and definitions
- `exceptions.py` - Custom exception hierarchy

#### Home Assistant Integration (`homeassistant/components/arcam_avr/`)
- `coordinator.py:ArcamAvrCoordinator` - Data coordination and state management
- `media_player.py:ArcamAvrMediaPlayer` - Media player entity implementation
- `config_flow.py:ArcamAvrConfigFlow` - Configuration flow handling
- `__init__.py` - Integration setup and entry point

### Testing Strategy
- **Unit Tests**: Individual component testing with mocks
- **Integration Tests**: End-to-end testing with mock devices
- **Protocol Tests**: Direct protocol library validation
- **Performance Tests**: Load and stress testing capabilities

## Common Development Tasks

### Adding New Commands
1. Add command constants to `commands.py`
2. Implement command in `protocol.py`
3. Add service definition to `services.yaml`
4. Update media player entity if needed
5. Add tests for new functionality

### Adding Translations
1. Update `strings.json` with new keys
2. Add translations to each language file in `translations/`
3. Ensure consistency across all languages
4. Test UI with different languages

### Debugging Connection Issues
1. Enable debug logging in configuration.yaml:
   ```yaml
   logger:
     logs:
       homeassistant.components.arcam_avr: debug
   ```
2. Check network connectivity to device
3. Verify device is powered on and responding
4. Test with mock device for protocol validation

### Performance Optimization
- Monitor coordinator update intervals
- Use fast polling only when device is active
- Implement proper error handling and retries
- Cache device state appropriately

## Deployment Options

### Development
```bash
# Local development with Home Assistant dev container
python -m homeassistant --config config/ --debug

# Testing with Docker Compose
docker-compose up -d
```

### Production
```bash
# Kubernetes deployment
kubectl apply -f k8s-deployment.yaml

# Docker Compose production
docker-compose -f docker-compose.yml up -d
```

## Security Considerations

- Never commit secrets or API keys
- Use secure defaults for all configurations
- Implement proper input validation
- Follow Home Assistant security best practices
- Regular security audits with Bandit

## Troubleshooting

### Common Issues
1. **Connection Timeout**: Check network and device power
2. **Command Failures**: Verify device compatibility and protocol version
3. **Discovery Issues**: Ensure devices are on same network segment
4. **Performance Issues**: Adjust update intervals and polling settings

### Debug Tools
- Use `test_protocol.py` for protocol validation
- Enable verbose logging for detailed troubleshooting
- Use mock devices for testing without hardware
- Monitor network traffic with tcpdump/wireshark

## Resources

- [Home Assistant Developer Documentation](https://developers.home-assistant.io/)
- [Arcam Protocol Documentation](docs/DEVELOPMENT.md)
- [Integration Testing Guide](tests/README.md)
- [Deployment Guide](docs/USER_GUIDE.md)

## Contact and Support

- Issues: Use GitHub Issues for bug reports and feature requests
- Development: Follow the contributing guidelines in DEVELOPMENT.md
- Documentation: Keep this file updated with project changes

---

**Note**: This project was developed with assistance from Claude Code. When making significant changes, consider updating this CLAUDE.md file to reflect new patterns, conventions, or architectural decisions.