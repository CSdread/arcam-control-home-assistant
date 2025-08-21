"""Arcam AVR command definitions and factory methods."""
from __future__ import annotations

import logging
from typing import Any

from .protocol import ArcamCommand

_LOGGER = logging.getLogger(__name__)

# Command codes
POWER = 0x00
SOFTWARE_VERSION = 0x04
RC5_SIMULATE = 0x08
VOLUME = 0x0D
MUTE = 0x0E
SOURCE = 0x1D

# RC5 command mapping for source selection
RC5_SOURCES = {
    "CD": (0x10, 0x76),
    "BD": (0x10, 0x62),
    "AV": (0x10, 0x5E),
    "STB": (0x10, 0x64),
    "SAT": (0x10, 0x1B),
    "PVR": (0x10, 0x60),
    "VCR": (0x10, 0x63),  # Note: Same as Aux in some docs
    "AUX": (0x10, 0x63),
    "GAME": (0x10, 0x61),
    "NET": (0x10, 0x5C),
    "FM": (0x10, 0x1C),
    "DAB": (0x10, 0x48),
    "BT": (0x10, 0x7A),
    "USB": (0x10, 0x7B),  # Based on pattern
    "UHD": (0x10, 0x7D),
}

# RC5 code for mute toggle
RC5_MUTE = (0x10, 0x0D)

# Source codes (for source status responses)
SOURCE_CODES = {
    0x00: "CD",
    0x01: "BD",
    0x02: "AV", 
    0x03: "STB",
    0x04: "SAT",
    0x05: "PVR",
    0x06: "VCR",
    0x07: "AUX",
    0x08: "GAME",
    0x09: "NET",
    0x0A: "FM",
    0x0B: "DAB",
    0x0C: "BT",
    0x0D: "USB",
    0x0E: "UHD",
}

# Reverse mapping for source names to codes
SOURCE_NAME_TO_CODE = {v: k for k, v in SOURCE_CODES.items()}

# Status request parameter
STATUS_REQUEST = 0xF0


