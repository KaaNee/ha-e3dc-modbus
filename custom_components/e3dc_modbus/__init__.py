"""E3DC (Modbus) integration.

Uses HA's shared Modbus connection (``homeassistant.components.modbus``,
2026.9+ "Modernizing Modbus") instead of opening its own socket — that's the
whole point of this integration replacing the old ``modbus:`` YAML platform,
see the project plan §1. Reads all subsystems (power/strings/EMS/wallbox) in
one pooled poll via ``e3dc_modbus.E3DCDevice``.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.components.modbus import async_get_unit
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.loader import async_get_loaded_integration
from modbus_connection import ModbusTcpParams

from e3dc_modbus import E3DCDevice

from .const import CONF_UNIT_ID, DOMAIN, LOGGER, UPDATE_INTERVAL_SECONDS
from .coordinator import E3DCModbusDataUpdateCoordinator
from .data import E3DCModbusData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import E3DCModbusConfigEntry

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: E3DCModbusConfigEntry) -> bool:
    """Set up E3DC (Modbus) from a config entry."""
    unit = async_get_unit(
        hass,
        entry,
        ModbusTcpParams(host=entry.data[CONF_HOST], port=entry.data[CONF_PORT]),
        entry.data[CONF_UNIT_ID],
    )
    device = await E3DCDevice.async_probe(unit)

    coordinator = E3DCModbusDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        config_entry=entry,
    )
    entry.runtime_data = E3DCModbusData(
        device=device,
        coordinator=coordinator,
        integration=async_get_loaded_integration(hass, entry.domain),
    )

    # First refresh here (not deferred to the coordinator's own schedule) so
    # setup fails cleanly if the device doesn't answer, instead of entities
    # starting up in an unknown state. See:
    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: E3DCModbusConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
