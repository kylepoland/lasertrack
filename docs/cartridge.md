# Cartridge electronics: contacts and the smart-cartridge PCB

How a cartridge is detected, identified, powered and lit. It covers the
cartridge PCB, its contact pads, the pogo pins in the slot floor, and the
board that carries them. The cartridge's shell, screws, ribs and detent are in
`decisions.md` (2026-11-17 to 2026-11-20); its dimensions are in `cad/params.py`.

Status, 2026-11-24: all of this is agreed with Kyle. Nothing has been designed
in KiCad, ordered or printed. Exact part numbers, pin assignments and
dimensions are still to be confirmed (see "Open").

## Why the change

The v1 box used an RC522 NFC reader and NTAG215 stickers. A bare tag on the
reader read reliably, but a tag inside a printed cartridge dropped out for more
than a second at a time, so the daemon saw the cartridge eject and re-insert.
Software debouncing (time-based removal, RF reset and retry) wasn't enough.
Wired contacts can't drop out like that, and they also carry power for lights
and add-ons.

## Decided

- **The cartridge carries a small custom PCB on its open bottom edge, with
  gold contact pads facing down.** Pogo pins in the slot floor press up on
  them. This reverses "no custom PCBs yet" (2026-11-16).
- **No NFC in the cartridge or the box.** The PCB does detection and ID. The
  RC522 and NTAG215 stickers are retired once the PCB works.
- **A microcontroller on every cartridge ("smart cartridge").** It reports the
  chip's factory unique ID, so every cartridge runs identical firmware. It
  drives the cartridge lights and any later add-ons, and talks to the box over
  a wire. This reverses "no microcontroller in V1" (2026-11-18).
- **6 contact pads: 5V, GND, TX, RX, SWIO, 3V3** (2026-11-24, was 5). The
  second data pad makes the link **full-duplex UART**: one wire each way, so
  either side can talk at any time, with no echo handling and faster speeds.
  The two data pads go to chip pins that can also do I²C, if the datasheet
  allows, so I²C stays possible later. I²C wasn't chosen as the default: a
  cartridge pulled out mid-message can hang an I²C bus, the Pi's hardware I²C
  handles clock stretching badly, the Pi's main I²C pins are taken (GPIO3 is
  the power button), and with I²C only the box can start a conversation.
- **The pads are spread along the cartridge's length** (2026-11-24) because
  it looks better than a tight cluster. Wide gaps also make it practically
  impossible for a pin to bridge two pads.
- **The 3V3 pad powers the cartridge's 3.3 V parts; no regulator on the
  cartridge** (2026-11-24). An e-ink screen, the chip and sensors draw only a
  few tens of mA. The box makes that 3.3 V on the slot board from its 5 V
  supply, not from the Pi's own 3.3 V rail, so it doesn't load the Pi. That's
  one regulator in the box instead of one in every cartridge, and no jumper.
  The 5V pad is for LEDs and anything else that needs 5 V.
- **The box programs cartridges in the slot** through the SWIO pad with a
  WCH-LinkE programmer (about $8) on the Pi. Chips are soldered blank;
  firmware updates also go through the slot.
- **The pad side of the PCB stays clean: no through-holes.** That bottom face
  shows. All add-on connections are surface-mount on the top. Vias are tented
  (covered with solder mask).
- **The LEDs are not on the PCB.** They sit elsewhere in the cartridge and are
  wired back to connectors on the PCB.
- **Any display would be e-ink, not LCD** (2026-11-24). E-ink has no
  backlight, and it keeps showing its image with the power off, so a cartridge
  could show its title even on the shelf. The display connector is laid out
  for a standard e-ink module (see "Connectors").
- **Flexibility over fixed functions** (2026-11-24). Every signal pin on every
  connector goes to a microcontroller pin. Any part that would lock a pin to
  one job (LED buffers, backlight switch, I²C pull-ups) gets a solder-jumper
  bypass or is left unfitted, so firmware can repurpose the pin.
- **A debug LED on the board** (2026-11-24), for bringing up new boards.
- **The cartridge interior is reworked to fit the PCB.** The internal ribs can
  be shortened or removed; a little extra flex in the faces is acceptable.
- **Spring force pushing the cartridge out is welcome.** The detent already
  takes noticeable force to pull out.
- **Pogo pins are Mill-Max 0906 spring pins** (see "Slot side").
- **Out of scope:** the multi-slot "game board" idea is a separate project,
  not a LaserTrack feature.

