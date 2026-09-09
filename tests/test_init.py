"""Test setting up a config entry end to end (mocked Modbus connection)."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.e3dc_modbus.const import CONF_UNIT_ID, DOMAIN


async def test_setup_entry_creates_expected_entities(hass: HomeAssistant, mock_e3dc_unit) -> None:
    """A full setup probes the device, polls it once, and creates entities."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "e3dc.example", CONF_PORT: 502, CONF_UNIT_ID: 1},
        unique_id="H20-000000000000",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.e3dc_modbus.async_get_unit", return_value=mock_e3dc_unit):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED

    pv_power = hass.states.get("sensor.e3dc_s10_x_compact_pv_power")
    assert pv_power is not None
    assert pv_power.state == "400"

    battery_soc = hass.states.get("sensor.e3dc_s10_x_compact_battery_state_of_charge")
    assert battery_soc is not None
    assert battery_soc.state == "91"

    autarky = hass.states.get("sensor.e3dc_s10_x_compact_autarky")
    assert autarky is not None
    assert autarky.state == "26"

    # Sign-split sensors for the Energy Dashboard: grid importing 300 W,
    # battery discharging 500 W (see conftest.py's mock_e3dc_unit).
    grid_import = hass.states.get("sensor.e3dc_s10_x_compact_grid_import_power")
    assert grid_import is not None
    assert grid_import.state == "300"

    grid_export = hass.states.get("sensor.e3dc_s10_x_compact_grid_export_power")
    assert grid_export is not None
    assert grid_export.state == "0"

    battery_charge = hass.states.get("sensor.e3dc_s10_x_compact_battery_charge_power")
    assert battery_charge is not None
    assert battery_charge.state == "0"

    battery_discharge = hass.states.get("sensor.e3dc_s10_x_compact_battery_discharge_power")
    assert battery_discharge is not None
    assert battery_discharge.state == "500"

    # 8 wallbox slots x 4 switches each, all unavailable (no wallbox present
    # on the mock unit's register data — every bit reads 0/False).
    wallbox_switch = hass.states.get("switch.e3dc_s10_x_compact_wallbox_1_solar_only_mode")
    assert wallbox_switch is not None
    assert wallbox_switch.state == "unavailable"


async def test_unload_entry(hass: HomeAssistant, mock_e3dc_unit) -> None:
    """Unloading a loaded entry succeeds and tears platforms down."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: "e3dc.example", CONF_PORT: 502, CONF_UNIT_ID: 1},
        unique_id="H20-000000000000",
    )
    entry.add_to_hass(hass)

    with patch("custom_components.e3dc_modbus.async_get_unit", return_value=mock_e3dc_unit):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
