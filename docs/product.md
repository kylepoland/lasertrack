# LaserTrack — product brief

Status: requirements captured from Kyle on 2026-11-16; software and
electronics direction added 2026-11-18. Cartridge and slot are modelled.
Software v1 running on the Pi since 2026-11-20: channels and Plex cartridges
(simulated tag) verified on the CRT. No wiring is built (RC522 not yet
connected).
Items marked **Open** are not decided.

## What it is

A device for watching TV and movies from Kyle's own library that behaves like
old television rather than a streaming menu. It does two things:

1. **Channels.** Turn it on and it is already playing scheduled channels you
   flip through, like broadcast TV.
2. **Cartridges.** Insert a physical cartridge and it plays what that
   cartridge stands for: a movie, a show, a playlist, or any piece of media.

The cartridge is the centrepiece. If only one thing is excellent, it is the
feel of holding, inserting and watching a cartridge.

## Form factors

- **Set-top box** that plugs into a TV.
- **All-in-one TV**: a screen with the box built in. This may come later, or
  first.

Requirement: parts are portable between form factors. The cartridge receptacle
in particular is a self-contained module (slot, NFC reader mount, any contact
pins) with a defined mounting interface, so the same model drops into the box
or the TV.

## Reference projects

LaserTrack is a combination of two existing open-source projects. Both run on
a Raspberry Pi under Linux and both play video with mpv.

| | FieldStation42 | 240-MP |
|---|---|---|
| What it gives us | Scheduled TV channels | Simple VCR-style media player, with NFC |
| Stack | Python, mpv | C++/Qt6 + QML, mpv |
| Media | Local folders per channel; mkv supported; network storage can be linked | Local files, Plex, Jellyfin, Emby; mkv supported |
| Control | Keyboard/IR via Flirc, web remote, REST API on port 4242, socket file | Keyboard, USB remotes, gamepads (7 actions) |
| NFC | None | PN532 USB or ACR122U; each card maps to content via a text file |
| Useful hook | `POST /player/break-in` plays a file then returns to the channel | Cards can be written from the UI |
| Licence | MPL-2.0 | GPL-3.0 |

Sources: https://github.com/shane-mason/FieldStation42 and
https://github.com/anthonycaccese/240-MP (read 2026-11-16).

Principle taken from 240-MP: navigation is not complicated. Few options, few
buttons, no deep menus.

## Software

Decided 2026-11-18 (option (a) of the three considered; see `decisions.md`).

- **FieldStation42 runs the channels, unmodified.**
- **A small LaserTrack daemon (Python) runs everything else**: it reads the
  NFC reader, buttons, knob and IR receiver; switches between CHANNELS and
  CARTRIDGE mode; plays cartridges with its own mpv; drives the small screen
  and on-screen text.
- **The daemon owns all input.** The same button means different things per
  mode (Ch ▲ changes channel, or skips to the next episode), so FS42 and mpv
  never read keys directly.
- **Mode switching:** inserting a cartridge stops FS42's player and starts the
  cartridge; pulling it out (or Stop) returns to channels, which pick up
  whatever is scheduled now. A short "tape loading" clip covers the gap.
- **No menus on the TV.** On-screen text is passive and VCR-style (`▶ PLAY`,
  `CH 03`, loading screens), in the spirit of 240-MP. Cartridges are assigned
  from a small web page on the LAN, opened on a phone: insert a blank
  cartridge, the TV shows `UNASSIGNED CARTRIDGE`, pick its media on the page.
- **Plex for cartridges only** (see Media).
- **v1 (2026-11-19)** covers channels, cartridges through Plex, the
  assignment page and NFC. Not yet: buttons, knob, IR, LCD, DIP switch,
  loading clip. See `software/README.md`.

## Media

- Library lives on Kyle's NAS, exposed as a network share. Files are `.mkv`
  Blu-ray rips (mostly H.264 at 20–40 Mbps; some older discs may be VC-1 or
  MPEG-2, which the Pi 4 cannot decode in hardware).
- A Plex server also runs on the NAS, with hardware transcoding (Kyle,
  2026-11-19). Kyle currently watches over Wi-Fi with Plex transcoding down
  for the CRT.
- **Share:** SMB, `//192.168.1.157/storage`. The box mounts only its `media`
  folder, **read-only** (decided 2026-11-19, see `decisions.md`).
