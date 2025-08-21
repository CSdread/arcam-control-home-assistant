# Arcam AVR Integration Test Suite

This directory contains comprehensive tests for the Arcam AVR Home Assistant integration.

## Test Categories

### Unit Tests
- `test_init.py` - Integration initialization and lifecycle
- `test_media_player.py` - Media player entity functionality
- `test_coordinator.py` - Data update coordinator
- `test_config_flow.py` - Configuration flow
- `arcam/test_*.py` - Protocol library tests

### Integration Tests
- `test_integration.py` - Full integration lifecycle testing
- `test_device_communication.py` - Device communication scenarios
- `test_performance.py` - Performance and load testing

### Test Utilities
- `fixtures/` - Shared test fixtures
- `test_config.py` - Test configuration and utilities
- `run_integration_tests.py` - Test runner script

## Running Tests

### Quick Test Run
```bash
# Run all tests
python -m pytest tests/components/arcam_avr/

# Run fast tests only (exclude performance tests)
python tests/components/arcam_avr/run_integration_tests.py --fast

# Run with verbose output
python -m pytest tests/components/arcam_avr/ -v
```

### Performance Testing
```bash
# Run performance tests only
python tests/components/arcam_avr/run_integration_tests.py --performance

# Run with coverage
python tests/components/arcam_avr/run_integration_tests.py --coverage
```

### Parallel Testing
```bash
# Run tests in parallel (requires pytest-xdist)
python tests/components/arcam_avr/run_integration_tests.py --parallel 4
```

## Test Coverage

The test suite provides comprehensive coverage of:

### Protocol Layer
- ✅ Binary protocol encoding/decoding
- ✅ Command construction and validation
- ✅ Response parsing and error handling
- ✅ Connection management and reconnection
- ✅ Broadcast message handling

### Integration Layer
- ✅ Configuration flow (setup, discovery, import)
- ✅ Data coordinator (polling, state management)
- ✅ Media player entity (all features)
- ✅ Device registry integration
- ✅ Service call handling

### Error Scenarios
- ✅ Connection failures and recovery
- ✅ Protocol errors and malformed responses
- ✅ Device disconnection and reconnection
- ✅ Command timeouts and retries
- ✅ Invalid configuration handling

### Performance Testing
- ✅ Startup and shutdown performance
- ✅ Memory usage and leak detection
- ✅ Concurrent command handling
- ✅ Rapid state update processing
- ✅ Error recovery performance

## Test Fixtures

### MockArcamDevice
Comprehensive mock device that simulates:
- Real device response timing
- State persistence across commands
- Broadcast message generation
- Connection management
- Error injection

### Test Data Generators
- Device state variations
- Command sequences
- Error scenarios
- Performance test data

## Test Markers

- `@pytest.mark.slow` - Performance and load tests
- `@pytest.mark.integration` - Full integration tests
- `@pytest.mark.performance` - Performance-specific tests
- `@pytest.mark.hardware` - Tests requiring real hardware

## Coverage Goals

- **Overall Coverage**: 90%+
- **Protocol Layer**: 95%+
- **Integration Layer**: 90%+
- **Error Handling**: 85%+

## Mock Strategy

The test suite uses a layered mocking approach:

1. **Protocol Level**: Mock TCP connections and device responses
2. **Integration Level**: Mock Home Assistant components as needed
3. **Hardware Simulation**: MockArcamDevice provides realistic behavior

This ensures tests are:
- Fast and reliable (no network dependencies)
- Comprehensive (all code paths covered)
- Realistic (behavior matches real devices)

## Continuous Integration

Tests are designed to run in CI environments:
- No external dependencies
- Consistent timing (mocked delays)
- Parallel execution support
- Clear pass/fail criteria

## Performance Benchmarks

Expected performance characteristics:
- Integration startup: < 3 seconds
- Command execution: < 1 second
- State updates: < 0.5 seconds
- Memory growth: < 10MB over 100 operations
- Error recovery: < 2 seconds

## Test Data

Test configurations include:
- Single and multi-zone setups
- Various device models and versions
- Different network conditions
- Error and edge cases
- Performance stress scenarios

## Debugging Tests

For debugging failed tests:

```bash
# Run with maximum verbosity
python -m pytest tests/components/arcam_avr/ -vvv --tb=long

# Run specific test with debugging
python -m pytest tests/components/arcam_avr/test_integration.py::test_full_integration_lifecycle -vvv --pdb

# Run with logging enabled
python -m pytest tests/components/arcam_avr/ --log-cli-level=DEBUG
```

## Adding New Tests

When adding new tests:

1. Follow the existing naming convention
2. Use appropriate fixtures from `test_config.py`
3. Add markers for categorization
4. Include docstrings explaining test purpose
5. Test both success and failure scenarios
6. Consider performance implications

## Test Dependencies

Required packages for testing:
- `pytest` - Test framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `pytest-xdist` - Parallel execution
- `psutil` - Performance monitoring (optional)

Install test dependencies:
```bash
pip install pytest pytest-asyncio pytest-cov pytest-xdist psutil
```

## Integration with Home Assistant Testing

These tests integrate with Home Assistant's testing framework:
- Use `tests.common.MockConfigEntry`
- Follow HA testing patterns
- Compatible with HA test runners
- Proper async handling

## Future Enhancements

Planned test improvements:
- Hardware-in-the-loop testing
- Fuzz testing for protocol robustness
- Load testing with multiple integrations
- Network condition simulation
- Real device compatibility testing