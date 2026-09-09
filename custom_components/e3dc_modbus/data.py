"""Runtime data for the E3DC (Modbus) integration.

Stored on ``ConfigEntry.runtime_data`` per current HA convention — not in
``hass.data[DOMAIN]``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from e3dc_modbus import E3DCDevice

    from .coordinator import E3DCModbusDataUpdateCoordinator

type E3DCModbusConfigEntry = ConfigEntry[E3DCModbusData]


@dataclass
class E3DCModbusData:
    """Everything a platform needs, reachable via ``entry.runtime_data``."""

    device: E3DCDevice
    coordinator: E3DCModbusDataUpdateCoordinator
    integration: Integration
