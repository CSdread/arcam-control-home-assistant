# Arcam AVR Protocol Specification

## Connection Details

### Network Configuration
- **Protocol**: TCP
- **Port**: 50000
- **Connection**: Persistent connection preferred
- **Timeout**: 3 seconds for command response
- **Encoding**: Binary protocol

### Device Setup Requirements
- IP control must be enabled on device
- Enable via OSD: General Setup → Control → On
- Alternative: Hold DIRECT button for 4 seconds until "RS232 CONTROL ON" displayed
- Device IP address configured in Network Settings menu

## Protocol Format

### Command Structure (Client → Device)
```
<St> <Zn> <Cc> <Dl> <Data...> <Et>
```

| Byte | Name | Value | Description |
|------|------|-------|-------------|
| St | Start transmission | 0x21 ('!') | Command start marker |
| Zn | Zone number | 0x01/0x02 | Zone 1 (master) or Zone 2 |
| Cc | Command code | 0x00-0xFF | Specific command identifier |
| Dl | Data length | 0x00-0xFF | Number of data bytes following |
| Data | Parameters | Variable | Command-specific data |
| Et | End transmission | 0x0D ('\r') | Command end marker |

### Response Structure (Device → Client)
```
<St> <Zn> <Cc> <Ac> <Dl> <Data...> <Et>
```

| Byte | Name | Value | Description |
|------|------|-------|-------------|
| St | Start transmission | 0x21 ('!') | Response start marker |
| Zn | Zone number | 0x01/0x02 | Zone responding |
| Cc | Command code | 0x00-0xFF | Echo of command |
| Ac | Answer code | 0x00-0xFF | Status/error code |
| Dl | Data length | 0x00-0xFF | Number of data bytes following |
| Data | Response data | Variable | Command-specific response |
| Et | End transmission | 0x0D ('\r') | Response end marker |

## Answer Codes

| Code | Name | Description |
|------|------|-------------|
| 0x00 | Status update | Command successful |
| 0x82 | Zone Invalid | Invalid zone specified |
| 0x83 | Command not recognised | Unknown command code |
| 0x84 | Parameter not recognised | Invalid parameter |
| 0x85 | Command invalid at this time | Command not allowed in current state |
| 0x86 | Invalid data length | Incorrect data length |

## Phase 1 Commands (Core Functionality)

### Power Control (0x00)

#### Turn On
```
Command:  21 01 00 01 01 0D
Response: 21 01 00 00 01 01 0D
```

#### Turn Off (Standby)
```
Command:  21 01 00 01 00 0D
Response: 21 01 00 00 01 00 0D
```

#### Request Power Status
```
Command:  21 01 00 01 F0 0D
Response: 21 01 00 00 01 XX 0D  (XX = 00 for standby, 01 for on)
```

### Volume Control (0x0D)

#### Set Volume
```
Command:  21 01 0D 01 XX 0D  (XX = 00-63 for volume 0-99)
Response: 21 01 0D 00 01 XX 0D
```

#### Request Current Volume
```
Command:  21 01 0D 01 F0 0D
Response: 21 01 0D 00 01 XX 0D  (XX = current volume)
```

### Mute Control (0x0E)

#### Request Mute Status
```
Command:  21 01 0E 01 F0 0D
Response: 21 01 0E 00 01 XX 0D  (XX = 00 for unmuted, 01 for muted)
```

#### Toggle Mute (via RC5 IR Command)
```
Command:  21 01 08 02 10 0D 0D  (RC5 command for mute)
Response: 21 01 08 00 02 10 0D 0D
```

### Source Selection (0x1D)

#### Request Current Source
```
Command:  21 01 1D 01 F0 0D
Response: 21 01 1D 00 01 XX 0D
```

Source codes:
- 0x00: CD
- 0x01: BD (Blu-ray)
- 0x02: AV
- 0x03: STB (Set-top box)
- 0x04: SAT (Satellite)
- 0x05: PVR
- 0x06: VCR
- 0x07: Aux
- 0x08: GAME
- 0x09: NET (Network)
- 0x0A: FM
- 0x0B: DAB
- 0x0C: BT (Bluetooth)
- 0x0D: USB
- 0x0E: UHD

#### Select Source (via RC5 IR Commands)
Use Simulate RC5 IR Command (0x08) with appropriate RC5 codes:

| Source | RC5 Code (Data1-Data2) |
|--------|------------------------|
| CD | 0x10 0x76 |
| BD | 0x10 0x62 |
| STB | 0x10 0x64 |
| Game | 0x10 0x61 |
| AV | 0x10 0x5E |
| SAT | 0x10 0x1B |
| PVR | 0x10 0x60 |
| Aux | 0x10 0x63 |
| NET | 0x10 0x5C |
| FM | 0x10 0x1C |
| DAB | 0x10 0x48 |
| BT | 0x10 0x7A |
| UHD | 0x10 0x7D |

### Simulate RC5 IR Command (0x08)
```
Command:  21 01 08 02 XX YY 0D  (XX YY = RC5 command bytes)
Response: 21 01 08 00 02 XX YY 0D
```

## Device Information Commands

### Software Version (0x04)
```
Command:  21 01 04 01 F0 0D
Response: 21 01 04 00 0C XX XX XX XX XX XX XX XX XX XX XX XX 0D
```
Response data contains 12 bytes of version information.

### Request Current Source Details (0x1D)
```
Command:  21 01 1D 01 F0 0D
Response: 21 01 1D 00 01 XX 0D  (XX = current source code)
```

## Status Broadcasting

The device may send unsolicited status updates when state changes occur due to:
- Front panel button presses
- IR remote control commands
- Other control interfaces

These broadcasts use the same format as command responses with answer code 0x00.

## Error Handling

### Connection Management
- Maintain persistent TCP connection
- Implement automatic reconnection on disconnect
- Handle connection timeouts gracefully
- Retry failed commands with exponential backoff

### Protocol Error Recovery
- Validate response format and checksums
- Handle unexpected responses
- Implement command queuing for reliability
- Log protocol errors for debugging

### Device State Synchronization
- Poll device status on reconnection
- Handle state changes from other sources
- Maintain local state cache for responsiveness
- Validate state consistency periodically

## Implementation Notes

### Command Timing
- Wait for response before sending next command
- Maximum 3-second timeout per command
- Allow command pipelining where supported
- Implement command prioritization (user commands first)

### Data Validation
- Validate all byte values before sending
- Check response length matches expected format
- Verify command echo in responses
- Handle partial or corrupted responses

### Model Compatibility
All commands listed are compatible with all supported models:
- AVR5, AVR10, AVR20, AVR30, AVR40
- AVR11, AVR21, AVR31, AVR41

Some advanced features may not be available on all models (noted in documentation).

## Testing Strategy

### Unit Test Requirements
- Mock TCP socket connections
- Test command encoding/decoding
- Validate error handling paths
- Test state synchronization logic

### Integration Test Requirements
- Real device communication validation
- Network error simulation
- Concurrent command handling
- Long-running stability tests