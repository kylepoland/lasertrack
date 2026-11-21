# Electronics

Wiring is documented as pin-map tables, one file per subsystem. Nothing is
designed yet; the table below is the format to follow.

## Pin-map template

Board: _name_ — logic level: _3.3 V / 5 V_ — powered from: _source_

| Signal | Board pin | Connects to | Device pin | Notes |
|---|---|---|---|---|
| _example: I2C SDA_ | _GPIO 21_ | _NFC reader_ | _SDA_ | _3.3 V only_ |

## Power

| Rail | Source | Loads | Estimated current |
|---|---|---|---|
| 5 V | Mean Well GST25 5 V 4 A supply → panel 5.5 x 2.1 jack → short barrel-to-USB-C lead → Pi USB-C | Pi 4, fan, screen backlight, cartridge LEDs (later) | ~3 A peak (Pi 4 under load ~1.5 A + USB) |
| 3.3 V | Pi's regulator (pins 1, 17) | RC522, screen logic, IR receiver | < 100 mA |

Parts to buy for the box: `box-parts.md`.
