# Contributing

1. `scripts/setup` — installiert alles (e3dc-modbus editable, Home Assistant, Testtools).
2. Ändern.
3. `scripts/lint` — Formatierung + Autofixes.
4. `pytest` — muss grün sein. Neue Entities/Verhalten brauchen einen Test (siehe
   `tests/conftest.py`s `mock_e3dc_unit` als Basis, kein echtes Gerät nötig).
5. `scripts/develop` — optional, für den manuellen Check gegen eine echte HA-Instanz.

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
