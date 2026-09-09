"""Base entity for the E3DC (Modbus) integration.

Every platform entity subclasses this so the device is registered once,
consistently, with the info the E3DC probe already gave us for free.
"""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import E3DCModbusDataUpdateCoordinator


class E3DCModbusEntity(CoordinatorEntity[E3DCModbusDataUpdateCoordinator]):
    """Common device_info/attribution/naming for every e3dc_modbus entity."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator: E3DCModbusDataUpdateCoordinator) -> None:
        """Tie this entity to the one E3DC device the config entry represents."""
        super().__init__(coordinator)
        device = coordinator.config_entry.runtime_data.device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            manufacturer=device.info.manufacturer,
            model=device.profile.name,
            name=f"E3DC {device.profile.name}",
            serial_number=device.info.serial_number,
            sw_version=device.info.firmware_release,
        )