class ArcamCommands:
    """Factory methods for creating Arcam commands."""
    
    @staticmethod
    def power_on(zone: int = 1) -> ArcamCommand:
        """Create power on command."""
        if not 1 <= zone <= 2:
            raise ValueError(f"Invalid zone: {zone}")
        
        return ArcamCommand(
            zone=zone,
            command_code=POWER,
            data=bytes([0x01])
        )
    
    @staticmethod
    def power_off(zone: int = 1) -> ArcamCommand:
        """Create power off (standby) command."""
        if not 1 <= zone <= 2:
            raise ValueError(f"Invalid zone: {zone}")
            
        return ArcamCommand(
            zone=zone,
            command_code=POWER,
            data=bytes([0x00])
        )
    
    @staticmethod
    def get_power_status(zone: int = 1) -> ArcamCommand:
        """Create get power status command."""
        if not 1 <= zone <= 2:
            raise ValueError(f"Invalid zone: {zone}")
            
        return ArcamCommand(
            zone=zone,
            command_code=POWER,
            data=bytes([STATUS_REQUEST])
        )
    
    @staticmethod
    def set_volume(volume: int, zone: int = 1) -> ArcamCommand:
        """Create set volume command.
        
        Args:
            volume: Volume level (0-99)
            zone: Zone number (1 or 2)
        """
        if not 1 <= zone <= 2:
            raise ValueError(f"Invalid zone: {zone}")
        if not 0 <= volume <= 99:
            raise ValueError(f"Invalid volume: {volume} (must be 0-99)")
            
        return ArcamCommand(
            zone=zone,
            command_code=VOLUME,
            data=bytes([volume])
        )
    
    @staticmethod
    def get_volume(zone: int = 1) -> ArcamCommand:
        """Create get volume command."""
        if not 1 <= zone <= 2:
            raise ValueError(f"Invalid zone: {zone}")
            
        return ArcamCommand(
            zone=zone,
            command_code=VOLUME,
            data=bytes([STATUS_REQUEST])
        )
    
    @staticmethod
    def get_mute_status(zone: int = 1) -> ArcamCommand:
        """Create get mute status command."""
        if not 1 <= zone <= 2:
            raise ValueError(f"Invalid zone: {zone}")
            
        return ArcamCommand(
            zone=zone,
            command_code=MUTE,
            data=bytes([STATUS_REQUEST])
        )
    
    @staticmethod
    def toggle_mute(zone: int = 1) -> ArcamCommand:
        """Create toggle mute command via RC5 simulation."""
        if not 1 <= zone <= 2:
            raise ValueError(f"Invalid zone: {zone}")
            
        return ArcamCommand(
            zone=zone,
            command_code=RC5_SIMULATE,
            data=bytes(RC5_MUTE)
        )
    
    @staticmethod
    def get_source(zone: int = 1) -> ArcamCommand:
        """Create get source command."""
        if not 1 <= zone <= 2:
            raise ValueError(f"Invalid zone: {zone}")
            
        return ArcamCommand(
            zone=zone,
            command_code=SOURCE,
            data=bytes([STATUS_REQUEST])
        )
    
    @staticmethod
    def select_source(source: str, zone: int = 1) -> ArcamCommand:
        """Create select source command via RC5 simulation.
        
        Args:
            source: Source name (e.g., 'CD', 'BD', 'STB')
            zone: Zone number (1 or 2)
        """
        if not 1 <= zone <= 2:
            raise ValueError(f"Invalid zone: {zone}")
            
        source_upper = source.upper()
        if source_upper not in RC5_SOURCES:
            available_sources = ", ".join(sorted(RC5_SOURCES.keys()))
            raise ValueError(f"Invalid source: {source}. Available: {available_sources}")
            
        rc5_data = RC5_SOURCES[source_upper]
        return ArcamCommand(
            zone=zone,
            command_code=RC5_SIMULATE,
            data=bytes(rc5_data)
        )
    
    @staticmethod
    def get_software_version(zone: int = 1) -> ArcamCommand:
        """Create get software version command."""
        if not 1 <= zone <= 2:
            raise ValueError(f"Invalid zone: {zone}")
            
        return ArcamCommand(
            zone=zone,
            command_code=SOFTWARE_VERSION,
            data=bytes([STATUS_REQUEST])
        )
    
    @staticmethod
    def simulate_rc5(rc5_data1: int, rc5_data2: int, zone: int = 1) -> ArcamCommand:
        """Create generic RC5 simulation command.
        
        Args:
            rc5_data1: First RC5 data byte
            rc5_data2: Second RC5 data byte  
            zone: Zone number (1 or 2)
        """
        if not 1 <= zone <= 2:
            raise ValueError(f"Invalid zone: {zone}")
        if not 0 <= rc5_data1 <= 255:
            raise ValueError(f"Invalid RC5 data1: {rc5_data1}")
        if not 0 <= rc5_data2 <= 255:
            raise ValueError(f"Invalid RC5 data2: {rc5_data2}")
            
        return ArcamCommand(
            zone=zone,
            command_code=RC5_SIMULATE,
            data=bytes([rc5_data1, rc5_data2])
        )


def get_source_name(source_code: int) -> str | None:
    """Get source name from source code."""
    return SOURCE_CODES.get(source_code)


def get_source_code(source_name: str) -> int | None:
    """Get source code from source name."""
    return SOURCE_NAME_TO_CODE.get(source_name.upper())


def get_available_sources() -> list[str]:
    """Get list of available source names."""
    return sorted(RC5_SOURCES.keys())


def is_valid_source(source_name: str) -> bool:
    """Check if source name is valid."""
    return source_name.upper() in RC5_SOURCES


def decode_volume_response(data: bytes) -> int | None:
    """Decode volume from response data."""
    if len(data) != 1:
        _LOGGER.warning("Invalid volume response data length: %d", len(data))
        return None
    return data[0]


def decode_power_response(data: bytes) -> bool | None:
    """Decode power state from response data."""
    if len(data) != 1:
        _LOGGER.warning("Invalid power response data length: %d", len(data))
        return None
    return data[0] == 0x01


def decode_mute_response(data: bytes) -> bool | None:
    """Decode mute state from response data.""" 
    if len(data) != 1:
        _LOGGER.warning("Invalid mute response data length: %d", len(data))
        return None
    return data[0] == 0x01


def decode_source_response(data: bytes) -> str | None:
    """Decode source from response data."""
    if len(data) != 1:
        _LOGGER.warning("Invalid source response data length: %d", len(data))
        return None
    source_code = data[0]
    return get_source_name(source_code)


def decode_version_response(data: bytes) -> str | None:
    """Decode software version from response data."""
    if len(data) != 12:
        _LOGGER.warning("Invalid version response data length: %d", len(data))
        return None
    
    try:
        # Version data is typically ASCII text
        version_str = data.decode('ascii').rstrip('\x00')
        return version_str
    except UnicodeDecodeError:
        _LOGGER.warning("Could not decode version data as ASCII")
        return None