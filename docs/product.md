# LaserTrack — product brief

Status: requirements captured from Kyle on 2026-11-16. Nothing here is built.
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

**Open:** how the two are combined. The options are (a) run FieldStation42 for
channels and add cartridge handling on top through its API, (b) run 240-MP and
add channels, (c) write a small LaserTrack program that drives mpv directly
and borrows ideas from both. This is the main software decision.

## Media

- Library lives on Kyle's NAS, exposed as a network share. Files are `.mkv`.
- A Plex server also runs on the NAS. Current intent is to skip Plex and read
  the share directly. **Open:** confirm. Reading the share is simpler and both
  reference projects can play local/mounted files; the cost is no Plex
  metadata, artwork or transcoding.
- **Open:** share protocol (SMB or NFS), and whether every `.mkv` plays on the
  chosen board without transcoding (depends on video codec, e.g. H.264 vs
  HEVC vs AV1).

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

Constraints to verify by measuring a real case with calipers:

- A cassette is about 100 x 64 x 12 mm; the cartridge must be no larger.
- Cassette cases have two hub pegs that sit in the tape reels. The cartridge
  needs matching holes or recesses, or the cases need pegless trays.
- 12 mm total thickness has to hold both shell walls, the NFC tag, screw
  heads and threads, weights, and any LED and contacts.

**Open:**

- What a cartridge stores. Likely just the tag's ID, with the box holding the
  ID-to-media mapping (240-MP's approach), so cartridges can be reassigned.
- NFC tag type and size (sticker, coin, card).
- Screw size and whether threads are heat-set inserts or cut into the plastic.
- Weight material and target mass.
- LED: whether to do it at all in V1; contact style (pogo pins on the box
  against pads on the cartridge is the usual approach); colour and behaviour.
- How the cartridge is retained and how insertion feels (detent, magnet,
  spring, click).
- How much of the cartridge stays visible when inserted, which decides
  whether a J-card-style label or the LED is seen during playback.
- J-card template size and how it is printed.

## Controls

- Buttons on the box: play/pause, volume, channel, and whatever else proves
  necessary. Keep the count low.
- Remote control: wanted eventually, not in V1.
- **Open:** exact button list, button type (tactile feel matters), and
  whether buttons reach the software as a USB keyboard (both reference
  projects accept keyboard input) or through GPIO.

## Hardware (all open)

- Main board. Both reference projects target Raspberry Pi; a Pi 4 or 5 is the
  natural candidate.
- NFC reader. PN532 is what 240-MP supports; placement relative to the tag is
  a mechanical constraint on the receptacle (range is a few centimetres and
  drops near metal, including metal weights).
- A microcontroller for buttons and cartridge LEDs, if the Pi does not handle
  them directly.
- Video and audio output: HDMI to a modern TV, or a CRT.
- For the all-in-one TV: screen type and size.

## Scope

V1 is the set-top box with on-box buttons, channels, and cartridge playback.
Not in V1: remote control. Not decided for V1: cartridge LEDs, the all-in-one
TV.
