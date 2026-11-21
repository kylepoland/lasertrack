# Set-top box: parts to buy

Parts the box model (`cad/models/box.py`) is drawn around. Each has a
parameter block in `cad/params.py`; values marked NOMINAL there come from a
product page and must be measured when the part arrives. Swapping a part
means editing its block and rebuilding.

| Part | Suggested | Notes | Params |
|---|---|---|---|
| Screen | Adafruit 1.54" 240x240 wide-angle TFT, ST7789 (product 3787) | SPI, 3.3 V logic and power. Board ~43.7 x 41.8, M2.5 holes on ~36.8 x 35.6 (sources disagree slightly), display 32 x 31. EYESPI flat-flex connector or pin header | `LCD_*` |
| Buttons (5) | 12 x 12 x 7.3 mm tactile switches (a pack with caps is fine; the printed caps replace them) | Soldered on a perfboard strip cut to 120 x 30 mm (from a 9 x 15 cm board) | `BUTTON_*`, `TACT_*`, `CAP_*` |
| Volume knob | EC11 rotary encoder with push switch, 20 mm D shaft, M7 bushing | Nut on the front of the panel; printed knob | `ENC_*`, `KNOB_*` |
| IR receiver | TSOP38238 (38 kHz) | On the button board, behind a 6 mm hole | `IR_*` |
| Status LED | 3 mm LED + resistor | On the button board above Power | `LED_*` |
| Power supply | Mean Well GST25A05-P1J (5 V 4 A, 5.5 x 2.1 mm barrel, centre positive), or the wall-plug version GST25U05-P1J | Desktop brick needs a C14 mains cord; the wall-plug version doesn't | — |
| Power jack | 5.5 x 2.1 mm panel-mount barrel jack, threaded (M8 nut) | Measure the thread; `DC_JACK_HOLE` is NOMINAL 8.0 | `DC_JACK_*` |
| Power lead inside | Short 5.5 x 2.1 mm plug to USB-C plug cable, 18-20 AWG | Jack to the Pi's USB-C, so the Pi's own input circuit stays in use. A right-angle USB-C end saves room | — |
| HDMI | Panel-mount HDMI socket to micro-HDMI plug extension, ~30 cm, with screw ears | Cutout and ear spacing are NOMINAL | `HDMI_*` |
| Composite + audio | 3.5 mm 4-pole panel-mount extension (male to female), ~30 cm | Kyle's existing cable plugs into it and splits video and stereo audio | `AV_JACK_*` |
| Output switch | Mini toggle switch, SPDT, 6 mm bushing (MTS-102 type) | HDMI / composite, read at boot | `TOGGLE_*` |
| Fan | 30 x 30 mm 5 V fan on a Pi 4 heatsink, total under 17 mm above the board | Exhausts up through the top grille | `PI_FAN_STACK` |
| Shell screws (8) | M3 x 35 pan head, hex socket | Up through the floor, columns and plate into the top tiles | `SHELL_SCREW_*` |
| Panel and board screws | M3 x 6 low pan head (Kyle has these) | Panels (4), button board (4), slot onto risers needs M3 x 8 (4) | — |
| Pi and screen screws | M2.5 x 6 (8) | Pi onto the plate standoffs (4), screen onto its posts (4) | `PI_PILOT`, `LCD_PILOT` |
| Feet | Printed, glued in | Or stick-on rubber bumpers | `FOOT_*` |

Already owned: Raspberry Pi 4 (2 GB), RC522 reader, spring ball plungers.
