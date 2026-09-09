"""DataUpdateCoordinator for the E3DC (Modbus) integration.

The coordinator's own ``data`` stays ``None`` on purpose: ``E3DCDevice`` and
its sub-blocks (``device.power``, ``device.ems``, ...) already hold live,
mutable state after ``async_update()`` — entities read straight off those
objects (``entry.runtime_data.device.power.pv_power``) rather than off a
coordinator-returned dict. The coordinator's job here is purely scheduling
+ error handling for one pooled Modbus read per interval.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from modbus_connection.exceptions import ModbusError

if TYPE_CHECKING:
    from .data import E3DCModbusConfigEntry


class E3DCModbusDataUpdateCoordinator(DataUpdateCoordinator[None]):
    """Poll the E3DC device once per interval."""

    config_entry: E3DCModbusConfigEntry

    async def _async_update_data(self) -> None:
        """Refresh every block via one pooled Modbus read.

        Raises ``UpdateFailed`` so entities go ``unavailable`` instead of
        showing a stale or crashing value on a dropped connection.
        """
        try:
            await self.config_entry.runtime_data.device.async_update()
        except ModbusError as exception:
            raise UpdateFailed(str(exception)) from exception
