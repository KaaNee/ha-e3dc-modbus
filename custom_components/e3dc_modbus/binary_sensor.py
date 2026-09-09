"""Binary sensor platform for E3DC (Modbus): EMS lock/status flags.

All 7 flags decode from the single EMS status register (see
``e3dc_modbus.const.EMS_STATUS_BITS``) — reading each is cheap once the
coordinator has polled that one register.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from .entity import E3DCModbusEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from e3dc_modbus import E3DCDevice

    from .coordinator import E3DCModbusDataUpdateCoordinator
    from .data import E3DCModbusConfigEntry


@dataclass(frozen=True, kw_only=True)
class E3DCBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Binary sensor description bound to a value getter on ``E3DCDevice``."""

    value_fn: Callable[[E3DCDevice], bool | None]


EMS_FLAG_SENSORS: tuple[E3DCBinarySensorEntityDescription, ...] = (
    E3DCBinarySensorEntityDescription(
        key="battery_charging_lock",
        translation_key="battery_charging_lock",
        value_fn=lambda device: device.ems.battery_charging_lock,
    ),
    E3DCBinarySensorEntityDescription(
        key="battery_discharging_lock",
        translation_key="battery_discharging_lock",
        value_fn=lambda device: device.ems.battery_discharging_lock,
    ),
    E3DCBinarySensorEntityDescription(
        key="emergency_power_possible",
        translation_key="emergency_power_possible",
        value_fn=lambda device: device.ems.emergency_power_possible,
    ),
    E3DCBinarySensorEntityDescription(
        key="weather_predicted_charging",
        translation_key="weather_predicted_charging",
        value_fn=lambda device: device.ems.weather_predicted_charging,
    ),
    E3DCBinarySensorEntityDescription(
        key="regulation_status",
        translation_key="regulation_status",
        value_fn=lambda device: device.ems.regulation_status,
    ),
    E3DCBinarySensorEntityDescription(
        key="charge_lock_time",
        translation_key="charge_lock_time",
        value_fn=lambda device: device.ems.charge_lock_time,
    ),
    E3DCBinarySensorEntityDescription(
        key="discharge_lock_time",
        translation_key="discharge_lock_time",
        value_fn=lambda device: device.ems.discharge_lock_time,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 - required by the platform signature
    entry: E3DCModbusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up EMS flag binary sensors for one config entry."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        E3DCModbusBinarySensor(coordinator, description) for description in EMS_FLAG_SENSORS
    )


class E3DCModbusBinarySensor(E3DCModbusEntity, BinarySensorEntity):
    """One EMS flag bit."""

    entity_description: E3DCBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: E3DCModbusDataUpdateCoordinator,
        entity_description: E3DCBinarySensorEntityDescription,
    ) -> None:
        """Bind this binary sensor to its description and a stable unique ID."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{entity_description.key}"

    @property
    def is_on(self) -> bool | None:
        """Current flag state, read live off the device object graph."""
        return self.entity_description.value_fn(self.coordinator.config_entry.runtime_data.device)
