"""Performance tests for Arcam AVR integration."""
import asyncio
import time
import pytest
from unittest.mock import AsyncMock, patch

from homeassistant.components.arcam_avr.coordinator import ArcamAvrCoordinator
from homeassistant.components.arcam_avr.arcam.protocol import ArcamResponse
from homeassistant.components.arcam_avr.arcam.commands import ArcamCommands
from homeassistant.components.arcam_avr.const import DOMAIN

from tests.common import MockConfigEntry


@pytest.mark.asyncio
async def test_coordinator_update_performance(hass, mock_connection_factory):
    """Test coordinator update performance."""
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
        
        # Measure time for initial refresh
        start_time = time.time()
        await coordinator.async_config_entry_first_refresh()
        initial_time = time.time() - start_time
        
        # Initial refresh should complete quickly
        assert initial_time < 2.0, f"Initial refresh took {initial_time:.2f}s, expected < 2.0s"
        
        # Measure time for subsequent updates
        update_times = []
        for _ in range(10):
            start_time = time.time()
            await coordinator._async_update_data()
            update_time = time.time() - start_time
            update_times.append(update_time)
        
        # Updates should be fast and consistent
        avg_update_time = sum(update_times) / len(update_times)
        max_update_time = max(update_times)
        
        assert avg_update_time < 0.5, f"Average update time {avg_update_time:.2f}s, expected < 0.5s"
        assert max_update_time < 1.0, f"Max update time {max_update_time:.2f}s, expected < 1.0s"


@pytest.mark.asyncio
async def test_concurrent_command_performance(hass, mock_connection_factory):
    """Test performance with concurrent commands."""
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
        
        # Add realistic delay to commands
        async def delayed_send_command(command):
            await asyncio.sleep(0.01)  # 10ms delay per command
            return ArcamResponse(command=command.command, data=0x01, zone=command.zone)
        
        mock_connection.send_command.side_effect = delayed_send_command
        mock_connection_class.return_value = mock_connection
        
        coordinator = ArcamAvrCoordinator(hass, config_entry, mock_connection)
        
        # Test concurrent command execution
        num_commands = 20
        commands = []
        
        start_time = time.time()
        for i in range(num_commands):
            cmd = coordinator.async_send_command(ArcamCommands.power_on(1), 1)
            commands.append(cmd)
        
        # Execute all commands
        await asyncio.gather(*commands)
        total_time = time.time() - start_time
        
        # Commands should be queued efficiently
        # With 10ms delay per command, 20 commands should take ~200ms + overhead
        assert total_time < 1.0, f"20 commands took {total_time:.2f}s, expected < 1.0s"
        assert total_time > 0.15, f"Commands completed too quickly ({total_time:.2f}s), may not be queued properly"


@pytest.mark.asyncio
async def test_memory_usage_stability(hass, mock_connection_factory):
    """Test memory usage remains stable during operation."""
    import gc
    import psutil
    import os
    
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
        await coordinator.async_config_entry_first_refresh()
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Simulate extended operation
        for cycle in range(100):
            # Update coordinator data
            await coordinator._async_update_data()
            
            # Send some commands
            await coordinator.async_send_command(ArcamCommands.power_on(1), 1)
            await coordinator.async_send_command(ArcamCommands.set_volume(50, 1), 50, 1)
            
            # Periodic garbage collection
            if cycle % 20 == 0:
                gc.collect()
        
        # Final memory check
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be minimal (less than 10MB)
        assert memory_growth < 10 * 1024 * 1024, f"Memory grew by {memory_growth / 1024 / 1024:.1f}MB"


@pytest.mark.asyncio
async def test_rapid_state_updates_performance(hass, mock_connection_factory):
    """Test performance with rapid state updates."""
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
        
        # Track update listener calls
        update_count = 0
        
        def mock_listener():
            nonlocal update_count
            update_count += 1
        
        coordinator.async_add_listener(mock_listener)
        
        # Rapid state updates
        start_time = time.time()
        for i in range(100):
            coordinator.data = {
                "power": i % 2 == 0,
                "volume": i % 100,
                "source": "BD" if i % 2 == 0 else "CD",
                "available": True
            }
            coordinator.async_update_listeners()
            
            # Allow some processing time every 10 updates
            if i % 10 == 0:
                await asyncio.sleep(0.001)
        
        # Wait for all updates to process
        await asyncio.sleep(0.1)
        update_time = time.time() - start_time
        
        # Updates should process quickly
        assert update_time < 1.0, f"100 rapid updates took {update_time:.2f}s, expected < 1.0s"
        assert update_count == 100, f"Expected 100 updates, got {update_count}"


