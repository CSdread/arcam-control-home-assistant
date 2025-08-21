"""Shared fixtures for Arcam AVR tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME
from tests.common import MockConfigEntry

from .fixtures.mock_device import MockArcamDevice

# Test constants
TEST_HOST = "192.168.1.100"
TEST_PORT = 50000
TEST_NAME = "Test AVR"
TEST_MODEL = "AVR11"
TEST_VERSION = "2.01"

@pytest.fixture
def mock_arcam_device():
    """Create mock Arcam device."""
    return MockArcamDevice()


@pytest.fixture
def mock_config_entry():
    """Create mock config entry."""
    return MockConfigEntry(
        domain="arcam_avr",
        data={
            CONF_HOST: TEST_HOST,
            CONF_PORT: TEST_PORT,
            CONF_NAME: TEST_NAME,
            "model": TEST_MODEL,
            "version": TEST_VERSION,
        },
        entry_id="test_entry_id",
        title=f"Arcam {TEST_MODEL}",
    )


@pytest.fixture
def mock_coordinator(hass, mock_config_entry):
    """Create mock coordinator."""
    from homeassistant.components.arcam_avr.coordinator import ArcamAvrCoordinator
    
    coordinator = ArcamAvrCoordinator(hass, mock_config_entry)
    coordinator.arcam = AsyncMock()
    coordinator.data = {
        "power": True,
        "volume": 50,
        "mute": False,
        "source": "BD",
        "available": True,
        "model": TEST_MODEL,
        "version": TEST_VERSION,
    }
    coordinator.last_update_success = True
    return coordinator


@pytest.fixture
def mock_connection():
    """Create mock connection."""
    connection = AsyncMock()
    connection.host = TEST_HOST
    connection.port = TEST_PORT
    connection.is_connected = True
    return connection


@pytest.fixture
async def mock_connection_factory(mock_arcam_device):
    """Create mock connection factory that returns mock device responses."""
    
    async def create_mock_connection(host, port):
        """Create a mock connection that uses the mock device."""
        connection = AsyncMock()
        connection.host = host
        connection.port = port
        connection.is_connected = True
        
        # Mock send_command to use mock device
        async def mock_send_command(command):
            from homeassistant.components.arcam_avr.arcam.protocol import ArcamProtocol
            
            command_bytes = ArcamProtocol.encode_command(command)
            response_bytes = await mock_arcam_device.send_command(command_bytes)
            return ArcamProtocol.decode_response(response_bytes)
        
        connection.send_command = mock_send_command
        
        # Mock other connection methods
        connection.connect = AsyncMock()
        connection.disconnect = AsyncMock()
        connection.start_broadcast_listener = AsyncMock()
        connection.stop_broadcast_listener = AsyncMock()
        connection.get_device_info = AsyncMock(return_value={
            "host": host,
            "port": port,
            "version": TEST_VERSION,
            "connected": True,
        })
        
        await mock_arcam_device.connect()
        return connection
    
    return create_mock_connection