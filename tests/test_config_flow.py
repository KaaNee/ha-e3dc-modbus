"""Test the config flow.

``async_get_temporary_unit`` itself belongs to HA core's ``modbus``
component (real TCP connection handling) — not our code, so it's mocked
here. Everything downstream of it (probing the device, error mapping,
unique_id, entry creation) is our code and is exercised for real.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from modbus_connection.exceptions import ModbusTimeoutError

from custom_components.e3dc_modbus.const import CONF_UNIT_ID, DOMAIN


@asynccontextmanager
async def _yield_unit(unit):
    yield unit


async def test_user_flow_creates_entry(hass: HomeAssistant, mock_e3dc_unit) -> None:
    """A reachable, supported device creates a config entry."""
    with patch(
        "custom_components.e3dc_modbus.config_flow.async_get_temporary_unit",
        side_effect=lambda *args, **kwargs: _yield_unit(mock_e3dc_unit),  # noqa: ARG005
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "e3dc.example", CONF_PORT: 502, CONF_UNIT_ID: 1},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "E3DC S10 X Compact"
    assert result["data"] == {CONF_HOST: "e3dc.example", CONF_PORT: 502, CONF_UNIT_ID: 1}


async def test_user_flow_duplicate_serial_aborts(hass: HomeAssistant, mock_e3dc_unit) -> None:
    """A second entry for the same physical device (same serial) is refused."""
    with patch(
        "custom_components.e3dc_modbus.config_flow.async_get_temporary_unit",
        side_effect=lambda *args, **kwargs: _yield_unit(mock_e3dc_unit),  # noqa: ARG005
    ):
        first = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.config_entries.flow.async_configure(
            first["flow_id"],
            {CONF_HOST: "e3dc.example", CONF_PORT: 502, CONF_UNIT_ID: 1},
        )

        second = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            second["flow_id"],
            # Different host, same device (same serial from the mock unit) —
            # must still be refused, since uniqueness is the serial, not the host.
            {CONF_HOST: "e3dc-other.example", CONF_PORT: 502, CONF_UNIT_ID: 1},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_user_flow_connection_error(hass: HomeAssistant) -> None:
    """An unreachable device shows a form error instead of crashing the flow."""

    @asynccontextmanager
    async def _raise(*_args, **_kwargs):
        raise ModbusTimeoutError("no response")
        yield  # pragma: no cover - unreachable, satisfies the generator shape

    with patch(
        "custom_components.e3dc_modbus.config_flow.async_get_temporary_unit",
        side_effect=_raise,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "e3dc.example", CONF_PORT: 502, CONF_UNIT_ID: 1},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
