"""Arcam AVR protocol implementation."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .exceptions import ArcamProtocolError

_LOGGER = logging.getLogger(__name__)

# Protocol constants
START_BYTE = 0x21  # '!'
END_BYTE = 0x0D    # '\r'

# Answer codes
ANSWER_OK = 0x00
ANSWER_ZONE_INVALID = 0x82
ANSWER_COMMAND_NOT_RECOGNIZED = 0x83
ANSWER_PARAMETER_NOT_RECOGNIZED = 0x84
ANSWER_COMMAND_INVALID_AT_THIS_TIME = 0x85
ANSWER_INVALID_DATA_LENGTH = 0x86


@dataclass
class ArcamCommand:
    """Represents an Arcam command."""
    
    zone: int
    command_code: int
    data: bytes = b""
    
    def __post_init__(self) -> None:
        """Validate command parameters."""
        if not 1 <= self.zone <= 2:
            raise ArcamProtocolError(f"Invalid zone: {self.zone}")
        if not 0 <= self.command_code <= 255:
            raise ArcamProtocolError(f"Invalid command code: {self.command_code}")
        if len(self.data) > 255:
            raise ArcamProtocolError(f"Data too long: {len(self.data)} bytes")


@dataclass
class ArcamResponse:
    """Represents an Arcam response."""
    
    zone: int
    command_code: int
    answer_code: int
    data: bytes
    
    @property
    def is_success(self) -> bool:
        """Check if response indicates success."""
        return self.answer_code == ANSWER_OK
    
    @property
    def error_message(self) -> str | None:
        """Get error message for non-success responses."""
        error_messages = {
            ANSWER_ZONE_INVALID: "Invalid zone specified",
            ANSWER_COMMAND_NOT_RECOGNIZED: "Command not recognized",
            ANSWER_PARAMETER_NOT_RECOGNIZED: "Parameter not recognized",
            ANSWER_COMMAND_INVALID_AT_THIS_TIME: "Command invalid at this time",
            ANSWER_INVALID_DATA_LENGTH: "Invalid data length",
        }
        return error_messages.get(self.answer_code)


class ArcamProtocol:
    """Implements Arcam binary protocol."""
    
    @staticmethod
    def encode_command(command: ArcamCommand) -> bytes:
        """Encode command to binary format.
        
        Format: <St> <Zn> <Cc> <Dl> <Data...> <Et>
        """
        data_length = len(command.data)
        
        # Build command bytes
        command_bytes = bytearray([
            START_BYTE,
            command.zone,
            command.command_code,
            data_length,
        ])
        
        # Add data if present
        if command.data:
            command_bytes.extend(command.data)
            
        # Add end byte
        command_bytes.append(END_BYTE)
        
        _LOGGER.debug(
            "Encoded command: zone=%d, code=0x%02X, data=%s -> %s",
            command.zone,
            command.command_code,
            command.data.hex() if command.data else "none",
            command_bytes.hex(),
        )
        
        return bytes(command_bytes)
    
    @staticmethod
    def decode_response(data: bytes) -> ArcamResponse:
        """Decode binary response.
        
        Format: <St> <Zn> <Cc> <Ac> <Dl> <Data...> <Et>
        """
        if len(data) < 6:
            raise ArcamProtocolError(f"Response too short: {len(data)} bytes")
            
        if data[0] != START_BYTE:
            raise ArcamProtocolError(f"Invalid start byte: 0x{data[0]:02X}")
            
        if data[-1] != END_BYTE:
            raise ArcamProtocolError(f"Invalid end byte: 0x{data[-1]:02X}")
            
        zone = data[1]
        command_code = data[2]
        answer_code = data[3]
        data_length = data[4]
        
        # Validate data length
        expected_length = 6 + data_length  # 5 header bytes + data + 1 end byte
        if len(data) != expected_length:
            raise ArcamProtocolError(
                f"Data length mismatch: expected {expected_length}, got {len(data)}"
            )
            
        # Extract response data
        response_data = data[5:5 + data_length] if data_length > 0 else b""
        
        response = ArcamResponse(
            zone=zone,
            command_code=command_code,
            answer_code=answer_code,
            data=response_data,
        )
        
        _LOGGER.debug(
            "Decoded response: zone=%d, code=0x%02X, answer=0x%02X, data=%s",
            response.zone,
            response.command_code,
            response.answer_code,
            response.data.hex() if response.data else "none",
        )
        
        return response
    
    @staticmethod
    def validate_response(response: ArcamResponse, expected_command: int) -> bool:
        """Validate response matches expected command."""
        if response.command_code != expected_command:
            _LOGGER.warning(
                "Command code mismatch: expected 0x%02X, got 0x%02X",
                expected_command,
                response.command_code,
            )
            return False
            
        return True
    
    @staticmethod
    def create_status_request(zone: int, command_code: int) -> ArcamCommand:
        """Create a status request command."""
        return ArcamCommand(
            zone=zone,
            command_code=command_code,
            data=bytes([0xF0]),  # Status request parameter
        )