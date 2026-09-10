# Contributing

1. `scripts/setup` — installiert alles (e3dc-modbus editable, Home Assistant, Testtools).
2. Ändern.
3. `scripts/lint` — Formatierung + Autofixes.
4. `pytest` — muss grün sein. Neue Entities/Verhalten brauchen einen Test (siehe
   `tests/conftest.py`s `mock_e3dc_unit` als Basis, kein echtes Gerät nötig).
5. `scripts/develop` — optional, für den manuellen Check gegen eine echte HA-Instanz.

## Architektur

- **`__init__.py`**: holt sich per `async_get_unit` eine geteilte Modbus-Unit von HA's
  `modbus`-Integration, probet das Gerät (`E3DCDevice.async_probe`), startet den Coordinator.
- **`coordinator.py`**: `DataUpdateCoordinator[None]` — pollt einmal pro Intervall
  (`device.async_update()`), liefert selbst keine Daten zurück. Entities lesen live von
  `entry.runtime_data.device.power.pv_power` etc., da `e3dc_modbus`s Blöcke bereits
  mutable State sind (kein Zwischen-Dict nötig).
- **`data.py`**: `entry.runtime_data` (aktuelles Pattern, nicht `hass.data[DOMAIN]`).
- **`entity.py`**: gemeinsame `DeviceInfo` (Hersteller/Modell/Seriennummer/Firmware aus dem
  Probe) für jede Entity.
- **`config_flow.py`**: validiert mit `async_get_temporary_unit` (Context-Manager, gibt die
  Verbindung nach der Prüfung wieder frei) — kein Entry entsteht, bevor das Gerät antwortet.
  `unique_id` ist die Seriennummer, nicht Host/Port (Geräte-Identität bleibt stabil, auch
  wenn sich die IP ändert).

## Test-Instanz manuell starten

Ohne Devcontainer, z. B. gegen echte Hardware:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_test.txt -r requirements_dev.txt   # braucht ../e3dc-modbus als Sibling
scripts/develop
```

Läuft standardmäßig auf Port 8123. Falls belegt: vor dem ersten Start
`config/configuration.yaml` (wird bei Bedarf von `scripts/develop` angelegt) um einen Port
ergänzen:

```yaml
http:
  server_port: 8124
```

`config/` ist gitignored und enthält die echte lokale HA-Instanz inkl. Config-Entries —
niemals committen (enthält Host/Seriennummer der echten Anlage).

Devcontainer (`.devcontainer.json`) vorhanden — VS Code erkennt ihn automatisch und richtet
Python/Ruff/Pytest ein.

**Tests laufen ohne echte Hardware**: `tests/conftest.py`s `mock_e3dc_unit`-Fixture baut ein
`modbus_connection.mock.MockModbusUnit`, das wie ein echtes E3DC antwortet.
`test_config_flow.py` mockt nur `async_get_temporary_unit` (HA-Core-Code, nicht unserer);
`test_init.py` fährt einen echten Config-Entry-Setup/Unload-Zyklus und prüft reale
Entity-States danach.

**CI läuft nur auf GitHub** (`.github/workflows/ci.yml`/`validate.yml`) — der Gitea-Spiegel
dieses Repos hat keine laufende CI. Bei Änderungen dort lokal mit `pytest`/`scripts/lint`
prüfen.

## Neues E3DC-Modell hinzufügen

Betrifft nur [`e3dc-modbus`](https://github.com/KaaNee/e3dc-modbus), nicht dieses Repo: neue
Datei unter `e3dc_modbus/models/`, siehe `models/s10_x_compact.py` als Vorlage. Diese
Integration merkt davon nichts.

## Neue Entity hinzufügen

1. Feld/Wert existiert bereits auf `E3DCDevice` (`device.power.*`, `device.ems.*`, ...)?
   Falls nicht: erst in `e3dc-modbus` ergänzen (siehe dortige `CONTRIBUTING`/README).
2. `EntityDescription` in `sensor.py`/`binary_sensor.py`/`switch.py` ergänzen (`value_fn`
   liest vom `E3DCDevice`-Objektgraphen, kein Zwischen-Dict).
3. `translation_key` + Übersetzung in `strings.json` **und** `translations/en.json` +
   `translations/de.json` (drei Dateien, sonst zeigt HA nur den rohen Key).
4. Optional: Icon in `icons.json`, falls der `device_class` kein sinnvolles Default-Icon hat.
5. Test in `tests/test_init.py` ergänzen: Wert im `mock_e3dc_unit`-Fixture setzen, State
   nach Setup prüfen.

## Wallbox-Schreibpfad klären

Falls du eine echte E3DC-Wallbox hast: probier einen Switch (z. B. „Wallbox 1 Solarbetrieb“)
und melde per Issue, ob sich am Gerät tatsächlich etwas ändert. Siehe README „Bekannte
Einschränkungen“ für den Hintergrund (Function 05H vs. 06H).
