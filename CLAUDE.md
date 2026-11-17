# LaserTrack

A personal hardware project: a TV set-top box that accepts NFC cartridges.
The box and the cartridges are 3D printed; the electronics are off-the-shelf
dev boards (Arduino / ESP32 / Raspberry Pi) wired to breakout boards. No custom
PCBs for now.

It combines scheduled TV channels (like FieldStation42) with cartridges that
play a specific movie, show or playlist (like 240-MP's NFC cards). The
cartridge is the centrepiece and must fit a cassette case. Requirements and
open questions are in `docs/product.md`; read it before design work. Do not
invent requirements; ask.

## Layout

| Folder | Contents |
|---|---|
| `cad/` | build123d (Python) models. `params.py` holds every shared dimension. |
| `firmware/` | PlatformIO project (not created yet). |
| `electronics/` | Pin-map tables in Markdown; KiCad only if a circuit outgrows a table. |
| `docs/` | `product.md` is the product brief; `decisions.md` logs what was decided and why. |
| `vendor/` | Downloaded STEP models and datasheets for bought parts. |

## CAD

- Models are code, written with build123d. Units are millimetres.
- Any dimension shared between two parts (cartridge and slot, board and
  mounting posts) lives in `cad/params.py` and is imported, never retyped.
- Mating parts use `FIT_CLEARANCE` from `params.py` (per side).
- Each model script exports STEP to `cad/out/` and prints its bounding box and
  volume. Check those numbers against the intent before saying a model is done.
- Kyle views models by opening the STEP in FreeCAD and slices in Bambu Studio.
- Printer: Bambu Lab H2D (dual nozzle, 0.4 mm). No separate printer-facts file.

Commands, run from `cad/`:

```bash
uv sync                                   # install Python 3.12 + build123d
uv run python models/tolerance_gauge.py   # build one model
```

Python is pinned to 3.12 because the CAD kernel has no builds for 3.13+.

## Electronics

Document wiring as a pin-map table (see `electronics/README.md`). Always state
the logic voltage of each board and the power source of each rail.

## Working agreements

- Record every real decision in `docs/decisions.md` with the reason.
- Kyle's cross-project preferences are in `~/.claude/CLAUDE.md`.
