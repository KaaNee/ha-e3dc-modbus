"""Constants for the E3DC (Modbus) integration."""

from __future__ import annotations

import logging

DOMAIN = "e3dc_modbus"
LOGGER = logging.getLogger(__package__)

ATTRIBUTION = "Data read locally from the E3DC Hauskraftwerk's Modbus/TCP interface"

# Not in homeassistant.const — E3DC's own term for the Modbus device/unit ID.
CONF_UNIT_ID = "unit_id"

DEFAULT_PORT = 502
DEFAULT_UNIT_ID = 1

#: How often to poll the device. E3DC's own doc caps requests at 10/s and
#: this integration reads one pooled block per update — 10s keeps power
#: readings responsive without hammering the device.
UPDATE_INTERVAL_SECONDS = 10

# --- Enum sensor value maps --------------------------------------------------
# Raw register value -> translation key (see translations/*.json). Doc
# reference: e3dc_modbus.const.EMERGENCY_POWER_STATUS / SG_READY_STATE.
EMERGENCY_POWER_STATUS_MAP: dict[int, str] = {
    0: "not_supported",
    1: "active",
    2: "inactive",
    3: "unavailable",
    4: "wrong_switch_position",
}

SG_READY_STATE_MAP: dict[int, str] = {
    1: "locked",
    2: "normal",
    3: "pv_surplus",
    4: "curtailed",
}
