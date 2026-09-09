"""Shared fixtures for e3dc_modbus tests."""

from __future__ import annotations

import pytest
from e3dc_modbus import const
from modbus_connection.mock import MockModbusConnection, MockModbusUnit

pytest_plugins = "pytest_homeassistant_custom_component"


def _encode_string(text: str, words: int) -> list[int]:
    """Encode ``text`` as null-padded ASCII register words (2 chars/word)."""
    raw = text.encode("ascii").ljust(words * 2, b"\x00")
    return [int.from_bytes(raw[i : i + 2], "big") for i in range(0, len(raw), 2)]


def _encode_int32_lsw_msw(value: int) -> tuple[int, int]:
    """Encode ``value`` as (LSW, MSW) — E3DC's word-swapped Int32 layout."""
    unsigned = value & 0xFFFFFFFF
    return unsigned & 0xFFFF, (unsigned >> 16) & 0xFFFF


@pytest.fixture
def mock_e3dc_unit() -> MockModbusUnit:
    """A mock Modbus unit that answers like a real E3DC S10 X Compact."""
    conn = MockModbusConnection()
    unit = conn.for_unit(1)
    unit.holding[const.MODBUS_ID.address] = const.E3DC_MAGIC_BYTE
    unit.holding[const.MANUFACTURER.address] = _encode_string("HagerEnergy GmbH", 16)
    unit.holding[const.MODEL_NAME.address] = _encode_string("S10 X Compact", 16)
    unit.holding[const.SERIAL_NUMBER.address] = _encode_string("H20-000000000000", 16)
    unit.holding[const.FIRMWARE_RELEASE.address] = _encode_string("H20_2026_02", 16)
    unit.holding[const.PV_POWER.address] = 400
    unit.holding[const.PV_POWER.address + 1] = 0
    # Grid: importing 300 W. Battery: discharging 500 W (negative per doc).
    grid_lsw, grid_msw = _encode_int32_lsw_msw(300)
    unit.holding[const.GRID_POWER.address] = grid_lsw
    unit.holding[const.GRID_POWER.address + 1] = grid_msw
    battery_lsw, battery_msw = _encode_int32_lsw_msw(-500)
    unit.holding[const.BATTERY_POWER.address] = battery_lsw
    unit.holding[const.BATTERY_POWER.address + 1] = battery_msw
    unit.holding[const.BATTERY_SOC.address] = 91
    unit.holding[const.AUTARKY_AND_CONSUMPTION.address] = 26 * 256 + 82
    return unit


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):  # noqa: ARG001
    """Make custom_components/ discoverable in every test automatically."""
    return
