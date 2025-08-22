# Arcam AVR User Guide

Complete guide for setting up and using the Arcam AVR integration with Home Assistant.

## Table of Contents

1. [Overview](#overview)
2. [Supported Devices](#supported-devices)
3. [Installation](#installation)
4. [Initial Setup](#initial-setup)
5. [Configuration](#configuration)
6. [Using the Integration](#using-the-integration)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Features](#advanced-features)
9. [FAQ](#faq)

## Overview

The Arcam AVR integration allows you to control your Arcam audio/video receiver from Home Assistant. This integration provides:

- **Full Media Player Control**: Power, volume, mute, source selection
- **Multi-Zone Support**: Control multiple zones independently
- **Real-Time Updates**: Automatic status updates via device broadcasts
- **Service Integration**: Use with automations, scripts, and scenes
- **Device Discovery**: Automatic detection of devices on your network

## Supported Devices

This integration supports Arcam AVR receivers with network connectivity:

### Confirmed Compatible Models
- **AVR Series**: AVR11, AVR21, AVR31, AVR390, AVR550, AVR750, AVR850
- **AV Series**: AV40, AV41, AV42
- **SR Series**: SR250, SR650

### Requirements
- Network connection (Ethernet or Wi-Fi)
- Firmware supporting network control protocol
- TCP port 50000 accessible (default)

> **Note**: Older models may require firmware updates for network control support.

## Installation

### Option 1: Home Assistant Community Store (HACS)
1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the "+" button
4. Search for "Arcam AVR"
5. Click "Download"
6. Restart Home Assistant

### Option 2: Manual Installation
1. Download the integration files
2. Copy to `custom_components/arcam_avr/` in your Home Assistant config directory
3. Restart Home Assistant
4. The integration will appear in Settings → Devices & Services

### Option 3: UV Package Manager (Recommended for Development)
```bash
uv add arcam-control-home-assistant
uv sync
```

## Initial Setup

### Automatic Discovery
1. Go to **Settings** → **Devices & Services**
2. Look for "Discovered" section
3. If your Arcam AVR appears, click "Configure"
4. Follow the setup wizard

### Manual Setup
1. Go to **Settings** → **Devices & Services**
2. Click **"+ Add Integration"**
3. Search for **"Arcam AVR"**
4. Enter your device details:
   - **Host**: IP address of your AVR (e.g., 192.168.1.100)
   - **Port**: Communication port (default: 50000)
   - **Name**: Friendly name for the device
   - **Zones**: Select zones to configure

### Finding Your Device IP Address

#### Method 1: Router Admin Panel
1. Access your router's admin interface
2. Look for "Connected Devices" or "DHCP Clients"
3. Find your Arcam device by name or MAC address

#### Method 2: Device Menu
1. On your AVR, navigate to Network settings
2. Look for "Network Status" or "IP Configuration"
3. Note the displayed IP address

#### Method 3: Network Scanner
Use a network scanning app on your phone or computer to find devices on port 50000.

## Configuration

### Basic Configuration
After initial setup, configure these basic options:

#### Device Settings
- **Update Interval**: How often to check for status (30-300 seconds)
- **Zones**: Enable/disable specific zones
- **Fast Polling**: Use faster updates when device is on

#### Network Settings
- **Timeout**: Connection timeout in seconds
- **Retry Attempts**: Number of retry attempts for failed commands

### Zone Configuration

#### Single Zone Setup
Most users will use Zone 1 (main zone) only:
```yaml
# Example entity after setup
media_player.living_room_avr
```

#### Multi-Zone Setup
For multi-zone systems, each zone gets its own entity:
```yaml
# Zone 1 (main)
media_player.living_room_avr

# Zone 2 (additional)
media_player.living_room_avr_zone_2
```

### Options Configuration
To modify options after setup:

1. Go to **Settings** → **Devices & Services**
2. Find your Arcam AVR integration
3. Click **"Configure"**
4. Adjust settings as needed
5. Click **"Submit"**

## Using the Integration

### Basic Controls

#### Power Control
```yaml
# Turn on
service: media_player.turn_on
target:
  entity_id: media_player.living_room_avr

# Turn off
service: media_player.turn_off
target:
  entity_id: media_player.living_room_avr
```

#### Volume Control
```yaml
# Set volume to 50%
service: media_player.volume_set
target:
  entity_id: media_player.living_room_avr
data:
  volume_level: 0.5

# Mute/unmute
service: media_player.volume_mute
target:
  entity_id: media_player.living_room_avr
data:
  is_volume_muted: true
```

#### Source Selection
```yaml
# Select Blu-ray input
service: media_player.select_source
target:
  entity_id: media_player.living_room_avr
data:
  source: "Blu-ray Player"
```

### Available Sources
The integration maps device sources to friendly names:

| Device Code | Friendly Name | Description |
|-------------|---------------|-------------|
| BD | Blu-ray Player | Blu-ray/UHD input |
| CD | CD Player | CD player input |
| DVD | DVD Player | DVD player input |
| SAT | Satellite/Cable | Satellite or cable box |
| PVR | PVR/DVR | Personal video recorder |
| VCR | VCR | VCR or legacy video |
| TAPE | Tape Deck | Cassette or tape deck |
| TUNER | AM/FM Tuner | Built-in radio tuner |
| PHONO | Phono/Turntable | Turntable input |
| AUX | Auxiliary Input | Generic auxiliary input |
| NET | Network/Streaming | Network streaming |
| USB | USB Input | USB media input |

### Automation Examples

#### Morning Routine
```yaml
automation:
  - alias: "Morning Audio"
    trigger:
      platform: time
      at: "07:00:00"
    action:
      - service: media_player.turn_on
        target:
          entity_id: media_player.living_room_avr
      - delay: "00:00:02"
      - service: media_player.select_source
        target:
          entity_id: media_player.living_room_avr
        data:
          source: "AM/FM Tuner"
      - service: media_player.volume_set
        target:
          entity_id: media_player.living_room_avr
        data:
          volume_level: 0.3
```

#### Movie Night Scene
```yaml
scene:
  - name: "Movie Night"
    entities:
      media_player.living_room_avr:
        state: "on"
        source: "Blu-ray Player"
        volume_level: 0.7
        is_volume_muted: false
      light.living_room:
        state: "off"
```

#### Volume Automation
```yaml
automation:
  - alias: "Auto Volume Control"
    trigger:
      platform: state
      entity_id: media_player.living_room_avr
      attribute: source
      to: "Blu-ray Player"
    action:
      - service: media_player.volume_set
        target:
          entity_id: media_player.living_room_avr
        data:
          volume_level: 0.6
```

### Lovelace UI Integration

#### Media Player Card
```yaml
type: media-control
entity: media_player.living_room_avr
```

#### Custom Card with Source Buttons
```yaml
type: vertical-stack
cards:
  - type: media-control
    entity: media_player.living_room_avr
  - type: horizontal-stack
    cards:
      - type: button
        tap_action:
          action: call-service
          service: media_player.select_source
          service_data:
            entity_id: media_player.living_room_avr
            source: "Blu-ray Player"
        name: "Blu-ray"
      - type: button
        tap_action:
          action: call-service
          service: media_player.select_source
          service_data:
            entity_id: media_player.living_room_avr
            source: "CD Player"
        name: "CD"
```

## Troubleshooting

### Common Issues

#### Cannot Connect to Device
**Symptoms**: Setup fails with "Cannot connect" error

**Solutions**:
1. **Check IP Address**: Verify the IP address is correct
2. **Network Connectivity**: Ensure Home Assistant can reach the device
3. **Device Power**: Make sure the AVR is powered on
4. **Port Access**: Verify port 50000 is not blocked
5. **Firmware**: Update AVR firmware if needed

#### Device Shows as Unavailable
**Symptoms**: Entity shows "unavailable" state

**Solutions**:
1. **Network Issues**: Check network connection
2. **Device Standby**: Some models disconnect in standby mode
3. **Restart Integration**: Reload the integration
4. **Check Logs**: Look for error messages in Home Assistant logs

#### Commands Not Working
**Symptoms**: Services don't control the device

**Solutions**:
1. **Device State**: Ensure device is responsive
2. **Zone Configuration**: Verify correct zone is targeted
3. **Source Mapping**: Check if source names are correct
4. **Rate Limiting**: Avoid sending commands too rapidly

#### Slow Updates
**Symptoms**: Status updates are delayed

**Solutions**:
1. **Update Interval**: Reduce update interval in options
2. **Fast Polling**: Enable fast polling when device is on
3. **Network Performance**: Check network latency
4. **Device Load**: Reduce other network traffic to device

### Debug Information

#### Enable Debug Logging
Add to `configuration.yaml`:
```yaml
logger:
  default: warning
  logs:
    custom_components.arcam_avr: debug
    homeassistant.components.arcam_avr: debug
```

#### Check Device Status
Use Developer Tools → States to check entity states and attributes:
- `media_player.your_avr_name`
- Look for `state`, `volume_level`, `source`, `is_volume_muted`

#### Network Testing
Test connectivity from Home Assistant host:
```bash
# Test TCP connection
telnet 192.168.1.100 50000

# Test ping
ping 192.168.1.100
```

### Log Analysis

#### Common Log Messages
- `Connected to Arcam AVR`: Successful connection
- `Connection timeout`: Network/device issue
- `Command failed`: Device rejected command
- `Protocol error`: Communication issue

#### Getting Help
When reporting issues, include:
1. Home Assistant version
2. Integration version
3. Device model and firmware version
4. Relevant log entries
5. Network configuration details

## Advanced Features

### Multi-Zone Control
For systems with multiple zones:

```yaml
# Control Zone 2 independently
service: media_player.volume_set
target:
  entity_id: media_player.living_room_avr_zone_2
data:
  volume_level: 0.3
```

### Custom Services
The integration provides additional services:

#### Send Raw Command
```yaml
service: arcam_avr.send_command
target:
  entity_id: media_player.living_room_avr
data:
  command: "0x01"  # Hexadecimal command code
  data: 1          # Optional data parameter
  zone: 1          # Target zone
```

### Integration with Other Systems

#### Voice Control (Google Assistant/Alexa)
Expose the media player entity to your voice assistant for voice control:
- "Turn on the receiver"
- "Set receiver volume to 50%"
- "Switch receiver to Blu-ray"

#### Node-RED Integration
Use Node-RED to create complex automation flows with the media player entity.

#### MQTT Integration
Bridge status to MQTT for integration with other home automation systems.

## FAQ

### General Questions

**Q: Which Arcam models are supported?**
A: Most modern Arcam AVR receivers with network connectivity. See the [Supported Devices](#supported-devices) section for specific models.

**Q: Can I control multiple zones?**
A: Yes, multi-zone systems create separate entities for each configured zone.

**Q: Does this work with older Arcam models?**
A: Only models with network control support. Older models may need firmware updates.

### Setup Questions

**Q: Why can't Home Assistant find my AVR automatically?**
A: Discovery requires the device to be on the same network segment. Try manual setup with the IP address.

**Q: What if my AVR uses a different port?**
A: You can specify a custom port during setup. Standard port is 50000.

**Q: Can I change the device name after setup?**
A: Yes, go to Settings → Devices & Services → Your AVR → Configure.

### Usage Questions

**Q: Why do volume changes seem slow?**
A: The integration respects device rate limits. Very rapid changes may be queued.

**Q: Can I see what's currently playing?**
A: This integration focuses on receiver control. For media info, integrate your source devices.

**Q: Why does the device show as unavailable sometimes?**
A: Some models disconnect when in standby. This is normal behavior.

### Technical Questions

**Q: Is this integration secure?**
A: Communication uses the device's built-in protocol over your local network.

**Q: How much network traffic does this generate?**
A: Minimal - only status polls and commands. Typically less than 1KB per minute.

**Q: Can I use this with Home Assistant OS?**
A: Yes, this integration works with all Home Assistant installation types.

---

## Support

For additional support:
- Check the [GitHub Issues](https://github.com/your-repo/arcam-control-home-assistant/issues)
- Visit the [Home Assistant Community Forum](https://community.home-assistant.io/)
- Review the [Technical Documentation](./technical_guide.md)

## Contributing

We welcome contributions! See the [Development Guide](./development_guide.md) for details on:
- Setting up development environment
- Running tests
- Submitting pull requests
- Reporting bugs

---

*Last updated: [Current Date]*