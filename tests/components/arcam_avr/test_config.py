"""Test configuration and utilities for Arcam AVR integration tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from homeassistant.components.arcam_avr.arcam.protocol import ArcamResponse
from homeassistant.components.arcam_avr.arcam.commands import ArcamCommands


@pytest.fixture
def test_config():
    """Test configuration fixture."""
    return {
        "host": "192.168.1.100",
        "port": 50000,
        "name": "Test AVR",
        "zones": [1, 2],
        "update_interval": 30,
    }


@pytest.fixture
def device_responses():
    """Mock device responses for various commands."""
    return {
        # Power status responses
        "power_status": ArcamResponse(command=0x01, data=0x01, zone=1),
        "power_on": ArcamResponse(command=0x01, data=0x01, zone=1),
        "power_off": ArcamResponse(command=0x01, data=0x00, zone=1),
        
        # Volume responses
        "volume_status": ArcamResponse(command=0x03, data=50, zone=1),
        "volume_set": ArcamResponse(command=0x03, data=75, zone=1),
        "mute_on": ArcamResponse(command=0x04, data=0x01, zone=1),
        "mute_off": ArcamResponse(command=0x04, data=0x00, zone=1),
        
        # Source responses
        "source_status": ArcamResponse(command=0x05, data="BD", zone=1),
        "source_set": ArcamResponse(command=0x05, data="CD", zone=1),
        
        # Device info responses
        "model_info": ArcamResponse(command=0x20, data="AVR11", zone=1),
        "version_info": ArcamResponse(command=0x21, data="2.01", zone=1),
        
        # Error responses
        "command_error": ArcamResponse(command=0xFF, data=0xFF, zone=1),
    }


@pytest.fixture
def broadcast_messages():
    """Mock broadcast messages from device."""
    return [
        {"command": 0x01, "data": 0x01, "zone": 1},  # Power on
        {"command": 0x01, "data": 0x00, "zone": 1},  # Power off
        {"command": 0x03, "data": 65, "zone": 1},    # Volume change
        {"command": 0x04, "data": 0x01, "zone": 1},  # Mute on
        {"command": 0x05, "data": "BD", "zone": 1},  # Source change
    ]


class MockArcamDevice:
    """Enhanced mock Arcam device for integration testing."""
    
    def __init__(self, host="192.168.1.100", port=50000):
        self.host = host
        self.port = port
        self.connected = False
        self.device_state = {
            "power": True,
            "volume": 50,
            "mute": False,
            "source": "BD",
            "model": "AVR11",
            "version": "2.01",
        }
        self.command_history = []
        self.broadcast_callbacks = []
        self.command_delay = 0.01  # 10ms default delay
        
    async def connect(self):
        """Simulate device connection."""
        self.connected = True
        
    async def disconnect(self):
        """Simulate device disconnection."""
        self.connected = False
        
    async def send_command(self, command):
        """Simulate sending command to device."""
        if not self.connected:
            raise ConnectionError("Device not connected")
            
        # Add delay to simulate real device response time
        if self.command_delay > 0:
            await asyncio.sleep(self.command_delay)
            
        self.command_history.append(command)
        
        # Process command and return appropriate response
        if command.command == 0x01:  # Power
            if command.data is not None:
                self.device_state["power"] = bool(command.data)
            return ArcamResponse(
                command=0x01,
                data=1 if self.device_state["power"] else 0,
                zone=command.zone
            )
            
        elif command.command == 0x03:  # Volume
            if command.data is not None:
                self.device_state["volume"] = max(0, min(99, command.data))
            return ArcamResponse(
                command=0x03,
                data=self.device_state["volume"],
                zone=command.zone
            )
            
        elif command.command == 0x04:  # Mute
            if command.data is not None:
                self.device_state["mute"] = bool(command.data)
            return ArcamResponse(
                command=0x04,
                data=1 if self.device_state["mute"] else 0,
                zone=command.zone
            )
            
        elif command.command == 0x05:  # Source
            if command.data is not None:
                self.device_state["source"] = command.data
            return ArcamResponse(
                command=0x05,
                data=self.device_state["source"],
                zone=command.zone
            )
            
        elif command.command == 0x20:  # Model info
            return ArcamResponse(
                command=0x20,
                data=self.device_state["model"],
                zone=command.zone
            )
            
        elif command.command == 0x21:  # Version info
            return ArcamResponse(
                command=0x21,
                data=self.device_state["version"],
                zone=command.zone
            )
            
        else:
            # Unknown command
            raise ValueError(f"Unknown command: {command.command}")
    
    def simulate_broadcast(self, message):
        """Simulate broadcast message from device."""
        for callback in self.broadcast_callbacks:
            callback(message)
    
    def add_broadcast_listener(self, callback):
        """Add broadcast message listener."""
        self.broadcast_callbacks.append(callback)
    
    def set_command_delay(self, delay):
        """Set command processing delay."""
        self.command_delay = delay
    
    def simulate_disconnect(self):
        """Simulate unexpected disconnection."""
        self.connected = False
    
    def simulate_reconnect(self):
        """Simulate reconnection."""
        self.connected = True
    
    def get_command_count(self, command_type=None):
        """Get count of commands sent."""
        if command_type is None:
            return len(self.command_history)
        return len([cmd for cmd in self.command_history if cmd.command == command_type])
    
    def clear_command_history(self):
        """Clear command history."""
        self.command_history.clear()


@pytest.fixture
async def enhanced_mock_connection_factory():
    """Factory for creating enhanced mock connections."""
    async def create_connection(host, port):
        mock_device = MockArcamDevice(host, port)
        
        mock_connection = AsyncMock()
        mock_connection.host = host
        mock_connection.port = port
        mock_connection.device = mock_device
        
        # Setup connection methods
        mock_connection.connect = mock_device.connect
        mock_connection.disconnect = mock_device.disconnect
        mock_connection.send_command = mock_device.send_command
        
        # Broadcast listener setup
        mock_connection.start_broadcast_listener = AsyncMock()
        mock_connection.stop_broadcast_listener = AsyncMock()
        mock_connection.add_broadcast_callback = mock_device.add_broadcast_listener
        
        # Connect by default
        await mock_device.connect()
        
        return mock_connection
    
    return create_connection


@pytest.fixture
def error_scenarios():
    """Common error scenarios for testing."""
    return {
        "connection_timeout": ConnectionError("Connection timeout"),
        "connection_refused": ConnectionError("Connection refused"),
        "device_not_responding": TimeoutError("Device not responding"),
        "invalid_response": ValueError("Invalid response format"),
        "protocol_error": RuntimeError("Protocol error"),
        "network_error": OSError("Network unreachable"),
    }


@pytest.fixture
def performance_metrics():
    """Performance metrics and thresholds for testing."""
    return {
        "max_startup_time": 3.0,      # seconds
        "max_command_time": 1.0,      # seconds
        "max_update_time": 0.5,       # seconds
        "max_memory_growth": 10,      # MB
        "min_command_success_rate": 0.95,  # 95%
        "max_error_recovery_time": 2.0,    # seconds
    }


class TestDataGenerator:
    """Generate test data for various scenarios."""
    
    @staticmethod
    def generate_device_states(count=10):
        """Generate various device states for testing."""
        import random
        
        states = []
        sources = ["BD", "CD", "DVD", "SAT", "PVR", "VCR", "TAPE", "TUNER"]
        
        for i in range(count):
            state = {
                "power": random.choice([True, False]),
                "volume": random.randint(0, 99),
                "mute": random.choice([True, False]),
                "source": random.choice(sources),
                "available": True,
            }
            states.append(state)
        
        return states
    
    @staticmethod
    def generate_command_sequences(count=20):
        """Generate command sequences for testing."""
        import random
        
        sequences = []
        
        for _ in range(count):
            sequence = []
            
            # Power command
            if random.choice([True, False]):
                sequence.append(("power", random.choice([True, False])))
            
            # Volume commands
            if random.choice([True, False]):
                sequence.append(("volume", random.randint(0, 99)))
            
            # Mute command
            if random.choice([True, False]):
                sequence.append(("mute", random.choice([True, False])))
            
            # Source command
            if random.choice([True, False]):
                sources = ["BD", "CD", "DVD", "SAT"]
                sequence.append(("source", random.choice(sources)))
            
            sequences.append(sequence)
        
        return sequences


@pytest.fixture
def test_data_generator():
    """Test data generator fixture."""
    return TestDataGenerator()


def pytest_configure(config):
    """Configure pytest for Arcam AVR tests."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "hardware: marks tests that require hardware"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Mark slow tests
        if "performance" in item.nodeid or "test_performance" in item.nodeid:
            item.add_marker(pytest.mark.slow)
            item.add_marker(pytest.mark.performance)
        
        # Mark integration tests
        if "integration" in item.nodeid or "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Mark device communication tests
        if "device_communication" in item.nodeid:
            item.add_marker(pytest.mark.integration)