### Parts and layout (agreed 2026-11-24)

- **Chip: WCH CH32V006 in QFN-20, CH32V006F8U6** (LCSC C42431288, 3 × 3 mm;
  changed from TSSOP-20 on 2026-11-24 because the TSSOP's 6.4 × 6.5 mm doesn't
  fit the 6.5 mm component zone between the ledges). It has 62 KB flash, 8 KB RAM, 18 I/O and
  single-wire SDI programming, and runs from 2 to 5.5 V. Chosen over the
  CH32V003 (16 KB flash, 2 KB RAM) to have room for a screen. Chosen over the
  CH32V203 because that chip needs two programming wires. If 18 I/O turns out
  too few (see the I/O budget), a larger package of the same family is the
  fallback.
- **Pad pitch 14 mm:** 6 pads at x = ±7, ±21, ±35 mm, a 70 mm span centred on
  the cartridge.
- **PCB 81 × 7.9 × 1.6 mm** (modelled in `cad/models/cartridge_pcb.py`; see
  "Mounting the PCB"). 1.6 mm is the standard, cheapest and stiffest thickness.
  7.9 rather than 8.0 because JLCPCB's outline tolerance is ±0.2 mm. The four
  outline corners have 1 mm chamfers (Kyle, 2026-11-24), hidden under the
  lips; the slot PCB's corners get the same.
- **Every part must be in stock at JLCPCB** (Kyle, 2026-11-24). Checked when
  the BOM is made and again just before ordering; a part that isn't in stock
  gets swapped for one that is.
- **Fitted / not fitted is chosen at order time**, not in the design. Every
  footprint is on the board; the BOM sent to JLCPCB lists only the parts to
  fit. Connectors may be left off v1 to save cost.
- **Order size is decided once the design is done**, from a cost comparison
  of a small prototype run against going straight to 20+.
- **The PCB is clamped between the two cartridge halves, with no screws**
  (see "Mounting the PCB" below).
- **Vertical-entry JST-SH connectors** (BM…B-SRSS-TB), so cables leave
  upwards into the cartridge cavity rather than along the narrow strip.
- **A small PCB in the slot instead of perfboard.** The 0906 tail is 0.43 mm
  thick and needs a 0.51 mm minimum hole. Perfboard holes are about 1 mm, so
  the pins would sit crooked; a slot PCB with about 0.6 mm holes holds them
  straight. It also carries the 3.3 V regulator, power switches and the Pi
  connector, and goes in the same JLCPCB order.
- **Note: a staged rollout is possible but not planned.** The 100 kΩ resistor on RX lets a
  resistor-only "dumb" cartridge share the same pads (the box measures it with
  an ADC). With JLCPCB assembly, every cartridge can be smart from the start.

## Pads (cartridge underside)

6 gold (ENIG) pads, about 3 mm along the length × 4 mm across. The 14 mm
pitch leaves an 11 mm gap between pads, far more than the cartridge's ±0.5 mm
play along its length. The detent plungers press on the back face, not the
floor, so they don't meet the pads.

Board: cartridge PCB — logic level: 3.3 V — powered from: box 3V3 pad (logic)
and box 5V pad (LEDs, add-ons)

| Pad | x (mm) | Signal | Box side | Notes |
|---|---|---|---|---|
| 1 | -35 | 5V | Pi 5 V supply → fuse → load switch | LEDs and 5 V add-ons. At the end, next to GND only, so a bridge there is a plain short that the fuse catches. |
| 2 | -21 | GND | Pi GND | |
| 3 | -7 | TX (box → cartridge) | Pi UART TX | Cartridge RX. Also I²C SDA if switched. |
| 4 | 7 | RX (cartridge → box) | Pi UART RX | Cartridge TX. 100 kΩ to GND on the cartridge marks it present. Also I²C SCL. |
| 5 | 21 | SWIO | WCH-LinkE SWIO | Programming and debug |
| 6 | 35 | 3V3 | slot-board 3.3 V regulator → load switch | Chip, e-ink, Qwiic devices |

"TX" and "RX" are named from the box's side.

**Comms:** full-duplex UART at 115200 baud to start (about 11 KB/s each way);
it can go well over 1 Mbaud over these few centimetres if needed. Packets carry
a checksum and are retried. The box ignores the lines for about 200 ms after
contact while the pins settle.

