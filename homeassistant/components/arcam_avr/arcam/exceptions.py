"""Arcam AVR exceptions."""


class ArcamError(Exception):
    """Base exception for Arcam AVR."""


class ArcamConnectionError(ArcamError):
    """Connection error."""


class ArcamProtocolError(ArcamError):
    """Protocol error."""


class ArcamCommandError(ArcamError):
    """Command execution error."""


class ArcamTimeoutError(ArcamError):
    """Command timeout error."""