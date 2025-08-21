"""Constants for the Arcam AVR integration."""

# Integration domain
DOMAIN = "arcam_avr"

# Configuration keys
CONF_HOST = "host"
CONF_PORT = "port"
CONF_NAME = "name"

# Default values
DEFAULT_PORT = 50000
DEFAULT_NAME = "Arcam AVR"
DEFAULT_TIMEOUT = 3.0
DEFAULT_UPDATE_INTERVAL = 30  # seconds

# Device information
MANUFACTURER = "Arcam"
MODEL_PREFIX = "AVR"

# Supported device models
SUPPORTED_MODELS = [
    "AVR5", "AVR10", "AVR20", "AVR30", "AVR40",
    "AVR11", "AVR21", "AVR31", "AVR41"
]

# Entity name templates
ENTITY_NAME_FORMAT = "{name}"
DEVICE_NAME_FORMAT = "Arcam {model}"

# Source mappings and friendly names
SOURCE_MAPPING = {
    "CD": "CD Player",
    "BD": "Blu-ray Player",
    "AV": "AV Input",
    "STB": "Set-Top Box",
    "SAT": "Satellite",
    "PVR": "PVR",
    "VCR": "VCR",
    "AUX": "Auxiliary",
    "GAME": "Game Console",
    "NET": "Network",
    "FM": "FM Radio",
    "DAB": "DAB Radio",
    "BT": "Bluetooth",
    "USB": "USB",
    "UHD": "UHD Player",
}

# Available sources list (ordered for UI)
AVAILABLE_SOURCES = [
    "CD", "BD", "UHD", "STB", "SAT", "PVR", 
    "GAME", "AV", "AUX", "NET", "BT", "USB",
    "FM", "DAB", "VCR"
]

# Volume configuration
VOLUME_MIN = 0
VOLUME_MAX = 99
VOLUME_STEP = 1

# Update intervals
UPDATE_INTERVAL_NORMAL = 30  # seconds
UPDATE_INTERVAL_FAST = 5     # seconds (when recently active)

# Timeout configuration
COMMAND_TIMEOUT = 3.0        # seconds
CONNECTION_TIMEOUT = 5.0     # seconds
RECONNECT_TIMEOUT = 60.0     # seconds

# Error messages
ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_INVALID_HOST = "invalid_host"
ERROR_TIMEOUT = "timeout"
ERROR_UNKNOWN = "unknown"
ERROR_ALREADY_CONFIGURED = "already_configured"

# Device classes and features
DEVICE_CLASS_RECEIVER = "receiver"

# State attributes
ATTR_SOUND_MODE = "sound_mode"
ATTR_INPUT_SOURCE = "source"
ATTR_MODEL = "model"
ATTR_VERSION = "version"

# Service data keys
SERVICE_DATA_VOLUME = "volume_level"
SERVICE_DATA_SOURCE = "source"
SERVICE_DATA_MUTE = "is_volume_muted"

# Zone configuration
ZONE_1 = 1
ZONE_2 = 2
DEFAULT_ZONE = ZONE_1

# Connection retry configuration
MAX_RECONNECT_ATTEMPTS = 5
RECONNECT_DELAY_BASE = 1.0    # seconds
RECONNECT_DELAY_MAX = 16.0    # seconds

# Diagnostic information keys
DIAG_CONNECTION_STATUS = "connection_status"
DIAG_DEVICE_INFO = "device_info"
DIAG_RECENT_COMMANDS = "recent_commands"
DIAG_ERROR_LOG = "error_log"
DIAG_PERFORMANCE_METRICS = "performance_metrics"