@pytest.mark.asyncio
async def test_error_recovery_performance(hass, mock_connection_factory):
    """Test performance during error conditions and recovery."""
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
        
        # Simulate intermittent failures
        call_count = 0
        
        def failing_send_command(command):
            nonlocal call_count
            call_count += 1
            if call_count % 3 == 0:  # Every third call fails
                raise ConnectionError("Simulated failure")
            return ArcamResponse(command=command.command, data=0x01, zone=command.zone)
        
        mock_connection.send_command.side_effect = failing_send_command
        mock_connection_class.return_value = mock_connection
        
        coordinator = ArcamAvrCoordinator(hass, config_entry, mock_connection)
        
        # Test error recovery performance
        success_count = 0
        error_count = 0
        
        start_time = time.time()
        for _ in range(30):  # 30 commands with 1/3 failure rate
            try:
                await coordinator.async_send_command(ArcamCommands.power_on(1), 1)
                success_count += 1
            except Exception:
                error_count += 1
        
        total_time = time.time() - start_time
        
        # Should handle errors gracefully without significant performance impact
        assert total_time < 5.0, f"Error recovery took {total_time:.2f}s, expected < 5.0s"
        assert success_count > 15, f"Only {success_count} successes out of 30, expected > 15"
        assert error_count < 15, f"Too many errors: {error_count}, expected < 15"


@pytest.mark.asyncio
async def test_large_data_handling_performance(hass, mock_connection_factory):
    """Test performance with large data payloads."""
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
        
        # Test with large state data
        large_data = {
            "power": True,
            "volume": 50,
            "source": "BD",
            "available": True,
            "device_info": {
                "model": "AVR850",
                "version": "2.15",
                "serial": "1234567890",
                "capabilities": ["zone1", "zone2", "zone3"],
                "sources": {f"input_{i}": f"Source {i}" for i in range(50)},
                "presets": {f"preset_{i}": f"Preset {i}" for i in range(100)},
            },
            "extra_data": "x" * 1000,  # 1KB of extra data
        }
        
        start_time = time.time()
        for _ in range(50):
            coordinator.data = large_data.copy()
            coordinator.async_update_listeners()
            await asyncio.sleep(0.001)  # Small delay to allow processing
        
        processing_time = time.time() - start_time
        
        # Should handle large data efficiently
        assert processing_time < 2.0, f"Large data processing took {processing_time:.2f}s, expected < 2.0s"


@pytest.mark.asyncio
async def test_startup_performance(hass, mock_connection_factory):
    """Test integration startup performance."""
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
        
        # Measure full integration setup time
        config_entry.add_to_hass(hass)
        
        start_time = time.time()
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        setup_time = time.time() - start_time
        
        # Integration should start up quickly
        assert setup_time < 3.0, f"Integration setup took {setup_time:.2f}s, expected < 3.0s"
        
        # Verify entity is available
        state = hass.states.get("media_player.test_avr")
        assert state is not None


@pytest.mark.asyncio
async def test_cleanup_performance(hass, mock_connection_factory):
    """Test integration cleanup performance."""
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
        
        # Setup integration
        config_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        
        # Add some state data and listeners
        coordinator = hass.data[DOMAIN][config_entry.entry_id]
        
        # Add multiple listeners
        listeners = []
        for i in range(10):
            listener = lambda: None
            coordinator.async_add_listener(listener)
            listeners.append(listener)
        
        # Measure cleanup time
        start_time = time.time()
        assert await hass.config_entries.async_unload(config_entry.entry_id)
        await hass.async_block_till_done()
        cleanup_time = time.time() - start_time
        
        # Cleanup should be fast
        assert cleanup_time < 2.0, f"Integration cleanup took {cleanup_time:.2f}s, expected < 2.0s"
        
        # Verify proper cleanup
        assert config_entry.entry_id not in hass.data.get(DOMAIN, {})