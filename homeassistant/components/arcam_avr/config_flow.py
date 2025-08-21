"""Config flow for Arcam AVR integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.device_registry import format_mac

from .arcam.connection import ArcamConnection
from .arcam.exceptions import ArcamConnectionError, ArcamTimeoutError
from .const import (
    DOMAIN,
    DEFAULT_PORT,
    DEFAULT_NAME,
    ERROR_CANNOT_CONNECT,
    ERROR_INVALID_HOST,
    ERROR_TIMEOUT,
    ERROR_UNKNOWN,
    ERROR_ALREADY_CONFIGURED,
    MANUFACTURER,
)

_LOGGER = logging.getLogger(__name__)

# Configuration schema
STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    host = data[CONF_HOST]
    port = data[CONF_PORT]
    
    # Test connection to device
    connection = ArcamConnection(host, port)
    
    try:
        await connection.connect()
        
        # Get device information
        device_info = await connection.get_device_info()
        
        await connection.disconnect()
        
        # Extract model from version info if available
        model = "Unknown"
        version = device_info.get("version", "Unknown")
        
        if version != "Unknown":
            # Try to extract model from version string or use generic model
            model = "AVR"
            
        return {
            "title": f"Arcam {model}",
            "host": host,
            "port": port,
            "model": model,
            "version": version,
        }
        
    except ArcamTimeoutError:
        raise TimeoutError("Connection timeout") from None
    except ArcamConnectionError as err:
        raise ConnectionError(f"Cannot connect: {err}") from err
    except Exception as err:
        _LOGGER.exception("Unexpected error during validation")
        raise ConnectionError(f"Unexpected error: {err}") from err
    finally:
        try:
            await connection.disconnect()
        except Exception:
            pass  # Ignore disconnect errors


class ArcamAvrConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Arcam AVR."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._discovered_host: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check if device is already configured
            host = user_input[CONF_HOST]
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except ConnectionError as err:
                error_str = str(err).lower()
                if "timeout" in error_str:
                    errors["base"] = ERROR_TIMEOUT
                elif "cannot connect" in error_str:
                    errors["base"] = ERROR_CANNOT_CONNECT
                else:
                    errors["base"] = ERROR_UNKNOWN
                _LOGGER.error("Connection validation failed: %s", err)
            except TimeoutError:
                errors["base"] = ERROR_TIMEOUT
                _LOGGER.error("Connection timeout during validation")
            except Exception as err:
                errors["base"] = ERROR_UNKNOWN
                _LOGGER.exception("Unexpected error: %s", err)
            else:
                # Create the config entry
                return self.async_create_entry(
                    title=info["title"],
                    data={
                        CONF_HOST: host,
                        CONF_PORT: user_input[CONF_PORT],
                        CONF_NAME: user_input[CONF_NAME],
                        "model": info["model"],
                        "version": info["version"],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_import(self, import_config: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        # Check if device is already configured
        host = import_config[CONF_HOST]
        await self.async_set_unique_id(host)
        self._abort_if_unique_id_configured()

        # Fill in defaults for missing values
        data = {
            CONF_HOST: host,
            CONF_PORT: import_config.get(CONF_PORT, DEFAULT_PORT),
            CONF_NAME: import_config.get(CONF_NAME, DEFAULT_NAME),
        }

        try:
            info = await validate_input(self.hass, data)
        except (ConnectionError, TimeoutError) as err:
            _LOGGER.error("Import validation failed: %s", err)
            return self.async_abort(reason=ERROR_CANNOT_CONNECT)
        except Exception as err:
            _LOGGER.exception("Unexpected error during import: %s", err)
            return self.async_abort(reason=ERROR_UNKNOWN)

        return self.async_create_entry(
            title=info["title"],
            data={
                **data,
                "model": info["model"],
                "version": info["version"],
            },
        )

    async def async_step_discovery(self, discovery_info: dict[str, Any]) -> FlowResult:
        """Handle discovery of device."""
        host = discovery_info[CONF_HOST]
        
        # Check if device is already configured
        await self.async_set_unique_id(host)
        self._abort_if_unique_id_configured()

        self._discovered_host = host
        
        # Set form title to show discovered device
        self.context["title_placeholders"] = {"host": host}
        
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle user-confirmation of discovered device."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            data = {
                CONF_HOST: self._discovered_host,
                CONF_PORT: user_input.get(CONF_PORT, DEFAULT_PORT),
                CONF_NAME: user_input.get(CONF_NAME, DEFAULT_NAME),
            }
            
            try:
                info = await validate_input(self.hass, data)
            except (ConnectionError, TimeoutError):
                errors["base"] = ERROR_CANNOT_CONNECT
            except Exception:
                errors["base"] = ERROR_UNKNOWN
            else:
                return self.async_create_entry(
                    title=info["title"],
                    data={
                        **data,
                        "model": info["model"],
                        "version": info["version"],
                    },
                )

        schema = vol.Schema({
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        })

        return self.async_show_form(
            step_id="discovery_confirm",
            data_schema=schema,
            errors=errors,
            description_placeholders={"host": self._discovered_host},
        )

    @staticmethod
    @config_entries.HANDLERS.register(DOMAIN)
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> ArcamAvrOptionsFlow:
        """Create the options flow."""
        return ArcamAvrOptionsFlow(config_entry)


class ArcamAvrOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Arcam AVR."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Current options with defaults
        options = self.config_entry.options
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    "update_interval", 
                    default=options.get("update_interval", 30)
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
                vol.Optional(
                    "command_timeout", 
                    default=options.get("command_timeout", 3)
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
                vol.Optional(
                    "enable_zone2", 
                    default=options.get("enable_zone2", False)
                ): cv.boolean,
            }),
        )