"""Config flow for E3DC (Modbus).

Validates the connection with a *temporary* Modbus unit before the config
entry exists (``async_get_temporary_unit`` — see the 2026.9 "Modernizing
Modbus" docs) so a typo in the host doesn't create a broken entry, and reuses
the device's own probe (``E3DCDevice.async_probe``) so "can we connect" and
"is this a model we support" are checked in the same step.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.modbus import async_get_temporary_unit
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.exceptions import HomeAssistantError
from modbus_connection import ModbusTcpParams
from modbus_connection.exceptions import ModbusError

from e3dc_modbus import E3DCDevice

from .const import CONF_UNIT_ID, DEFAULT_PORT, DEFAULT_UNIT_ID, DOMAIN, LOGGER

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): int,
    }
)


class E3DCModbusConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for E3DC (Modbus)."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """First (and only) step: host/port/unit ID, then probe the device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            params = ModbusTcpParams(host=user_input[CONF_HOST], port=user_input[CONF_PORT])
            try:
                async with async_get_temporary_unit(
                    self.hass, params, user_input[CONF_UNIT_ID]
                ) as unit:
                    device = await E3DCDevice.async_probe(unit)
            except (ModbusError, HomeAssistantError) as exception:
                # HomeAssistantError here means another entry already holds
                # this host/port with different link settings (see
                # async_get_temporary_unit's docstring) — surfaced the same
                # way as a plain connection failure, since the fix (matching
                # settings, or picking the right existing entry) is the
                # user's to make either way.
                LOGGER.warning("Could not reach E3DC device: %s", exception)
                errors["base"] = "cannot_connect"
            except ValueError as exception:
                # Raised by E3DCDevice.async_probe when no known model
                # profile matches — see e3dc_modbus/device.py.
                LOGGER.warning(exception)
                errors["base"] = "unsupported_model"
            else:
                await self.async_set_unique_id(device.info.serial_number)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"E3DC {device.profile.name}",
                    data={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                        CONF_UNIT_ID: user_input[CONF_UNIT_ID],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(STEP_USER_DATA_SCHEMA, user_input),
            errors=errors,
        )
