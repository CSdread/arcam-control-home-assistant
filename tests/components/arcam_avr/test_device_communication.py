"""Device communication integration tests for Arcam AVR."""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from homeassistant.components.arcam_avr.arcam.protocol import ArcamCommand, ArcamResponse
from homeassistant.components.arcam_avr.arcam.commands import ArcamCommands
from homeassistant.components.arcam_avr.coordinator import ArcamAvrCoordinator
from homeassistant.components.arcam_avr.const import DOMAIN

from tests.common import MockConfigEntry


async def test_device_query_sequence(hass, mock_connection_factory):
    """Test the device query sequence during startup."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        mock_connection_class.return_value = mock_connection
        
        # Setup coordinator
        coordinator = ArcamAvrCoordinator(hass, config_entry, mock_connection)
        
        # Test initial device queries
        await coordinator.async_config_entry_first_refresh()
        
        # Verify multiple commands were sent for device info
        assert mock_connection.send_command.call_count >= 3
        
        # Check that device info was retrieved
        assert coordinator.data is not None
        assert "available" in coordinator.data


async def test_broadcast_message_processing(hass, mock_connection_factory):
    """Test processing of broadcast messages from device."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        mock_connection_class.return_value = mock_connection
        
        coordinator = ArcamAvrCoordinator(hass, config_entry, mock_connection)
        
        # Simulate broadcast listener callback
        broadcast_data = {
            "command": 0x01,  # Power status
            "data": 0x01,     # Power on
            "zone": 1
        }
        
        # Call the broadcast handler
        await coordinator._handle_broadcast_message(broadcast_data)
        
        # Verify state was updated
        assert coordinator.data["power"] is True


async def test_command_retry_mechanism(hass, mock_connection_factory):
    """Test command retry mechanism on failures."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        
        # First call fails, second succeeds
        mock_connection.send_command.side_effect = [
            ConnectionError("Timeout"),
            ArcamResponse(command=0x01, data=0x01, zone=1)
        ]
        mock_connection_class.return_value = mock_connection
        
        coordinator = ArcamAvrCoordinator(hass, config_entry, mock_connection)
        
        # Execute command with retry
        power_on_cmd = ArcamCommands.power_on(1)
        result = await coordinator.async_send_command(power_on_cmd, 1)
        
        # Should have retried and succeeded
        assert mock_connection.send_command.call_count == 2
        assert result is not None


async def test_concurrent_command_execution(hass, mock_connection_factory):
    """Test handling of concurrent command execution."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        mock_connection_class.return_value = mock_connection
        
        coordinator = ArcamAvrCoordinator(hass, config_entry, mock_connection)
        
        # Execute multiple commands concurrently
        commands = [
            coordinator.async_send_command(ArcamCommands.power_on(1), 1),
            coordinator.async_send_command(ArcamCommands.set_volume(50, 1), 50, 1),
            coordinator.async_send_command(ArcamCommands.set_source("BD", 1), "BD", 1),
        ]
        
        results = await asyncio.gather(*commands, return_exceptions=True)
        
        # All commands should complete without exceptions
        assert len(results) == 3
        assert all(not isinstance(r, Exception) for r in results)


async def test_device_disconnection_recovery(hass, mock_connection_factory):
    """Test recovery behavior when device disconnects."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        mock_connection_class.return_value = mock_connection
        
        coordinator = ArcamAvrCoordinator(hass, config_entry, mock_connection)
        
        # Initial successful state
        await coordinator.async_config_entry_first_refresh()
        assert coordinator.last_update_success is True
        
        # Simulate device disconnection
        mock_connection.send_command.side_effect = ConnectionError("Device disconnected")
        
        # Next update should fail
        await coordinator._async_update_data()
        assert coordinator.last_update_success is False
        
        # Simulate reconnection
        mock_connection.send_command.side_effect = None
        mock_connection.send_command.return_value = ArcamResponse(command=0x01, data=0x01, zone=1)
        
        # Recovery should work
        await coordinator._async_update_data()
        assert coordinator.last_update_success is True


async def test_zone_specific_commands(hass, mock_connection_factory):
    """Test zone-specific command routing."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
            "zones": [1, 2],
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        mock_connection_class.return_value = mock_connection
        
        coordinator = ArcamAvrCoordinator(hass, config_entry, mock_connection)
        
        # Test zone 1 command
        await coordinator.async_send_command(ArcamCommands.power_on(1), 1)
        
        # Verify command was sent with correct zone
        args = mock_connection.send_command.call_args[0]
        assert args[0].zone == 1
        
        # Test zone 2 command
        await coordinator.async_send_command(ArcamCommands.power_on(2), 2)
        
        # Verify command was sent with correct zone
        args = mock_connection.send_command.call_args[0]
        assert args[0].zone == 2


