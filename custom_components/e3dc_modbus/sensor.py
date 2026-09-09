"""Sensor platform for E3DC (Modbus).

Every sensor reads straight off ``entry.runtime_data.device`` (updated by
the coordinator) via ``value_fn`` — there's no intermediate dict, since
``e3dc_modbus``'s blocks are already the live, mutable state.

String 3 and the wallbox power fields are registered but start disabled:
string 3 is documented "not used" on this device family, and the wallbox
power fields read as unavailable on any installation without a wallbox
(the project's own, for instance) — see e3dc-modbus's README/const.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
)

from .const import EMERGENCY_POWER_STATUS_MAP, SG_READY_STATE_MAP
from .entity import E3DCModbusEntity

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from e3dc_modbus import E3DCDevice

    from .coordinator import E3DCModbusDataUpdateCoordinator
    from .data import E3DCModbusConfigEntry

# String 3 (0-based index) is documented as unused on this device family —
# see e3dc-modbus's const.py.
_UNUSED_STRING_INDEX = 2


@dataclass(frozen=True, kw_only=True)
class E3DCSensorEntityDescription(SensorEntityDescription):
    """Sensor description bound to a value getter on ``E3DCDevice``.

    ``entity_registry_enabled_default`` is inherited from
    ``SensorEntityDescription``/``EntityDescription`` — set it per instance
    below to start an entity disabled (e.g. string 3, wallbox power).
    """

    value_fn: Callable[[E3DCDevice], float | int | str | None]


POWER_SENSORS: tuple[E3DCSensorEntityDescription, ...] = (
    E3DCSensorEntityDescription(
        key="pv_power",
        translation_key="pv_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda device: device.power.pv_power,
    ),
    E3DCSensorEntityDescription(
        key="battery_power",
        translation_key="battery_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda device: device.power.battery_power,
    ),
    E3DCSensorEntityDescription(
        key="household_power",
        translation_key="household_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda device: device.power.household_power,
    ),
    E3DCSensorEntityDescription(
        key="grid_power",
        translation_key="grid_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda device: device.power.grid_power,
    ),
    # Sign-split from grid_power/battery_power (doc: negative grid_power =
    # feed-in, negative battery_power = discharge) — the Energy Dashboard's
    # grid/battery panels need separate non-negative import/export and
    # charge/discharge sensors, not one signed value. Feed each of these
    # into HA's built-in "Integration - Riemann sum" helper to get the kWh
    # energy sensor the Energy Dashboard actually wants; see README.
    E3DCSensorEntityDescription(
        key="grid_import_power",
        translation_key="grid_import_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda device: (
            max(device.power.grid_power, 0) if device.power.grid_power is not None else None
        ),
    ),
    E3DCSensorEntityDescription(
        key="grid_export_power",
        translation_key="grid_export_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda device: (
            max(-device.power.grid_power, 0) if device.power.grid_power is not None else None
        ),
    ),
    E3DCSensorEntityDescription(
        key="battery_charge_power",
        translation_key="battery_charge_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda device: (
            max(device.power.battery_power, 0) if device.power.battery_power is not None else None
        ),
    ),
    E3DCSensorEntityDescription(
        key="battery_discharge_power",
        translation_key="battery_discharge_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda device: (
            max(-device.power.battery_power, 0) if device.power.battery_power is not None else None
        ),
    ),
    E3DCSensorEntityDescription(
        key="external_power",
        translation_key="external_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda device: device.power.external_power,
    ),
    E3DCSensorEntityDescription(
        key="wallbox_power",
        translation_key="wallbox_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda device: device.power.wallbox_power,
        entity_registry_enabled_default=False,
    ),
    E3DCSensorEntityDescription(
        key="wallbox_pv_power",
        translation_key="wallbox_pv_power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda device: device.power.wallbox_pv_power,
        entity_registry_enabled_default=False,
    ),
    E3DCSensorEntityDescription(
        key="battery_soc",
        translation_key="battery_soc",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda device: device.power.battery_soc,
    ),
    E3DCSensorEntityDescription(
        key="autarky",
        translation_key="autarky",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda device: device.power.autarky,
    ),
    E3DCSensorEntityDescription(
        key="self_consumption",
        translation_key="self_consumption",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda device: device.power.self_consumption,
    ),
    E3DCSensorEntityDescription(
        key="powermeter_l1",
        translation_key="powermeter_l1",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda device: device.power.powermeter_l1,
    ),
    E3DCSensorEntityDescription(
        key="powermeter_l2",
        translation_key="powermeter_l2",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda device: device.power.powermeter_l2,
    ),
    E3DCSensorEntityDescription(
        key="powermeter_l3",
        translation_key="powermeter_l3",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        value_fn=lambda device: device.power.powermeter_l3,
    ),
    E3DCSensorEntityDescription(
        key="emergency_power_status",
        translation_key="emergency_power_status",
        device_class=SensorDeviceClass.ENUM,
        options=list(EMERGENCY_POWER_STATUS_MAP.values()),
        value_fn=lambda device: (
            EMERGENCY_POWER_STATUS_MAP.get(device.ems.emergency_power_status)
            if device.ems.emergency_power_status is not None
            else None
        ),
    ),
    E3DCSensorEntityDescription(
        key="sg_ready_state",
        translation_key="sg_ready_state",
        device_class=SensorDeviceClass.ENUM,
        options=list(SG_READY_STATE_MAP.values()),
        value_fn=lambda device: (
            SG_READY_STATE_MAP.get(device.ems.sg_ready_state)
            if device.ems.sg_ready_state is not None
            else None
        ),
    ),
)


def _string_sensors(index: int) -> tuple[E3DCSensorEntityDescription, ...]:
    """Voltage/current/power for one PV string (0-based ``index``)."""
    enabled_by_default = index != _UNUSED_STRING_INDEX
    return (
        E3DCSensorEntityDescription(
            key=f"string_{index}_voltage",
            translation_key="string_voltage",
            translation_placeholders={"index": str(index + 1)},
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            value_fn=lambda device, i=index: device.strings.strings[i].voltage,
            entity_registry_enabled_default=enabled_by_default,
        ),
        E3DCSensorEntityDescription(
            key=f"string_{index}_current",
            translation_key="string_current",
            translation_placeholders={"index": str(index + 1)},
            device_class=SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            value_fn=lambda device, i=index: device.strings.strings[i].current,
            entity_registry_enabled_default=enabled_by_default,
        ),
        E3DCSensorEntityDescription(
            key=f"string_{index}_power",
            translation_key="string_power",
            translation_placeholders={"index": str(index + 1)},
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            native_unit_of_measurement=UnitOfPower.WATT,
            value_fn=lambda device, i=index: device.strings.strings[i].power,
            entity_registry_enabled_default=enabled_by_default,
        ),
    )


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 - required by the platform signature
    entry: E3DCModbusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors for one config entry."""
    coordinator = entry.runtime_data.coordinator
    string_count = len(entry.runtime_data.device.strings.strings)
    descriptions = list(POWER_SENSORS)
    for index in range(string_count):
        descriptions.extend(_string_sensors(index))

    async_add_entities(E3DCModbusSensor(coordinator, description) for description in descriptions)


class E3DCModbusSensor(E3DCModbusEntity, SensorEntity):
    """A single read-only E3DC value."""

    entity_description: E3DCSensorEntityDescription

    def __init__(
        self,
        coordinator: E3DCModbusDataUpdateCoordinator,
        entity_description: E3DCSensorEntityDescription,
    ) -> None:
        """Bind this sensor to its description and a stable unique ID."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{entity_description.key}"

    @property
    def native_value(self) -> float | int | str | None:
        """Current value, read live off the device object graph."""
        return self.entity_description.value_fn(self.coordinator.config_entry.runtime_data.device)