**Safe hot-plugging:** the box keeps 3V3 and 5V off until it sees its RX line
pulled low by the cartridge's 100 kΩ, which needs GND and that pad both
connected. It then turns power on through soft-start load switches. Power
never arrives before ground, so all pins can be the same height.

## Cartridge PCB parts

**Fitted** = soldered by JLCPCB. **Not fitted** = footprint only, added later.

| Part | Fitted? | Purpose |
|---|---|---|
| CH32V006F8U6 (QFN-20, 3 × 3 mm) | Yes | Microcontroller |
| 100 nF capacitor beside each chip's power pin | Yes | Decoupling: a local charge store so the chip doesn't glitch when it draws current suddenly |
| About 10 µF on 5 V, about 4.7 µF on 3V3 | Yes | Smooth the rails for LEDs and add-ons. Kept modest because the box soft-starts power. |
| 100 Ω series resistors on TX, RX and SWIO | Yes | Limit current into the chip's pins during hot-plugging |
| ESD protection array (e.g. SRV05-4) on the pad lines | Yes | Dumps static from fingers on exposed pads to ground |
| 100 kΩ RX to GND | Yes | Presence detection with power off |
| 2× 74AHCT1G125 buffer (SC-70, 5 V supply), with bypass jumper | Yes | Level-shifts LED data to 5 V so the LEDs read it reliably. Bypass makes the pin a plain 3.3 V GPIO. |
| 330 Ω series resistor on each LED data line | Yes | Softens signal edges down the wire; protects the first LED |
| 2× 4.7 kΩ I²C pull-ups, with jumper to disconnect | Yes | I²C needs them. Open the jumper if Qwiic modules bring their own, or to repurpose the pins. |
| Debug LED + resistor on a chip pin | Yes | Firmware can blink it ("is the chip running?") |
| W25Q32JVSS SPI flash, 4 MB (SOIC-8, 150 mil: the 128 Mbit part only comes wider) | Not fitted | Image storage for a screen. One 200×200 mono e-ink image is only 5 KB, so a few fit in the chip's own flash; this is for many images or colour. |
| 6 ENIG pads, bottom | Yes | Contacts |

No regulator: 3.3 V comes from the box (see Decided).

## Connectors (top side)

All JST-SH (1 mm pitch, surface-mount, latching). They're real connectors;
"Qwiic" is just a standard pin order on a 4-pin JST-SH. The labels below are
each connector's default use. The signal pins are general-purpose chip pins
that firmware can repurpose, within what each chip pin supports and as long as
signals stay at 3.3 V.

| Connector | Pins | Default use |
|---|---|---|
| LED A | 3: 5V, DATA, GND | Addressable LEDs (WS2812B / SK6812) anywhere in the cartridge |
| LED B | 3: 5V, DATA, GND | Second chain |
| Qwiic | 4: GND, 3V3, SDA, SCL | I²C sensors, buttons, small modules; off-the-shelf modules plug in |
| Display | 8: GND, 3V3, SCK, MOSI, CS, DC, RST, BUSY (PA1 direct; the backlight MOSFET option was dropped in layout) | An e-ink module with an SPI driver board (the common 8-wire pinout). BUSY is an input that tells the chip when the panel has finished refreshing. |
| Spare pads (bare) | Whatever GPIO is left + GND, 3V3, 5V | Anything else |

