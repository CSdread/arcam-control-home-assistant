# Arcam AVR Troubleshooting Guide

Comprehensive troubleshooting guide for the Arcam AVR Home Assistant integration.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Common Issues](#common-issues)
3. [Setup Problems](#setup-problems)
4. [Connection Issues](#connection-issues)
5. [Control Problems](#control-problems)
6. [Performance Issues](#performance-issues)
7. [Advanced Troubleshooting](#advanced-troubleshooting)
8. [Getting Help](#getting-help)

## Quick Diagnostics

### Health Check Steps
Run through this checklist first:

1. **Device Status**: Is your Arcam AVR powered on and responsive?
2. **Network**: Can you ping the device from Home Assistant host?
3. **Integration Status**: Is the integration loaded without errors?
4. **Entity State**: Check entity state in Developer Tools → States
5. **Logs**: Review Home Assistant logs for error messages

### Basic Network Test
```bash
# From Home Assistant host, test connectivity
ping 192.168.1.100              # Replace with your device IP
telnet 192.168.1.100 50000      # Test TCP port access
```

### Entity Inspection
Go to **Developer Tools** → **States** and find your Arcam AVR entity:
- Check `state` (should be `on`, `off`, or `unavailable`)
- Review `attributes` for device info and current settings
- Note any error states or missing attributes

## Common Issues

### Integration Won't Load

#### Symptoms
- Integration not visible in Settings → Devices & Services
- Error messages during Home Assistant startup
- Import errors in logs

#### Solutions

**1. Check Installation**
```bash
# Verify files are in correct location
ls -la /config/custom_components/arcam_avr/

# Check manifest.json exists and is valid
cat /config/custom_components/arcam_avr/manifest.json
```

**2. Restart Home Assistant**
```bash
# Restart to reload custom components
# Use your preferred restart method
```

**3. Check Logs**
Look for import or initialization errors:
```
2024-01-01 12:00:00 ERROR (MainThread) [homeassistant.loader] 
Error loading custom_components.arcam_avr
```

**4. Verify Dependencies**
Ensure all required Python packages are available in your environment.

### Device Not Discovered

#### Symptoms
- Device doesn't appear in discovered integrations
- Manual setup required even with compatible device

#### Solutions

**1. Network Segmentation**
- Ensure Home Assistant and AVR are on same network segment
- Check VLAN configuration if applicable
- Verify multicast/broadcast traffic is allowed

**2. Device Settings**
- Enable network control on the AVR
- Check if device is in standby (some models disable network in deep standby)
- Verify network settings on device

**3. Manual Setup**
Use manual configuration if discovery fails:
1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Arcam AVR"
4. Enter device details manually

### Entity Shows as Unavailable

#### Symptoms
- Entity state shows "unavailable"
- Cannot control device through Home Assistant
- No response to commands

#### Solutions

**1. Device Power State**
- Some models disconnect from network when in standby
- Try turning device on manually first
- Check if device supports network wake-up

**2. Network Connectivity**
```bash
# Test basic connectivity
ping 192.168.1.100

# Test port access
nc -v 192.168.1.100 50000

# Check for firewall issues
telnet 192.168.1.100 50000
```

**3. Integration Restart**
1. Go to Settings → Devices & Services
2. Find Arcam AVR integration
3. Click "..." → "Reload"

**4. Check Update Interval**
- Very long update intervals may cause temporary unavailable states
- Consider reducing update interval in integration options

## Setup Problems

### Cannot Connect During Setup

#### Error Messages
- "Failed to connect to the Arcam AVR"
- "Connection timed out"
- "Cannot connect to device"

#### Solutions

**1. Verify IP Address**
- Double-check device IP address
- Use device menu or router admin to confirm IP
- Try connecting from another device on same network

**2. Port Configuration**
- Default port is 50000
- Some models may use different ports
- Check device manual for correct port

**3. Device Configuration**
- Enable network control in device settings
- Check if authentication is required
- Verify network settings are correct

**4. Network Issues**
- Test connectivity with ping and telnet
- Check for firewall blocking port 50000
- Verify no VPN interference

### Invalid Host Format Error

#### Symptoms
- "Invalid host IP address format" during setup
- Setup form validation fails

#### Solutions

**1. IP Address Format**
- Use IPv4 format: `192.168.1.100`
- Don't include `http://` or other prefixes
- Don't include port number in host field

**2. Valid Examples**
```
✓ 192.168.1.100
✓ 10.0.0.50
✓ 172.16.1.200

✗ http://192.168.1.100
✗ 192.168.1.100:50000
✗ arcam-avr.local (use IP address)
```

### Already Configured Error

#### Symptoms
- "This device is already configured"
- Cannot add second instance of same device

#### Solutions

**1. Check Existing Integrations**
1. Go to Settings → Devices & Services
2. Look for existing Arcam AVR integrations
3. Remove duplicate if found

**2. Different Configuration**
- Use different name or port if legitimately different device
- Check if multiple zones are already configured

## Connection Issues

### Intermittent Disconnections

#### Symptoms
- Entity occasionally shows unavailable
- Commands sometimes fail
- Logs show connection errors

#### Solutions

**1. Network Stability**
- Check network equipment (router, switches)
- Test with wired connection if using Wi-Fi
- Monitor for network interference

**2. Device Firmware**
- Update AVR firmware to latest version
- Check release notes for network improvements
- Contact Arcam support for known issues

**3. Integration Settings**
- Increase timeout values
- Adjust update interval
- Enable retry mechanisms

**4. Power Management**
- Disable network power saving on device
- Check router power saving settings
- Consider UPS for network equipment

### Slow Response Times

#### Symptoms
- Commands take long time to execute
- UI updates are delayed
- Timeout errors in logs

#### Solutions

**1. Network Performance**
```bash
# Test network latency
ping -c 10 192.168.1.100

# Check network bandwidth
iperf3 -c 192.168.1.100  # If device supports it
```

**2. Device Load**
- Reduce other network traffic to device
- Check if other integrations are accessing device
- Avoid rapid command sequences

**3. Integration Tuning**
- Adjust timeout settings
- Optimize update intervals
- Enable fast polling only when needed

### Port Access Issues

#### Symptoms
- "Connection refused" errors
- Cannot telnet to port 50000
- Setup fails immediately

#### Solutions

**1. Device Configuration**
- Verify network control is enabled
- Check device is not in deep sleep mode
- Restart device to reset network stack

**2. Firewall/Security**
```bash
# Check if port is listening
nmap -p 50000 192.168.1.100

# Test from different source
telnet 192.168.1.100 50000
```

**3. Network Equipment**
- Check router/switch port blocking
- Verify VLAN configuration
- Test with device on same subnet

## Control Problems

### Commands Not Working

#### Symptoms
- Services execute without error but device doesn't respond
- Some commands work, others don't
- Inconsistent behavior

#### Solutions

**1. Device State**
- Ensure device is powered on and responsive
- Test commands manually with device remote
- Check if device is in correct mode/input

**2. Command Validation**
- Verify source names match available options
- Check volume levels are within valid range (0-99 or 0.0-1.0)
- Ensure zone numbers are correct (1-4)

**3. Rate Limiting**
```python
# Avoid rapid command sequences
await hass.services.async_call("media_player", "turn_on", {"entity_id": entity_id})
await asyncio.sleep(1)  # Wait between commands
await hass.services.async_call("media_player", "volume_set", {"entity_id": entity_id, "volume_level": 0.5})
```

**4. Debug Logging**
Enable debug logging to see command details:
```yaml
# configuration.yaml
logger:
  logs:
    homeassistant.components.arcam_avr: debug
```

### Source Selection Issues

#### Symptoms
- Cannot select certain sources
- Source names don't match device
- Invalid source errors

#### Solutions

**1. Source Mapping**
Check available sources in entity attributes:
```yaml
# Example entity attributes
source_list:
  - "Blu-ray Player"
  - "CD Player"
  - "DVD Player"
  # ... etc
```

**2. Use Correct Names**
```yaml
# Use friendly names from source_list
- service: media_player.select_source
  data:
    entity_id: media_player.arcam_avr
    source: "Blu-ray Player"  # Not "BD" or "Bluray"
```

**3. Device-Specific Sources**
- Some sources may not be available on all models
- Check device manual for supported inputs
- Use device code if friendly name fails

### Volume Control Problems

#### Symptoms
- Volume changes don't take effect
- Volume level incorrect in UI
- Mute state inconsistent

#### Solutions

**1. Volume Scale**
Home Assistant uses 0.0-1.0, device uses 0-99:
```yaml
# Set to 50% (device volume ~50)
- service: media_player.volume_set
  data:
    entity_id: media_player.arcam_avr
    volume_level: 0.5
```

**2. Mute State**
Check current mute state before changing:
```yaml
# Check attributes
is_volume_muted: true/false
```

**3. Zone-Specific Volume**
For multi-zone systems, ensure targeting correct zone:
```yaml
# Zone 2 volume control
- service: media_player.volume_set
  target:
    entity_id: media_player.arcam_avr_zone_2
  data:
    volume_level: 0.3
```

## Performance Issues

### Slow Updates

#### Symptoms
- Entity state updates slowly
- Changes not reflected in UI immediately
- Long delay between command and state change

#### Solutions

**1. Update Interval**
Reduce update interval in integration options:
1. Settings → Devices & Services → Arcam AVR
2. Configure → Update Interval
3. Set to 30-60 seconds for faster updates

**2. Fast Polling**
Enable fast polling when device is on:
1. Integration options → Fast Polling When On
2. This uses shorter intervals when device is active

**3. Broadcast Messages**
Ensure device broadcast messages are working:
- Check logs for broadcast message reception
- Broadcasts provide immediate updates without polling

### High Resource Usage

#### Symptoms
- High CPU usage from integration
- Memory usage growing over time
- Home Assistant performance impact

#### Solutions

**1. Polling Optimization**
- Increase update interval to reduce polling frequency
- Disable fast polling if not needed
- Monitor resource usage with different settings

**2. Connection Management**
- Check for connection leaks in logs
- Restart integration if memory usage grows
- Update to latest integration version

**3. Network Efficiency**
- Reduce number of simultaneous connections
- Optimize command queuing
- Monitor network traffic patterns

### Memory Leaks

#### Symptoms
- Integration memory usage grows over time
- Home Assistant becomes slow after extended operation
- Eventually requires restart

#### Solutions

**1. Integration Restart**
Regularly restart the integration:
1. Settings → Devices & Services → Arcam AVR
2. Click "..." → "Reload"

**2. Connection Cleanup**
Check logs for connection management issues:
```
# Look for these patterns
Connection not properly closed
Callback not removed
Resource cleanup failed
```

**3. Update Integration**
- Update to latest version
- Check release notes for memory leak fixes
- Report issue if problem persists

## Advanced Troubleshooting

### Debug Logging

Enable comprehensive debug logging:

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    homeassistant.components.arcam_avr: debug
    homeassistant.components.arcam_avr.arcam.protocol: debug
    homeassistant.components.arcam_avr.arcam.connection: debug
    homeassistant.components.arcam_avr.coordinator: debug
    homeassistant.components.arcam_avr.media_player: debug
```

### Protocol Analysis

Monitor raw protocol communication:

```python
# Enable protocol debugging
import logging
logging.getLogger('homeassistant.components.arcam_avr.arcam.protocol').setLevel(logging.DEBUG)
```

Look for these log patterns:
```
Sending command: 02 01 01 01 03 03
Received response: 02 01 01 01 03 03
Broadcast message: 02 01 00 01 02 03
```

### Network Monitoring

Use network tools to monitor communication:

```bash
# Monitor all traffic to device
tcpdump -i any host 192.168.1.100

# Monitor specific port
tcpdump -i any host 192.168.1.100 and port 50000

# Save capture for analysis
tcpdump -i any host 192.168.1.100 -w arcam.pcap
```

### Performance Profiling

Monitor integration performance:

```python
# Add timing measurements
import time

start_time = time.time()
# ... operation ...
duration = time.time() - start_time
_LOGGER.debug("Operation took %.2f seconds", duration)
```

### Database Analysis

Check Home Assistant database for issues:

```sql
-- Check entity state history
SELECT * FROM states WHERE entity_id = 'media_player.arcam_avr' 
ORDER BY last_changed DESC LIMIT 100;

-- Check for rapid state changes
SELECT COUNT(*), DATE(last_changed) FROM states 
WHERE entity_id = 'media_player.arcam_avr' 
GROUP BY DATE(last_changed);
```

## Getting Help

### Before Asking for Help

Gather this information:
1. **Versions**:
   - Home Assistant version
   - Integration version
   - Device model and firmware

2. **Configuration**:
   - Integration setup details
   - Network configuration
   - Any custom settings

3. **Logs**:
   - Relevant error messages
   - Debug logs if possible
   - Timeline of when issues occur

4. **Testing**:
   - Basic network connectivity tests
   - What troubleshooting steps you've tried
   - Whether issue is consistent or intermittent

### Log Collection

```bash
# Collect relevant logs
grep -A 5 -B 5 "arcam_avr" /config/home-assistant.log > arcam_debug.log

# Include system information
uname -a >> arcam_debug.log
python3 --version >> arcam_debug.log
```

### Support Channels

1. **GitHub Issues**:
   - Bug reports: [GitHub Issues](https://github.com/your-repo/arcam-control-home-assistant/issues)
   - Feature requests: Use issue templates
   - Include all diagnostic information

2. **Community Forum**:
   - General questions: [Home Assistant Community](https://community.home-assistant.io/)
   - Search existing topics first
   - Use appropriate tags

3. **Documentation**:
   - Check [User Guide](./user_guide.md) for usage questions
   - Review [Technical Guide](./technical_guide.md) for implementation details
   - See [Development Guide](./development_guide.md) for contribution info

### Issue Templates

When reporting bugs, include:

```markdown
## Environment
- Home Assistant version: X.X.X
- Integration version: X.X.X
- Device model: Arcam AVRXX
- Firmware version: X.XX

## Problem Description
[Describe the issue]

## Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Logs
```yaml
[Paste relevant logs here]
```

## Additional Context
[Any other relevant information]
```

### Feature Requests

For feature requests, include:
- Use case description
- Expected behavior
- Alternatives considered
- Implementation suggestions (if any)

---

## Quick Reference

### Common Commands
```bash
# Test connectivity
ping 192.168.1.100
telnet 192.168.1.100 50000

# Check entity state
# Go to Developer Tools → States → media_player.arcam_avr

# Restart integration
# Settings → Devices & Services → Arcam AVR → ... → Reload

# View logs
tail -f /config/home-assistant.log | grep arcam_avr
```

### Useful Log Patterns
```
# Successful connection
Connected to Arcam AVR at 192.168.1.100:50000

# Command execution
Sending command to zone 1: power_on
Command completed successfully

# Broadcast received
Received broadcast: power state changed to on

# Connection issues
Connection timeout after 5.0 seconds
Failed to connect: Connection refused
```

---

*This troubleshooting guide is updated regularly based on user feedback and common issues. Please check for the latest version when encountering problems.*