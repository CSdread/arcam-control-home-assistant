"""Test Arcam AVR config flow."""
import pytest
from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.components.arcam_avr.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry


async def test_form_user(hass):
    """Test the user configuration form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_form_user_success(hass, mock_connection_factory):
    """Test successful user configuration."""
    with patch(
        "homeassistant.components.arcam_avr.config_flow.ArcamConnection"
    ) as mock_connection_class:
        # Set up mock connection
        mock_connection_class.return_value = await mock_connection_factory("192.168.1.100", 50000)
        
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 50000,
                CONF_NAME: "Test AVR",
            },
        )
        
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Arcam AVR"
        assert result["data"][CONF_HOST] == "192.168.1.100"
        assert result["data"][CONF_PORT] == 50000
        assert result["data"][CONF_NAME] == "Test AVR"


async def test_form_user_connection_error(hass):
    """Test connection error during configuration."""
    with patch(
        "homeassistant.components.arcam_avr.config_flow.ArcamConnection"
    ) as mock_connection_class:
        mock_conn = AsyncMock()
        mock_conn.connect.side_effect = ConnectionError("Connection failed")
        mock_connection_class.return_value = mock_conn
        
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 50000,
                CONF_NAME: "Test AVR",
            },
        )
        
        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "cannot_connect"}


async def test_form_user_timeout_error(hass):
    """Test timeout error during configuration."""
    with patch(
        "homeassistant.components.arcam_avr.config_flow.ArcamConnection"
    ) as mock_connection_class:
        mock_conn = AsyncMock()
        mock_conn.connect.side_effect = TimeoutError("Connection timeout")
        mock_connection_class.return_value = mock_conn
        
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 50000,
                CONF_NAME: "Test AVR",
            },
        )
        
        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "timeout"}


async def test_form_user_unknown_error(hass):
    """Test unknown error during configuration."""
    with patch(
        "homeassistant.components.arcam_avr.config_flow.ArcamConnection"
    ) as mock_connection_class:
        mock_conn = AsyncMock()
        mock_conn.connect.side_effect = Exception("Unknown error")
        mock_connection_class.return_value = mock_conn
        
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 50000,
                CONF_NAME: "Test AVR",
            },
        )
        
        assert result["type"] == FlowResultType.FORM
        assert result["errors"] == {"base": "unknown"}


async def test_duplicate_entry(hass):
    """Test duplicate entry handling."""
    # Create existing entry
    MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.100", CONF_PORT: 50000},
    ).add_to_hass(hass)
    
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={CONF_HOST: "192.168.1.100", CONF_PORT: 50000, CONF_NAME: "Test AVR"},
    )
    
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_import_flow_success(hass, mock_connection_factory):
    """Test successful import flow."""
    with patch(
        "homeassistant.components.arcam_avr.config_flow.ArcamConnection"
    ) as mock_connection_class:
        mock_connection_class.return_value = await mock_connection_factory("192.168.1.100", 50000)
        
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 50000,
            },
        )
        
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_HOST] == "192.168.1.100"
        assert result["data"][CONF_PORT] == 50000


async def test_import_flow_connection_error(hass):
    """Test import flow with connection error."""
    with patch(
        "homeassistant.components.arcam_avr.config_flow.ArcamConnection"
    ) as mock_connection_class:
        mock_conn = AsyncMock()
        mock_conn.connect.side_effect = ConnectionError("Connection failed")
        mock_connection_class.return_value = mock_conn
        
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 50000,
            },
        )
        
        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "cannot_connect"


async def test_discovery_flow(hass, mock_connection_factory):
    """Test discovery flow."""
    with patch(
        "homeassistant.components.arcam_avr.config_flow.ArcamConnection"
    ) as mock_connection_class:
        mock_connection_class.return_value = await mock_connection_factory("192.168.1.100", 50000)
        
        # Start discovery
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_DISCOVERY},
            data={CONF_HOST: "192.168.1.100"},
        )
        
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "discovery_confirm"
        
        # Confirm discovery
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PORT: 50000, CONF_NAME: "Discovered AVR"},
        )
        
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_HOST] == "192.168.1.100"


async def test_options_flow(hass):
    """Test options flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "192.168.1.100", CONF_PORT: 50000},
        options={"update_interval": 30},
    )
    entry.add_to_hass(hass)
    
    result = await hass.config_entries.options.async_init(entry.entry_id)
    
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"
    
    # Test updating options
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "update_interval": 60,
            "command_timeout": 5,
            "enable_zone2": True,
        },
    )
    
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "update_interval": 60,
        "command_timeout": 5,
        "enable_zone2": True,
    }