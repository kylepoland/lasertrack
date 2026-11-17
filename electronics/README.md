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