- **Cartridges play through Plex** (decided 2026-11-18), so they share Plex's
  Continue Watching with Kyle's phone:
  - Movie: start at Plex's saved position; report progress every ~10 s and
    "stopped" when the cartridge is pulled. Plex marks it watched at 90%.
  - Show: play Plex's On Deck episode for that show, then continue to the next.
  - Playlist or collection: the box remembers which item is current (Plex
    playlists don't); each item's position still comes from Plex. Shuffle is
    a per-cartridge option.
  - Quality follows the output switch: composite asks Plex for a ~480p
    transcode; HDMI direct-plays (or a 720p/1080p transcode on Wi-Fi).
- **Channels read the share directly**, as FS42 expects, and must not touch
  Plex watch history.
- **No duplicate library.** Kyle does not want transcoded copies of the
  library just for the channels; disk space is expensive.
- ~~How channels get playable quality without copies.~~ Measured 2026-11-19:
  the Pi 4 plays the raw files (H.264, 4K HEVC, and VC-1 in software) with
  0% dropped frames on composite once `mpv.conf` uses `profile=fast` and
  `hwdec=v4l2m2m-copy,drm`. VC-1 (72 files) is marginal. See `decisions.md`.
- **Open:** Ethernet or Wi-Fi; Kyle will try both.

## Cartridge

Requirements:

- Looks and feels good; this is the priority over everything else.
- Fits inside a standard audio cassette case.
- The case carries a printed J-card.
- Printed in two halves, top and bottom, screwed together.
- Hex-socket screws visible on the top face as a design element.
- NFC tag sealed inside.
- Optional internal weights for heft.
- Optional contact pins that take power from the box to light one or more
  LEDs in the cartridge while it plays. Subtle, not distracting.
- Material: matte PLA, printed on the H2D.

Measured (2026-11-17): Kyle's cases are 103 x 64 x 14 mm inside, with
pegless trays. The cartridge is 101 x 62 x 12.5 mm (see `decisions.md`).

- Inserts into the box **long edge first**, about 1/3 in, label facing the
  user. The J-card carries the portrait poster; the cartridge label is a
  landscape version.
- M3 x 6 hex-socket screws, heads on the front (label) face.
- Light effects through cartridge contacts and box pogo pins are wanted
  later; not designed yet.

**Open:**

- ~~What a cartridge stores.~~ Decided 2026-11-18: only the tag's UID; the box
  holds the UID-to-media table, so cartridges can be reassigned without
  rewriting.
- ~~NFC tag type.~~ Decided 2026-11-18: NTAG215 stickers (Kyle's existing
  stock; read and written with the RC522 already). Sticker size to be measured.
- Screw size and whether threads are heat-set inserts or cut into the plastic.
- Weight material and target mass.
- LED: whether to do it at all in V1; contact style (pogo pins on the box
  against pads on the cartridge is the usual approach); colour and behaviour.
- ~~How the cartridge is retained and how insertion feels.~~ Decided
  2026-11-18: end tracks on rails, plus spring ball plungers clicking into
  seats on the back face (see `decisions.md`). Feel still to be tuned on a print.
- How much of the cartridge stays visible when inserted, which decides
  whether a J-card-style label or the LED is seen during playback.
- J-card template size and how it is printed.

## Controls

Decided 2026-11-18:

| Control | TV (channels) mode | Cartridge mode |
|---|---|---|
| Power | Safe shutdown / wake | same |
| Play/Pause | (none, or mute) | Pause / resume |
| Stop/Eject | (none) | Stop, save position to Plex, back to channels; Play resumes |
| Ch ▲ / Ch ▼ | Change channel | Next / previous episode (or seek in a movie) |
| Volume knob (rotary encoder) | Volume; press to mute | same |

- Buttons and knob are wired to Pi GPIO and read by Linux's kernel drivers
  (`gpio-keys`, `rotary-encoder`), which work on interrupts and don't drop
  presses while the Pi is busy decoding.
- **IR receiver is in V1** (hardware and input handling). Which remote to use
  (an old VCR remote, a bought one, or a custom printed one) is worked out later.
- **Open:** button type (tactile feel matters); whether Stop stays or pulling
  the cartridge is enough (4 buttons instead of 5).

## Hardware

Decided 2026-11-18 unless marked Open. Wiring goes in `electronics/` as pin maps.

| Part | Role | Notes |
|---|---|---|
| Raspberry Pi 4 (Kyle's) | Main board; runs FS42 and the daemon | 3.3 V logic. Only board in V1 |
| RC522 NFC reader (Kyle's) | Reads cartridge tag UID | SPI, 3.3 V, wired straight to the Pi |
| 1.54" 240×240 IPS LCD (ST7789, SPI) | Cover art and progress in cartridge mode; channel number in TV mode | LCD rather than OLED: no burn-in from a channel number shown for hours. Shares SPI with the RC522 |
| 5 push buttons + EC11 rotary encoder with push | Controls above | |
| IR receiver (TSOP38238) | Remote, later | Needs a window on the front panel |
| Output-select DIP switch | HDMI or composite, read at boot | See Video output |
| Power button on GPIO3 | Safe shutdown and wake | Pulling power can corrupt the SD card |
| Heatsink + 30 mm 5 V fan | Cooling in a closed box | Pi switches the fan by temperature |
| Panel-mount USB-C, HDMI, Ethernet, RCA jacks | Back panel | RCA wired from the Pi's 4-pole AV jack (Pi pinout differs from camcorder cables) |
| Official Pi 5 V 3 A USB-C supply | Power for everything | |

- **No microcontroller in V1.** A Raspberry Pi Pico is added later only if the
  cartridge LEDs become colour effects (see `decisions.md` for why).
- **NFC placement:** range drops near metal, and the slot's steel ball plungers
  sit 30 mm either side of centre. Test-read through a printed cartridge and
  slot before fixing the reader mount.

### Video output

- **One TV at a time.** HDMI to a modern TV, or the Pi's own composite out to
  the CRT (better on a CRT than an HDMI-to-composite converter).
- **A DIP switch on a GPIO pin selects the output at boot**, using a
  conditional section in the Pi's `config.txt` (`[gpioN=1]`), read by the
  firmware before Linux starts. The daemon reads the same pin to pick Plex
  quality. Flipping it needs a reboot. Spare switch positions are available
  for later (e.g. NTSC/PAL, 240p/480i).

## Scope

V1 is the set-top box with on-box buttons, IR receiver, channels, and
cartridge playback. Not in V1: the remote itself. Not decided for V1:
cartridge LEDs, the all-in-one TV.
