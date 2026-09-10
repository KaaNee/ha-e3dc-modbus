# E3DC (Modbus) – Home Assistant Custom Component

HACS-Integration für E3DC-Hauskraftwerke über Modbus/TCP. Ersetzt die klassische
`modbus:`-YAML-Konfiguration durch Config Flow, echte Entities/Devices und eine geteilte
Modbus-Verbindung (`homeassistant.components.modbus`, HA 2026.9+ "Modernizing Modbus")
statt eigenem Socket.

Nutzt [`e3dc-modbus`](https://github.com/KaaNee/e3dc-modbus) als Device Library (reines
Python, kein HA-Bezug, eigenes Repo) und
[`modbus-connection`](https://home-assistant-libs.github.io/modbus-connection/) als
Verbindungs-Framework.

> [!NOTE]
> Dieses Repository ist mit Unterstützung von KI (Claude Code) entstanden — Integration,
> Tests und Doku wurden gegen eine echte Home-Assistant-Instanz und echte Hardware verifiziert.

> [!NOTE]
> Gegen ein echtes E3DC S10 X Compact verifiziert (siehe `e3dc-modbus`s README). Wallbox-
> Schreibzugriffe sind unverifiziert — siehe `custom_components/e3dc_modbus/switch.py`.

## Installation

**Voraussetzung:** In `e3dc-modbus` ist noch nicht auf PyPI veröffentlicht. `manifest.json`
verweist auf `e3dc-modbus==0.0.2`, was aktuell **fehlschlägt**, sobald HA versucht, es zu
installieren. Bis zur Veröffentlichung:

```bash
# im venv der HA-Instanz
pip install -e /pfad/zu/e3dc-modbus
```

Danach als HACS Custom Repository (`Integration`, dieses Verzeichnis) hinzufügen, oder
`custom_components/e3dc_modbus/` manuell nach `<config>/custom_components/` kopieren.

**Am Gerät:** Hauptmenü → Smart-Funktionen → Smart Home → Modbus aktivieren, Protokoll
`E3DC` wählen (nicht `SUN_SPEC`).

**In HA:** Einstellungen → Geräte & Dienste → Integration hinzufügen → „E3DC (Modbus)“.
Host, Port (Standard 502), Unit-ID (Standard 1) eingeben — Verbindung wird sofort geprüft
(`async_get_temporary_unit`, siehe `config_flow.py`).

## Entities

| Domain | Beispiele | Quelle |
|---|---|---|
| `sensor` | PV-/Batterie-/Netzleistung, Netzbezug/-einspeisung, Batterielade-/entladeleistung, SOC, Autarkie, Eigenverbrauch, Netzzähler L1-L3, 3× String-Spannung/Strom/Leistung, Notstrom-Status, SG-Ready-Status | `sensor.py` |
| `binary_sensor` | Batterie-Lade-/Entladesperre, Notstrom möglich, wetterbasiertes Laden, Abregelung, Lade-/Entladesperrzeit | `binary_sensor.py` |
| `switch` | Pro Wallbox (0-7): Solarbetrieb, Laden abbrechen, Schuko an, einphasig laden | `switch.py` |

Keine Energie-Sensoren (kWh) direkt vom Gerät: E3DC hat keine nativen Lifetime-Zähler-Register
(siehe `e3dc-modbus`s const.py) — alles hier sind Momentanleistungen (W). Für's Energy Dashboard
siehe unten.

String 3 (unbenutzt auf diesem Gerätetyp lt. E3DC-Doku) und die Wallbox-Power-Sensoren
(nur relevant mit Wallbox) sind standardmäßig **deaktiviert**, aber vorhanden — in den
Entity-Einstellungen aktivierbar.

## Energy Dashboard einrichten

HA's Energy Dashboard braucht **Energie**-Sensoren (kWh, stetig steigend), keine
Leistungssensoren (W) — die liefert diese Integration nicht direkt, weil E3DC selbst keine
Lifetime-Zähler-Register hat. Für Netz und Batterie kommt dazu: das Dashboard will Bezug und
Einspeisung (bzw. Laden und Entladen) als **getrennte** Werte, nicht ein Signal mit
Vorzeichen. Deshalb gibt es hier vier zusätzliche, bereits vorzeichen-getrennte Leistungssensoren
(`grid_import_power`, `grid_export_power`, `battery_charge_power`, `battery_discharge_power`) —
die alte YAML-Config hat genau das über Template-Sensoren gelöst, hier ist es Teil der
Integration.

Fehlender letzter Schritt — Leistung (W) zu Energie (kWh) — ist reine HA-Bordmittel, kein
Code nötig:

1. **Einstellungen → Geräte & Dienste → Helfer → Helfer erstellen → Integralsensor**
   (= Riemann-Summe). Für jede Größe einen Helfer anlegen, Eingangssensor auf den
   passenden Leistungssensor, **Metrisches Präfix: k (kilo)** (sonst kommt Wh statt kWh
   raus), Zeiteinheit: Stunden:
   - PV-Leistung → *E3DC PV-Erzeugung*
   - Netzbezugsleistung → *E3DC Netzbezug*
   - Netzeinspeiseleistung → *E3DC Netzeinspeisung*
   - Batterieladeleistung → *E3DC Batterie Laden*
   - Batterieentladeleistung → *E3DC Batterie Entladen*
2. **Einstellungen → Dashboards → Energie**: die fünf neuen Helfer-Sensoren bei
   „Stromnetz“/„PV-Module“/„Heimspeicher“ eintragen (jeweils als „Aus dem Netz bezogene
   Energie“/„In das Netz eingespeiste Energie“ bzw. „Aus der Batterie entladene/In die
   Batterie geladene Energie“).
3. **Für Echtzeit-Leistungsanzeige** (nicht nur Tages-kWh): in denselben Dialogen bei
   „Art der Leistungsmessung“ **„Zwei Sensoren“** wählen — nicht „Standard“, das ist für
   einen einzelnen signed Sensor gedacht. Die vorzeichen-getrennten Leistungssensoren
   passen direkt hinein:
   - Netzanschluss: Netzbezugsleistung → *Netzbezugsleistung*, Netzeinspeiseleistung →
     *Netzeinspeiseleistung*
   - Heimspeicher: Entladeleistung → *Batterieentladeleistung*, Ladeleistung →
     *Batterieladeleistung*
4. Kann nach dem Anlegen bis zu ein paar Minuten dauern, bis die Statistik-Metadaten stehen
   (HA zeigt dazu eine gelbe, harmlose Warnung) — kein Fehler.

Ende-zu-Ende gegen die echte Anlage getestet (alle drei Kategorien, inkl. Echtzeit-Leistung).

**Warum keine fertigen kWh-Sensoren direkt aus der Integration?** Geprüft und bewusst so
entschieden — passt zum Vorgehen vergleichbarer Integrationen: SolarEdge (Core) und
[Anker Solix](https://github.com/thomluther/ha-anker-solix/discussions/16) (Solarbank/Batterie,
dieselbe Situation wie hier) liefern ebenfalls nur vorzeichen-getrennte Leistungssensoren und
verweisen für die kWh-Umwandlung auf HA's Integral-Helfer, statt selbst zu akkumulieren. Der
Anker-Solix-Maintainer begründet das explizit: Integrationsentitäten direkt im Dashboard sind
riskant (Historie bricht bei Integrationsänderungen, Wertspitzen korrumpieren Statistiken) —
der Helfer entkoppelt die Statistik von der Integration. Eine eigene Akkumulation in
`e3dc_modbus` müsste außerdem Neustart-sicher persistieren (`RestoreEntity`) und exakt HA's
eigene Integrationsmethode nachbilden — dupliziert, was HA bereits zuverlässig löst, für
zweifelhaften Gewinn.

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

## Entwicklung

```bash
scripts/setup      # installiert e3dc-modbus (editable) + HA + Testabhängigkeiten
scripts/lint        # ruff format + ruff check --fix
pytest              # 5 Tests: Config Flow, Setup/Unload, gegen modbus_connection.mock
scripts/develop     # startet eine echte HA-Instanz mit dieser Integration in ./config/
```

Devcontainer (`.devcontainer.json`) vorhanden — VS Code erkennt ihn automatisch und richtet
Python/Ruff/Pytest ein.

**Tests laufen ohne echte Hardware**: `tests/conftest.py`s `mock_e3dc_unit`-Fixture baut ein
`modbus_connection.mock.MockModbusUnit`, das wie ein echtes E3DC antwortet.
`test_config_flow.py` mockt nur `async_get_temporary_unit` (HA-Core-Code, nicht unserer);
`test_init.py` fährt einen echten Config-Entry-Setup/Unload-Zyklus und prüft reale
Entity-States danach.

## Bekannte Einschränkungen

- **Wallbox-Schreibpfad unverifiziert.** E3DCs Doku verlangt Modbus-Funktion 05H für
  Bit-Schreibzugriffe, `modbus_connection`s `bit()`-Feld schreibt aber per 06H. Ohne echte
  Wallbox nicht zu klären — Rückmeldungen willkommen.
- **`e3dc-modbus` noch nicht auf PyPI** — siehe Installation oben. `manifest.json`s
  `requirements` referenziert `e3dc-modbus==0.0.2`, was bei einer echten HA-Installation
  fehlschlägt, bis das Paket veröffentlicht ist (oder die Requirement-Zeile auf eine
  Git-URL umgestellt wird).
- **`.github/workflows/ci.yml`/`validate.yml` setzen ein GitHub-Repo voraus** (der
  `e3dc-modbus`-Checkout in `ci.yml`, hassfest/HACS in `validate.yml`) — funktionieren nicht
  auf Gitea. Vor dem GitHub-Umzug lokal mit `pytest`/`scripts/lint` prüfen.
- Nur S10 X Compact real getestet. Weitere Modelle: Modellprofil in `e3dc-modbus`s
  `models/` ergänzen, hier ändert sich nichts.

## Lizenz

Apache-2.0, siehe `LICENSE`.
