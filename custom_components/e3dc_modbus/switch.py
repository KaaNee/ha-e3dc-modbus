"""Switch platform for E3DC (Modbus): per-wallbox controls.

UNVERIFIED — no wallbox to test against (see e3dc-modbus's README and
``e3dc_modbus.wallbox`` docstring). In particular, the write path itself is
in question: E3DC's doc requires Modbus function 05H for these bits, but
``modbus_connection``'s ``bit()`` field writes via 06H instead. Turning one
of these on/off against a real wallbox may simply do nothing, or worse — if
you have a wallbox, please report back what actually happens.

Entities exist for all 8 wallbox slots regardless of whether a wallbox
answers there: ``available`` follows the wallbox's own ``available`` bit, so
an unconnected slot just shows up gray instead of not existing — plug a
wallbox in later and its switches come alive without re-adding anything.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription

from .entity import E3DCModbusEntity

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine
    from typing import Any

    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from e3dc_modbus.wallbox import Wallbox

    from .coordinator import E3DCModbusDataUpdateCoordinator
    from .data import E3DCModbusConfigEntry

    _WallboxCoroutine = Coroutine[Any, Any, None]


@dataclass(frozen=True, kw_only=True)
class E3DCWallboxSwitchEntityDescription(SwitchEntityDescription):
    """Switch description bound to one boolean field on ``Wallbox``."""

    is_on_fn: Callable[[Wallbox], bool | None]
    turn_on_fn: Callable[[Wallbox], _WallboxCoroutine]
    turn_off_fn: Callable[[Wallbox], _WallboxCoroutine]


def _bit_switch(key: str, translation_key: str) -> E3DCWallboxSwitchEntityDescription:
    """Build a switch description for a single writable Wallbox bit field."""
    return E3DCWallboxSwitchEntityDescription(
        key=key,
        translation_key=translation_key,
        is_on_fn=lambda wallbox: getattr(wallbox, key),
        turn_on_fn=lambda wallbox: wallbox.write(key, True),  # noqa: FBT003
        turn_off_fn=lambda wallbox: wallbox.write(key, False),  # noqa: FBT003
    )


WALLBOX_SWITCHES: tuple[E3DCWallboxSwitchEntityDescription, ...] = (
    _bit_switch("sunmode", "wallbox_sunmode"),
    _bit_switch("charging_aborted", "wallbox_charging_aborted"),
    _bit_switch("schuko_on", "wallbox_schuko_on"),
    _bit_switch("one_phase_charging", "wallbox_one_phase_charging"),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 - required by the platform signature
    entry: E3DCModbusConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up wallbox control switches for one config entry."""
    coordinator = entry.runtime_data.coordinator
    wallboxes = entry.runtime_data.device.wallbox.wallboxes
    async_add_entities(
        E3DCModbusWallboxSwitch(coordinator, description, index)
        for index in range(len(wallboxes))
        for description in WALLBOX_SWITCHES
    )


class E3DCModbusWallboxSwitch(E3DCModbusEntity, SwitchEntity):
    """One writable control bit on one wallbox slot."""

    entity_description: E3DCWallboxSwitchEntityDescription

    def __init__(
        self,
        coordinator: E3DCModbusDataUpdateCoordinator,
        entity_description: E3DCWallboxSwitchEntityDescription,
        index: int,
    ) -> None:
        """Bind this switch to one wallbox slot's control bit."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._index = index
        self._attr_translation_placeholders = {"index": str(index + 1)}
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_wallbox_{index}_{entity_description.key}"
        )

    @property
    def _wallbox(self) -> Wallbox:
        return self.coordinator.config_entry.runtime_data.device.wallbox.wallboxes[self._index]

    @property
    def available(self) -> bool:
        """Gray out this switch on a slot with no wallbox plugged in."""
        return super().available and bool(self._wallbox.available)

    @property
    def is_on(self) -> bool | None:
        """Current bit state, read live off the wallbox object."""
        return self.entity_description.is_on_fn(self._wallbox)

    async def async_turn_on(self, **kwargs: object) -> None:  # noqa: ARG002
        """Set this control bit — UNVERIFIED, see module docstring."""
        await self.entity_description.turn_on_fn(self._wallbox)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: object) -> None:  # noqa: ARG002
        """Clear this control bit — UNVERIFIED, see module docstring."""
        await self.entity_description.turn_off_fn(self._wallbox)
        await self.coordinator.async_request_refresh()
