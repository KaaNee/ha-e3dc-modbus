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

HA's Energy Dashboard braucht **Energie**-Sensoren (kWh, stetig steigend), keine
Leistungssensoren (W) — die liefert diese Integration nicht direkt, weil E3DC selbst keine
Lifetime-Zähler-Register hat. Für Netz und Batterie kommt dazu: das Dashboard will Bezug und
Einspeisung (bzw. Laden und Entladen) als **getrennte** Werte, nicht ein Signal mit
Vorzeichen. Deshalb gibt es hier vier zusätzliche, bereits vorzeichen-getrennte Leistungssensoren:
`grid_import_power`, `grid_export_power`, `battery_charge_power`, `battery_discharge_power`.

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

**Warum keine fertigen kWh-Sensoren direkt aus der Integration?** Bewusste Entscheidung,
passend zum Vorgehen vergleichbarer Integrationen (SolarEdge, Anker Solix): eigene
Akkumulation in der Integration ist riskant (Historie bricht bei Änderungen, Wertspitzen
korrumpieren Statistiken) — HA's Integral-Helfer entkoppelt die Statistik davon und macht
genau das schon zuverlässig.

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
