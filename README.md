# E3DC (Modbus) – Home Assistant Custom Component

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=KaaNee&repository=ha-e3dc-modbus&category=integration)

HACS-Integration für E3DC-Hauskraftwerke über Modbus/TCP. Ersetzt die klassische
`modbus:`-YAML-Konfiguration durch Config Flow, echte Entities/Devices und eine geteilte
Modbus-Verbindung (`homeassistant.components.modbus`, HA 2026.9+ "Modernizing Modbus")
statt eigenem Socket.

Nutzt [`e3dc-modbus`](https://github.com/KaaNee/e3dc-modbus) als Device Library und
[`modbus-connection`](https://home-assistant-libs.github.io/modbus-connection/) als
Verbindungs-Framework.

> [!NOTE]
> Gegen ein echtes E3DC S10 X Compact verifiziert. Wallbox-Schreibzugriffe sind
> unverifiziert — siehe „Bekannte Einschränkungen“ unten.

## Installation

Über den Button oben als HACS Custom Repository hinzufügen (Kategorie „Integration“), oder
`custom_components/e3dc_modbus/` manuell nach `<config>/custom_components/` kopieren.

**Am Gerät:** Hauptmenü → Smart-Funktionen → Smart Home → Modbus aktivieren, Protokoll
`E3DC` wählen (nicht `SUN_SPEC`).

**In HA:** Einstellungen → Geräte & Dienste → Integration hinzufügen → „E3DC (Modbus)“.
Host, Port (Standard 502), Unit-ID (Standard 1) eingeben — Verbindung wird sofort geprüft.

## Entities

| Domain | Beispiele | Quelle |
|---|---|---|
| `sensor` | PV-/Batterie-/Netzleistung, Netzbezug/-einspeisung, Batterielade-/entladeleistung, SOC, Autarkie, Eigenverbrauch, Netzzähler L1-L3, 3× String-Spannung/Strom/Leistung, Notstrom-Status, SG-Ready-Status | `sensor.py` |
| `binary_sensor` | Batterie-Lade-/Entladesperre, Notstrom möglich, wetterbasiertes Laden, Abregelung, Lade-/Entladesperrzeit | `binary_sensor.py` |
| `switch` | Pro Wallbox (0-7): Solarbetrieb, Laden abbrechen, Schuko an, einphasig laden | `switch.py` |

Keine Energie-Sensoren (kWh) direkt vom Gerät: E3DC hat keine nativen Lifetime-Zähler-Register
— alles hier sind Momentanleistungen (W). Für's Energy Dashboard siehe unten.

String 3 (unbenutzt auf diesem Gerätetyp lt. E3DC-Doku) und die Wallbox-Power-Sensoren
(nur relevant mit Wallbox) sind standardmäßig **deaktiviert**, aber vorhanden — in den
Entity-Einstellungen aktivierbar.

## Energy Dashboard einrichten

Die Integration liefert nur Momentanleistung in Watt, keine kWh — E3DC hat dafür keine
Zähler-Register im Gerät. Für Netz und Batterie sind deshalb vier vorzeichen-getrennte
Leistungssensoren dabei (`grid_import_power`, `grid_export_power`, `battery_charge_power`,
`battery_discharge_power`), weil das Energy Dashboard Bezug/Einspeisung bzw. Laden/Entladen
getrennt haben will statt eines einzelnen Werts mit Vorzeichen.

Die Umrechnung in kWh übernimmt Home Assistants eigener Helfer:

1. **Einstellungen → Geräte & Dienste → Helfer → Helfer erstellen → Integralsensor**
   (Riemann-Summe). Leg für jede der fünf Größen einen Helfer an, Eingangssensor jeweils auf
   den passenden Leistungssensor, **Metrisches Präfix: k (kilo)** (sonst kommt Wh statt kWh
   raus), Zeiteinheit: Stunden:
   - PV-Leistung → *E3DC PV-Erzeugung*
   - Netzbezugsleistung → *E3DC Netzbezug*
   - Netzeinspeiseleistung → *E3DC Netzeinspeisung*
   - Batterieladeleistung → *E3DC Batterie Laden*
   - Batterieentladeleistung → *E3DC Batterie Entladen*
2. **Einstellungen → Dashboards → Energie**: die fünf neuen Helfer bei
   „Stromnetz“/„PV-Module“/„Heimspeicher“ eintragen (jeweils als „Aus dem Netz bezogene
   Energie“/„In das Netz eingespeiste Energie“ bzw. „Aus der Batterie entladene/In die
   Batterie geladene Energie“).
3. Für Echtzeit-Leistung (nicht nur Tages-kWh) in denselben Dialogen bei „Art der
   Leistungsmessung“ **„Zwei Sensoren“** wählen — nicht „Standard“, das ist für einen
   einzelnen signed Sensor gedacht:
   - Netzanschluss: Netzbezugsleistung → *Netzbezugsleistung*, Netzeinspeiseleistung →
     *Netzeinspeiseleistung*
   - Heimspeicher: Entladeleistung → *Batterieentladeleistung*, Ladeleistung →
     *Batterieladeleistung*

> [!TIP]
> Direkt nach dem Anlegen der Helfer zeigt HA kurz eine gelbe Warnung, dass Statistik-Daten
> fehlen — das legt sich nach ein paar Minuten von selbst, kein Fehler.

**Warum keine fertigen kWh-Sensoren direkt aus der Integration?** Hätte den Umweg über die
Helfer erspart, aber eine eigene Zählung im Code müsste bei jedem Neustart sauber
weiterlaufen und würde bei einem Update der Integration leicht die Statistik-Historie
durcheinanderbringen. Der HA-Helfer macht genau das schon zuverlässig — andere
Integrationen wie SolarEdge oder Anker Solix machen es aus demselben Grund genauso.

## Bekannte Einschränkungen

- **Wallbox-Schreibpfad unverifiziert.** E3DCs Doku verlangt Modbus-Funktion 05H für
  Bit-Schreibzugriffe, `modbus_connection`s `bit()`-Feld schreibt aber per 06H. Ohne echte
  Wallbox nicht zu klären — Rückmeldungen willkommen.
- Nur S10 X Compact real getestet. Weitere Modelle: Modellprofil in `e3dc-modbus`s
  `models/` ergänzen, hier ändert sich nichts.

## Markenrechte

Icon/Logo unter `custom_components/e3dc_modbus/brand/` stammen von der offiziellen
[E3DC-Website](https://www.e3dc.com) (HagerEnergy GmbH) und dienen ausschließlich der
Wiedererkennung im HA-Frontend. Markenrechte liegen bei HagerEnergy GmbH.

## Entwicklung

Siehe [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Lizenz

Apache-2.0, siehe `LICENSE`.