**Size check.** An 8-pin vertical JST-SH is about 10 mm long and 4–5 mm deep
(exact figures from JST's datasheet at layout). On a strip about 80 mm long
and 8 mm wide (6.5 mm usable between the ledges), the four connectors take
about 30 mm along it and should fit the width; confirm with JST's drawing. The
vertical housing plus a mated plug stands about 6–7 mm tall inside the
cartridge's 62 mm cavity. The ribs are removed in `cartridge_pcb`, so nothing
else sits in that space.

**I/O budget.** The chip has 20 pins: 2 are power (VDD, GND) and 18
are I/O pins firmware can control. Each wire that carries a signal to or from
the chip uses one I/O pin:

| Use | Pins |
|---|---|
| TX, RX (pads) | 2 |
| SWIO (pad) | 1 |
| I²C SDA, SCL (Qwiic) | 2 |
| SPI SCK, MOSI (display) | 2 |
| Display CS, DC, RST, BUSY | 4 |
| LED A, LED B data | 2 |
| Debug LED | 1 |
| **Planned total** | **14** |
| Image flash later (MISO, CS) | +2 = 16 |

That leaves 2–4 pins for the bare spare pads. If more are ever needed: the
same chip comes in larger packages with more pins, chosen before the schematic
is drawn. Several jobs can also share pins (more I²C devices share the same
two Qwiic wires; SPI devices share SCK/MOSI and need only their own CS). Pin
assignments wait for the CH32V006 datasheet.

Manufacture: JLCPCB with assembly, ENIG finish, matte black mask, tented vias.
The estimate from 2026-11-21 was about $60–100 for 20 boards ($3–5 each),
including US tariffs. A longer strip barely changes the price (JLCPCB's base
price covers up to 100 × 100 mm). Get a live quote.

## Mounting the PCB

**Decided 2026-11-24: clamped between the two halves, no screws.**

Modelled in `cad/models/cartridge_pcb.py` (dimensions in `cad/params.py`,
`CPCB_*`). Across the thickness, Z = 0 at the back face, 12.5 at the front;
every Z face is a whole layer from its half's printed face:

| Feature | Z (mm) | Width | Notes |
|---|---|---|---|
| Inside between skins | 1.6 – 10.3 | 8.7 | back skin 1.6, front skin 2.2 |
| PCB pocket | 1.8 – 10.1 | 8.3 | 0.2 per side |
| PCB | 2.0 – 9.9 | 7.9 | |
| Window (between the lips) | 2.6 – 9.3 | 6.7 | lips cover 0.6 of each edge; 4 mm pads leave 1.35 each side |

- Length: the PCB spans x = ±40.5 (81 mm), pocket ±40.7. The bottom screw
  posts and their webs start at x = ±41.0. The window stops 1 mm inside the
  pocket ends.
- Lips below the PCB are 0.84 mm thick (2 lines); the groove is 1.8 mm for the
  1.6 mm board, so the pins push it up 0.2 mm against the ledges. Seated, the
  pads are 1.04 mm above the bottom face. The slot's pins stand that much
  taller; their stroke and compression don't change.
- Ledges above the PCB's long edges are 1.26 mm (3 lines) and take the pins'
  push. The back half carries the back lip and ledge, the front half the front
  ones (the seam at Z = 7.5 runs through the board). Parts zone on top: 6.2 mm
  wide (0.25 mm inside the window line), 8 mm tall, checked clear of the shell.
  At x = ±25.5 to ±34.5 the thickened skin behind the detent seats narrows it
  to 5.6 mm; the 5.2 mm deep JST connectors still fit there.
- In `cartridge_pcb` the bottom wall is replaced by the window across the
  board's length, the alignment lip/rebate stops at the board, and **all
  internal ribs are removed** (revisit after a v1 print).
- Thinnest spot: where the pocket crosses the detent seat pads (x = ±25.5 to
  ±34.5), about 1.3 mm of wall is left behind the entry ramp, backed by the
  PCB edge. Check it in section views.
- The pins push the PCB *up into* the cartridge, so a printed ledge above the
  strip takes that load.
- A thin lip of each half overlaps the pad face's long edges by about 0.5 mm,
  like a window frame, so the board can't drop out.
- Screwing the halves together clamps it. The board is held by its whole
  length, not two points.
- No holes in the PCB, so the pad face stays clean, and no countersink option
  in the JLCPCB order.
- The pads must stand clear of the lip so the pins reach them. In the model,
  the pad face sits flush with or slightly proud of the cartridge's bottom
  face.

Rejected: **two countersunk screws** up through the PCB into printed bosses.
A countersunk head sits flush, so the pins would still meet the pads. But it
puts two holes and screw heads on the visible face, leaves a thin rim on a
1.6 mm board (an M2 countersunk head is about 1.2 mm tall), and JLCPCB charges
extra for countersinks.

## Slot side

**Pins: Mill-Max 0906 spring pins, standard stroke, solder mount**
(`0906-X-15-20-7X-14-11-0`). From Kyle's copy of the Mill-Max drawing:

| Dimension | Value (mm) |
|---|---|
| Plunger Ø (tip, rounded) | 1.07 |
| Barrel Ø / press ring Ø / flange Ø | 1.5 / 1.63 / 1.83 |
| Flange to barrel top | 2.69 |
| Tail Ø × length | 0.43 × 1.75 |
| Mounting hole | 0.51 min |
| Stroke | 0.7 mid, 1.4 max (0906-8: 0.5 / 0.99) |
| Length A (flange underside to tip) | 0906-1 4.5, -2 5.0, -3 5.51, -4 5.99, -8 3.94 |
| Force | about 60 g at mid-stroke (published figure; 10–25 g initial) |

- **0906-2 (A = 5.0) for all six,** on DigiKey as
  0906-2-15-20-75-14-11-0, soldered to the slot PCB at the same x positions as
  the pads. Six pins at mid-stroke push out with about 3.5 N.
- **Seated compression: 0.76 mm** (rated mid-stroke 0.7, max 1.4), so the
  print can be about ±0.35 mm out before a pin nears either end of its
  stroke. Modelled in `cad/models/slot_pcb.py`.
- **Floor:** 3.2 mm thick (16 layers) over the slot PCB, with a 2.2 mm hole per
  pin (flange 1.83 + clearance). Free pin tips stand 1.8 mm above the floor;
  the barrel tops sit 0.5 mm below it. Pins at z = 6.15 (pad centre plus the
  0.2 mm the plungers push the cartridge forward).
- **Slot PCB mounting:** 84 × 18.6 mm, in a pocket in the slot's underside
  (0.2 mm per side, so the pocket lines the pins up with their holes). Pin
  flanges sit against the pocket ceiling. Four M3 low pan heads go up through
  the board into the 9 mm back wall at x = ±14, ±38 (4.4 mm of thread). The
  slot body is 1 mm deeper than `slot.py`'s, and parts hang under the board,
  so the slot needs taller risers in the box.
- **Slot PCB carries** (`electronics/slot_pcb.md`): the 6 pins; a 0.5 A
  polyfuse on the Pi's 5 V; a TPS22917 load switch for the cartridge's 5 V
  (soft start, output discharge); an AP2112K-3.3 regulator for the
  cartridge's 3.3 V, switched by the same enable; 1 kΩ in series with the
  Pi's TX and RX; a 1 MΩ pull-up and 10 kΩ sense line on RX for presence;
  headers to the Pi (GPIO 14/15 UART, GPIO 23 power enable, GPIO 24 sense)
  and to the WCH-LinkE.
- Contact happens as the cartridge lands on the floor, at the same moment as
  the detent click.

**Rejected:** test-probe tips (spear or crown points scratch the pads);
magnetic pogo connectors (the magnet's pull fights the detent); a card-edge
connector like the NES used (high grip force swamps the click, and it's a
known failure point); a 2.54 mm pin strip (could bridge pads).

## Rejected options

| Option | Why not |
|---|---|
| NFC (RC522 + NTAG215) | Unreliable through the printed cartridge |
| Microswitch in the slot floor | Visible, and a toddler can press it |
| Hall sensor + magnet | Detects presence only, no ID or power |
| Binary solder-jumper pads | 8–11 pins; too much spring force and too many failure points |
| 1-Wire ID chip (DS2401) | $1–2 per cartridge for an ID only |
| I²C EEPROM with factory ID | Cheap, but a microcontroller costs about the same and does far more |
| 5 pads, half-duplex UART | Replaced by 6 pads (full duplex), 2026-11-24 |
| I²C as the box–cartridge link | Hot-plug hangs, the Pi's clock-stretching problem, pin conflict, box-only initiation (see Decided); still possible on the same pads |
| 3.3 V regulator on each cartridge | The box supplies 3.3 V; one regulator in the box instead of one per cartridge |
| LCD display with backlight | E-ink chosen; backlight MOSFET left unfitted |
| Countersunk screws through the PCB | Holes and screw heads on the visible pad face; clamping between the halves instead |

## Open

- Routing the cartridge board (the slot board is routed, 2026-11-25), then
  Gerbers, BOM and placement files for JLCPCB.
- The slot PCB's Pi header pins hang 8.4 mm under the slot, plus dupont
  plugs: the box risers need about 15 mm, or switch to right-angle headers.
- JLCPCB stock and LCSC numbers for every part (only the CH32V006F8U6,
  C42431288, is filled in so far).
- Routing for the LED and display wires inside the cartridge shell.
- Risers for the deeper `slot_pcb` in the box; `box.py` still uses `slot.py`.
- Check one pin with calipers when they arrive.
- Cartridge firmware: a PlatformIO project in `firmware/` (ch32v003fun
  toolchain or WCH's SDK). The box protocol: ID, LED commands, storage, updates.
- E-ink module choice, if and when.