async def test_adaptive_polling_intervals(hass, mock_connection_factory):
    """Test adaptive polling interval adjustment."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        mock_connection_class.return_value = mock_connection
        
        coordinator = ArcamAvrCoordinator(hass, config_entry, mock_connection)
        
        # Initial interval should be default
        initial_interval = coordinator.update_interval
        
        # Simulate device being powered on (fast polling)
        coordinator.data = {"power": True, "available": True}
        coordinator._adjust_update_interval()
        
        fast_interval = coordinator.update_interval
        assert fast_interval < initial_interval
        
        # Simulate device being powered off (slow polling)
        coordinator.data = {"power": False, "available": True}
        coordinator._adjust_update_interval()
        
        slow_interval = coordinator.update_interval
        assert slow_interval > fast_interval


async def test_protocol_error_handling(hass, mock_connection_factory):
    """Test handling of protocol-level errors."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        mock_connection_class.return_value = mock_connection
        
        coordinator = ArcamAvrCoordinator(hass, config_entry, mock_connection)
        
        # Simulate various protocol errors
        from homeassistant.components.arcam_avr.arcam.exceptions import (
            ArcamError,
            ArcamProtocolError,
            ArcamCommandError,
        )
        
        error_scenarios = [
            ArcamProtocolError("Invalid response"),
            ArcamCommandError("Command not supported"),
            ArcamError("General error"),
        ]
        
        for error in error_scenarios:
            mock_connection.send_command.side_effect = error
            
            # Should not crash coordinator
            try:
                await coordinator.async_send_command(ArcamCommands.power_on(1), 1)
            except Exception as e:
                pytest.fail(f"Coordinator should handle {type(error).__name__} gracefully, but raised: {e}")


async def test_data_validation_and_sanitization(hass, mock_connection_factory):
    """Test data validation and sanitization from device."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        mock_connection_class.return_value = mock_connection
        
        coordinator = ArcamAvrCoordinator(hass, config_entry, mock_connection)
        
        # Test various invalid data scenarios
        invalid_data_sets = [
            {"volume": 150},      # Volume out of range
            {"volume": -10},      # Negative volume
            {"source": None},     # None source
            {"power": "invalid"}, # Invalid power state
            {},                   # Empty data
        ]
        
        for invalid_data in invalid_data_sets:
            # Coordinator should sanitize and validate data
            coordinator._update_device_state(invalid_data)
            
            # Data should be properly sanitized
            if "volume" in invalid_data:
                if invalid_data["volume"] > 99:
                    assert coordinator.data.get("volume", 0) <= 99
                elif invalid_data["volume"] < 0:
                    assert coordinator.data.get("volume", 0) >= 0


async def test_command_queue_management(hass, mock_connection_factory):
    """Test command queue management under load."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        
        # Add delay to simulate slow device
        async def slow_send_command(command):
            await asyncio.sleep(0.1)
            return ArcamResponse(command=command.command, data=0x01, zone=command.zone)
        
        mock_connection.send_command.side_effect = slow_send_command
        mock_connection_class.return_value = mock_connection
        
        coordinator = ArcamAvrCoordinator(hass, config_entry, mock_connection)
        
        # Queue multiple commands rapidly
        start_time = asyncio.get_event_loop().time()
        
        commands = []
        for i in range(10):
            cmd = coordinator.async_send_command(ArcamCommands.power_on(1), 1)
            commands.append(cmd)
        
        # All commands should complete
        await asyncio.gather(*commands)
        
        end_time = asyncio.get_event_loop().time()
        
        # Should have taken reasonable time (commands should be queued, not all parallel)
        duration = end_time - start_time
        assert duration > 0.5  # At least some serialization occurred
        assert duration < 2.0  # But not too slow


async def test_device_model_detection(hass, mock_connection_factory):
    """Test device model detection from responses."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test AVR",
        data={
            "host": "192.168.1.100",
            "port": 50000,
            "name": "Test AVR",
        },
        entry_id="test_entry_id",
    )
    
    with patch(
        "homeassistant.components.arcam_avr.coordinator.ArcamConnection"
    ) as mock_connection_class:
        mock_connection = await mock_connection_factory("192.168.1.100", 50000)
        
        # Mock device info responses
        def mock_send_command(command):
            if command.command == 0x20:  # Model query
                return ArcamResponse(command=0x20, data="AVR550", zone=1)
            elif command.command == 0x21:  # Version query
                return ArcamResponse(command=0x21, data="1.15", zone=1)
            else:
                return ArcamResponse(command=command.command, data=0x01, zone=command.zone)
        
        mock_connection.send_command.side_effect = mock_send_command
        mock_connection_class.return_value = mock_connection
        
        coordinator = ArcamAvrCoordinator(hass, config_entry, mock_connection)
        await coordinator.async_config_entry_first_refresh()
        
        # Check that device info was detected
        assert "device_info" in coordinator.data
        device_info = coordinator.data["device_info"]
        assert device_info["model"] == "AVR550"
        assert device_info["sw_version"] == "1.15"