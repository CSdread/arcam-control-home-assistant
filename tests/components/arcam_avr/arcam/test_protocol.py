"""Test Arcam protocol implementation."""
import pytest

from homeassistant.components.arcam_avr.arcam.protocol import (
    ArcamProtocol,
    ArcamCommand,
    ArcamResponse,
    ANSWER_OK,
    ANSWER_ZONE_INVALID,
    ANSWER_COMMAND_NOT_RECOGNIZED,
)
from homeassistant.components.arcam_avr.arcam.exceptions import ArcamProtocolError


class TestArcamCommand:
    """Test ArcamCommand dataclass."""
    
    def test_valid_command(self):
        """Test valid command creation."""
        command = ArcamCommand(zone=1, command_code=0x00, data=bytes([0x01]))
        assert command.zone == 1
        assert command.command_code == 0x00
        assert command.data == bytes([0x01])
    
    def test_invalid_zone(self):
        """Test invalid zone raises exception."""
        with pytest.raises(ArcamProtocolError):
            ArcamCommand(zone=0, command_code=0x00)
        
        with pytest.raises(ArcamProtocolError):
            ArcamCommand(zone=3, command_code=0x00)
    
    def test_invalid_command_code(self):
        """Test invalid command code raises exception."""
        with pytest.raises(ArcamProtocolError):
            ArcamCommand(zone=1, command_code=-1)
        
        with pytest.raises(ArcamProtocolError):
            ArcamCommand(zone=1, command_code=256)
    
    def test_data_too_long(self):
        """Test data too long raises exception."""
        long_data = bytes([0x00] * 256)
        with pytest.raises(ArcamProtocolError):
            ArcamCommand(zone=1, command_code=0x00, data=long_data)


class TestArcamResponse:
    """Test ArcamResponse dataclass."""
    
    def test_successful_response(self):
        """Test successful response properties."""
        response = ArcamResponse(
            zone=1,
            command_code=0x00,
            answer_code=ANSWER_OK,
            data=bytes([0x01])
        )
        assert response.is_success is True
        assert response.error_message is None
    
    def test_error_response(self):
        """Test error response properties."""
        response = ArcamResponse(
            zone=1,
            command_code=0x00,
            answer_code=ANSWER_ZONE_INVALID,
            data=bytes()
        )
        assert response.is_success is False
        assert response.error_message == "Invalid zone specified"
    
    def test_unknown_error_response(self):
        """Test unknown error code."""
        response = ArcamResponse(
            zone=1,
            command_code=0x00,
            answer_code=0xFF,  # Unknown error
            data=bytes()
        )
        assert response.is_success is False
        assert response.error_message is None


class TestArcamProtocol:
    """Test protocol encoding and decoding."""
    
    def test_encode_power_on_command(self):
        """Test encoding power on command."""
        command = ArcamCommand(zone=1, command_code=0x00, data=bytes([0x01]))
        encoded = ArcamProtocol.encode_command(command)
        expected = bytes([0x21, 0x01, 0x00, 0x01, 0x01, 0x0D])
        assert encoded == expected
    
    def test_encode_no_data_command(self):
        """Test encoding command with no data."""
        command = ArcamCommand(zone=1, command_code=0x00)
        encoded = ArcamProtocol.encode_command(command)
        expected = bytes([0x21, 0x01, 0x00, 0x00, 0x0D])
        assert encoded == expected
    
    def test_encode_volume_command(self):
        """Test encoding volume command."""
        command = ArcamCommand(zone=1, command_code=0x0D, data=bytes([0x32]))
        encoded = ArcamProtocol.encode_command(command)
        expected = bytes([0x21, 0x01, 0x0D, 0x01, 0x32, 0x0D])
        assert encoded == expected
    
    def test_decode_power_response(self):
        """Test decoding power response."""
        data = bytes([0x21, 0x01, 0x00, 0x00, 0x01, 0x01, 0x0D])
        response = ArcamProtocol.decode_response(data)
        
        assert response.zone == 1
        assert response.command_code == 0x00
        assert response.answer_code == 0x00
        assert response.data == bytes([0x01])
    
    def test_decode_no_data_response(self):
        """Test decoding response with no data."""
        data = bytes([0x21, 0x01, 0x00, 0x00, 0x00, 0x0D])
        response = ArcamProtocol.decode_response(data)
        
        assert response.zone == 1
        assert response.command_code == 0x00
        assert response.answer_code == 0x00
        assert response.data == bytes()
    
    def test_decode_error_response(self):
        """Test decoding error response."""
        data = bytes([0x21, 0x01, 0x00, 0x82, 0x00, 0x0D])
        response = ArcamProtocol.decode_response(data)
        
        assert response.zone == 1
        assert response.command_code == 0x00
        assert response.answer_code == 0x82  # Zone invalid
        assert len(response.data) == 0
    
    def test_decode_invalid_start_byte(self):
        """Test decoding invalid start byte raises exception."""
        data = bytes([0x20, 0x01, 0x00, 0x00, 0x00, 0x0D])
        with pytest.raises(ArcamProtocolError, match="Invalid start byte"):
            ArcamProtocol.decode_response(data)
    
    def test_decode_invalid_end_byte(self):
        """Test decoding invalid end byte raises exception."""
        data = bytes([0x21, 0x01, 0x00, 0x00, 0x00, 0x0C])
        with pytest.raises(ArcamProtocolError, match="Invalid end byte"):
            ArcamProtocol.decode_response(data)
    
    def test_decode_too_short(self):
        """Test decoding too short data raises exception."""
        data = bytes([0x21, 0x01])
        with pytest.raises(ArcamProtocolError, match="Response too short"):
            ArcamProtocol.decode_response(data)
    
    def test_decode_length_mismatch(self):
        """Test decoding with length mismatch raises exception."""
        data = bytes([0x21, 0x01, 0x00, 0x00, 0x02, 0x01, 0x0D])  # Says 2 bytes, has 1
        with pytest.raises(ArcamProtocolError, match="Data length mismatch"):
            ArcamProtocol.decode_response(data)
    
    def test_validate_response_success(self):
        """Test response validation for matching command."""
        response = ArcamResponse(
            zone=1,
            command_code=0x00,
            answer_code=0x00,
            data=bytes([0x01])
        )
        assert ArcamProtocol.validate_response(response, 0x00) is True
    
    def test_validate_response_mismatch(self):
        """Test response validation for non-matching command."""
        response = ArcamResponse(
            zone=1,
            command_code=0x0D,
            answer_code=0x00,
            data=bytes([0x32])
        )
        assert ArcamProtocol.validate_response(response, 0x00) is False
    
    def test_create_status_request(self):
        """Test creating status request command."""
        command = ArcamProtocol.create_status_request(1, 0x00)
        assert command.zone == 1
        assert command.command_code == 0x00
        assert command.data == bytes([0xF0])