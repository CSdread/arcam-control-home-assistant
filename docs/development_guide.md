# Arcam AVR Development Guide

Comprehensive guide for developers contributing to the Arcam AVR Home Assistant integration.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment](#development-environment)
3. [Code Standards](#code-standards)
4. [Testing Strategy](#testing-strategy)
5. [Pull Request Process](#pull-request-process)
6. [Release Process](#release-process)
7. [Architecture Guidelines](#architecture-guidelines)
8. [Debugging](#debugging)

## Getting Started

### Prerequisites

Before contributing, ensure you have:
- Python 3.11 or higher
- Git with commit signing configured
- UV package manager (recommended)
- Basic understanding of Home Assistant integrations
- Familiarity with asyncio and TCP networking

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/your-repo/arcam-control-home-assistant.git
cd arcam-control-home-assistant

# Create virtual environment
uv venv
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\activate  # Windows

# Install dependencies
uv sync --dev

# Install pre-commit hooks
pre-commit install

# Verify setup
python -m pytest tests/ -x
```

## Development Environment

### UV Package Manager Setup

We strongly recommend using UV for dependency management:

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync

# Add new dependencies
uv add requests  # Runtime dependency
uv add --dev pytest  # Development dependency

# Update dependencies
uv lock --upgrade
```

### IDE Configuration

#### VS Code Setup
Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "none",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
```

#### PyCharm Setup
1. Set interpreter to `.venv/bin/python`
2. Enable Ruff for linting and formatting
3. Configure pytest as test runner
4. Set project root correctly

### Environment Variables

Create `.env` file for development:
```bash
# Development settings
PYTHONPATH=.
HA_DEV_MODE=1
ARCAM_DEBUG=1

# Test device configuration (optional)
TEST_ARCAM_HOST=192.168.1.100
TEST_ARCAM_PORT=50000
```

### Docker Development (Optional)

For containerized development:
```dockerfile
# Dockerfile.dev
FROM python:3.11-slim

WORKDIR /workspace
COPY . .

RUN pip install uv
RUN uv sync --dev

CMD ["python", "-m", "pytest", "tests/"]
```

```bash
# Build and run
docker build -f Dockerfile.dev -t arcam-dev .
docker run -v $(pwd):/workspace arcam-dev
```

## Code Standards

### Code Style

We use Ruff for linting and formatting:

```bash
# Format code
ruff format .

# Check for linting issues
ruff check .

# Fix auto-fixable issues
ruff check . --fix
```

#### Ruff Configuration (`pyproject.toml`)
```toml
[tool.ruff]
target-version = "py311"
line-length = 88
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "N",  # pep8-naming
    "UP", # pyupgrade
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
]
ignore = [
    "E501",  # Line too long (handled by formatter)
]

[tool.ruff.per-file-ignores]
"tests/*" = ["N802", "N803"]  # Allow mixed case in tests
```

### Type Hints

Use type hints consistently:
```python
from typing import Any, Dict, List, Optional, Union
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

async def async_setup_entry(
    hass: HomeAssistant, 
    entry: ConfigEntry
) -> bool:
    """Set up Arcam AVR from a config entry."""
    data: Dict[str, Any] = entry.data
    # Implementation...
```

### Documentation Standards

#### Docstrings
Use Google-style docstrings:
```python
async def send_command(
    self, 
    command: ArcamCommand, 
    timeout: float = 5.0
) -> ArcamResponse:
    """Send command to Arcam device.
    
    Args:
        command: The command to send to the device.
        timeout: Maximum time to wait for response in seconds.
        
    Returns:
        Response from the device.
        
    Raises:
        ConnectionError: If device is not reachable.
        TimeoutError: If command times out.
        ArcamProtocolError: If protocol communication fails.
    """
```

#### Comments
- Use comments sparingly for complex logic
- Prefer self-documenting code
- Include TODO comments with GitHub issues when applicable

### Error Handling

#### Custom Exceptions
```python
from homeassistant.components.arcam_avr.arcam.exceptions import (
    ArcamError,
    ArcamConnectionError,
    ArcamProtocolError,
    ArcamCommandError,
)

try:
    response = await connection.send_command(command)
except ArcamConnectionError:
    # Handle connection issues
    _LOGGER.warning("Failed to connect to device")
    return False
except ArcamProtocolError as err:
    # Handle protocol errors
    _LOGGER.error("Protocol error: %s", err)
    raise
```

#### Logging
```python
import logging
_LOGGER = logging.getLogger(__name__)

# Use appropriate log levels
_LOGGER.debug("Sending command: %s", command)
_LOGGER.info("Connected to device at %s:%d", host, port)
_LOGGER.warning("Device not responding, retrying...")
_LOGGER.error("Failed to setup integration: %s", err)
```

### Async Patterns

#### Proper Async Usage
```python
import asyncio
from typing import Any, Callable

class ArcamConnection:
    async def __aenter__(self):
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

# Use context managers
async def example_usage():
    async with ArcamConnection(host, port) as conn:
        response = await conn.send_command(command)
        return response
```

#### Timeout Handling
```python
import asyncio

async def send_command_with_timeout(
    command: ArcamCommand, 
    timeout: float = 5.0
) -> ArcamResponse:
    """Send command with timeout."""
    try:
        return await asyncio.wait_for(
            self._send_command(command), 
            timeout=timeout
        )
    except asyncio.TimeoutError:
        raise ArcamCommandError(f"Command timeout after {timeout}s")
```

## Testing Strategy

### Test Structure

#### Test Organization
```
tests/components/arcam_avr/
├── __init__.py
├── conftest.py                 # Shared fixtures
├── test_init.py               # Integration tests
├── test_config_flow.py        # Configuration tests
├── test_coordinator.py        # Coordinator tests
├── test_media_player.py       # Entity tests
├── test_integration.py        # End-to-end tests
├── test_performance.py        # Performance tests
├── arcam/                     # Protocol tests
│   ├── test_protocol.py
│   ├── test_commands.py
│   └── test_connection.py
└── fixtures/                  # Test data
    └── __init__.py
```

#### Test Categories

**Unit Tests**: Test individual components in isolation
```python
async def test_command_encoding():
    """Test command encoding produces correct bytes."""
    command = ArcamCommand(command=0x01, data=0x01, zone=1)
    encoded = encode_command(command)
    assert encoded == b'\x02\x01\x01\x01\x03\x03'
```

**Integration Tests**: Test component interactions
```python
async def test_coordinator_command_execution(
    hass, mock_config_entry, mock_connection
):
    """Test coordinator executes commands correctly."""
    coordinator = ArcamAvrCoordinator(hass, mock_config_entry, mock_connection)
    result = await coordinator.async_send_command(
        ArcamCommands.power_on, 1
    )
    assert result is True
    mock_connection.send_command.assert_called_once()
```

**Performance Tests**: Validate timing and resource usage
```python
async def test_command_performance():
    """Test command execution meets performance requirements."""
    start_time = time.time()
    await coordinator.async_send_command(ArcamCommands.power_on, 1)
    execution_time = time.time() - start_time
    assert execution_time < 1.0  # Must complete within 1 second
```

### Test Fixtures

#### Shared Fixtures (`conftest.py`)
```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
    )

@pytest.fixture
async def mock_connection():
    """Create a mock connection."""
    connection = AsyncMock()
    connection.send_command.return_value = ArcamResponse(
        command=0x01, data=0x01, zone=1
    )
    return connection
```

#### Mock Device Factory
```python
@pytest.fixture
async def mock_device_factory():
    """Factory for creating realistic mock devices."""
    async def create_device(host: str, port: int):
        device = MockArcamDevice(host, port)
        await device.connect()
        return device
    return create_device
```

### Running Tests

#### Basic Test Execution
```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/components/arcam_avr/test_coordinator.py

# Run with coverage
python -m pytest --cov=homeassistant.components.arcam_avr tests/

# Run only fast tests
python -m pytest -m "not slow" tests/
```

#### Test Configuration
```bash
# Run with verbose output
python -m pytest -v tests/

# Stop on first failure
python -m pytest -x tests/

# Run specific test by name
python -m pytest -k "test_power_on" tests/

# Run with live logging
python -m pytest --log-cli-level=DEBUG tests/
```

#### Performance Testing
```bash
# Run performance tests
python tests/components/arcam_avr/run_integration_tests.py --performance

# Monitor memory usage
python -m pytest tests/components/arcam_avr/test_performance.py::test_memory_usage -v
```

### Test Data Management

#### Creating Test Data
```python
# Use factories for consistent test data
def create_test_device_info() -> dict:
    """Create standardized device info for tests."""
    return {
        "model": "AVR11",
        "version": "2.01",
        "serial": "TEST123456",
        "zones": [1, 2],
    }

# Use parametrization for multiple scenarios
@pytest.mark.parametrize("volume,expected", [
    (0, 0.0),
    (50, 0.505),
    (99, 1.0),
])
def test_volume_conversion(volume, expected):
    """Test volume conversion with various inputs."""
    result = device_volume_to_ha_volume(volume)
    assert abs(result - expected) < 0.01
```

## Pull Request Process

### Branch Strategy

We use a feature branch workflow:

```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add new feature"

# Push branch
git push -u origin feature/your-feature-name
```

### Commit Messages

Follow conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

#### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

#### Examples
```bash
git commit -m "feat(coordinator): add adaptive polling intervals"
git commit -m "fix(protocol): handle malformed broadcast messages"
git commit -m "docs: update configuration examples"
git commit -m "test: add integration tests for multi-zone setup"
```

### Pre-commit Checks

Before submitting, ensure all checks pass:

```bash
# Run pre-commit hooks
pre-commit run --all-files

# Run tests
python -m pytest tests/

# Check type hints
mypy homeassistant/components/arcam_avr/

# Verify no security issues
bandit -r homeassistant/components/arcam_avr/
```

### Pull Request Template

When creating a PR, include:

#### Description
- Clear description of changes
- Problem being solved
- Solution approach

#### Testing
- Test cases added/updated
- Manual testing performed
- Performance impact assessment

#### Documentation
- Documentation updates
- Breaking changes noted
- Migration guide if needed

#### Checklist
- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Performance impact assessed

### Code Review Process

#### As Author
1. Ensure PR is ready for review
2. Add appropriate labels and reviewers
3. Respond to feedback constructively
4. Update based on review comments

#### As Reviewer
1. Review code for correctness and style
2. Test functionality if possible
3. Provide constructive feedback
4. Approve when satisfied with changes

## Release Process

### Versioning

We follow semantic versioning (SemVer):
- `MAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features (backward compatible)
- Patch: Bug fixes (backward compatible)

### Release Checklist

#### Pre-release
- [ ] All tests pass
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in `manifest.json`
- [ ] No known critical issues

#### Release Steps
1. Create release branch from main
2. Update version numbers
3. Update CHANGELOG.md
4. Create release PR
5. Tag release after merge
6. Publish release notes

#### Post-release
- [ ] Update main branch
- [ ] Archive old versions if needed
- [ ] Update documentation site
- [ ] Notify community

### Hotfix Process

For critical bug fixes:
1. Create hotfix branch from latest release tag
2. Apply minimal fix
3. Test thoroughly
4. Release as patch version
5. Merge back to main

## Architecture Guidelines

### Design Principles

#### Separation of Concerns
- Protocol logic separate from HA integration
- Clear boundaries between layers
- Single responsibility for each class

#### Error Resilience
- Graceful degradation on failures
- Automatic recovery where possible
- Clear error reporting to users

#### Performance First
- Async operations throughout
- Efficient resource usage
- Minimal blocking operations

### Code Organization

#### Module Structure
```python
# Clear module boundaries
homeassistant/components/arcam_avr/
├── __init__.py          # Integration setup
├── coordinator.py       # Data management
├── config_flow.py      # User interface
├── media_player.py     # HA entity
└── arcam/              # Protocol library
    ├── protocol.py     # Low-level protocol
    ├── commands.py     # Command definitions
    └── connection.py   # Network handling
```

#### Dependency Management
- Minimize external dependencies
- Use Home Assistant utilities when available
- Clearly document any new dependencies

### API Design

#### Consistent Interfaces
```python
# Use consistent method signatures
async def async_send_command(
    self, 
    command_func: Callable[..., ArcamCommand],
    *args: Any,
    **kwargs: Any
) -> bool:
```

#### Error Handling
```python
# Clear exception hierarchy
class ArcamError(Exception):
    """Base exception for Arcam integration."""

class ArcamConnectionError(ArcamError):
    """Connection-related errors."""

class ArcamProtocolError(ArcamError):
    """Protocol communication errors."""
```

## Debugging

### Local Development

#### Debug Configuration
```python
# Enable debug logging
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Protocol debugging
logger = logging.getLogger('homeassistant.components.arcam_avr.arcam.protocol')
logger.setLevel(logging.DEBUG)
```

#### Mock Device Testing
```python
# Create local mock for testing
from tests.components.arcam_avr.test_config import MockArcamDevice

async def debug_session():
    device = MockArcamDevice("127.0.0.1", 50000)
    await device.connect()
    
    # Test commands
    response = await device.send_command(
        ArcamCommand(command=0x01, data=0x01, zone=1)
    )
    print(f"Response: {response}")

asyncio.run(debug_session())
```

### Production Debugging

#### Log Analysis
```bash
# Monitor Home Assistant logs
tail -f /config/home-assistant.log | grep arcam_avr

# Filter specific component logs
grep "arcam_avr" /config/home-assistant.log | tail -50
```

#### Network Debugging
```bash
# Monitor network traffic
tcpdump -i any host 192.168.1.100 and port 50000

# Test connectivity
nc -v 192.168.1.100 50000
```

### Common Issues

#### Import Errors
```python
# Ensure proper Python path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

#### Async Context Issues
```python
# Use proper async context
async def test_function():
    async with aiohttp.ClientSession() as session:
        # Use session for requests
        pass

# Avoid mixing sync and async
# Bad: time.sleep() in async function
# Good: await asyncio.sleep()
```

#### Memory Leaks
```python
# Always clean up resources
class ConnectionManager:
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
        
    async def cleanup(self):
        """Clean up connections and callbacks."""
        if self.connection:
            await self.connection.close()
        self.callbacks.clear()
```

## Contributing Guidelines

### First-Time Contributors

1. **Start Small**: Begin with documentation fixes or minor bug fixes
2. **Read Code**: Familiarize yourself with existing codebase
3. **Ask Questions**: Use GitHub discussions for clarification
4. **Follow Examples**: Look at existing similar implementations

### Communication

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and design discussions
- **Pull Requests**: Code changes and improvements
- **Discord/IRC**: Real-time discussions (if available)

### Recognition

Contributors are recognized in:
- CHANGELOG.md for each release
- Contributors section in README.md
- GitHub contributor statistics

---

## Additional Resources

- [Home Assistant Developer Documentation](https://developers.home-assistant.io/)
- [Python Async Programming](https://docs.python.org/3/library/asyncio.html)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Git Best Practices](https://www.conventionalcommits.org/)

---

*This development guide is updated regularly. Please check for the latest version before starting development.*