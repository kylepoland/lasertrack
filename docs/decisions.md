# Decisions

Newest at the bottom. Each entry: what was decided, and why.

## 2026-11-16 — Toolchain

- **CAD is code, using build123d.** Parametric, free and open source, and the
  box and cartridges can share dimensions from one file so they stay
  compatible. Claude can write and check the models directly.
- **FreeCAD is the viewer.** Exported STEP files are opened in FreeCAD for
  inspection. FreeCAD was the first choice for modelling by hand; code CAD was
  chosen instead because it lets Claude do more of the work.
- **Bambu Studio is the slicer.** It imports STEP directly and supports the H2D.
- **Rejected:** Fusion 360 Personal (10-document cap, non-commercial licence),
  Onshape Free (designs are public), Blender (not parametric).

## 2026-11-16 — Electronics

- **Dev boards and breakouts only; no custom PCBs yet.**
- **Wiring is documented as pin-map tables in Markdown.** KiCad 10 is the
  fallback if a circuit gets too complicated for a table.
- **Wokwi** is available for simulating firmware and wiring before buying parts.
- **PlatformIO** for firmware, because it runs from the command line.

## 2026-11-16 — Project structure

- **One repo per project under `~/code/`**, with `cad/`, `firmware/`,
  `electronics/`, `docs/`, `vendor/`.
- **Knowledge lives in four places:** `~/.claude/CLAUDE.md` (Kyle's preferences
  across projects), `CLAUDE.md` here (this project), skills (procedures), and
  this file (decisions).
- **Skills are written after the work has been done once**, not up front. The
  first candidate is a "printable CAD" skill after the first real part prints.
- **No printer-facts file.** The H2D is consistent enough that a single
  `FIT_CLEARANCE` in `cad/params.py` is sufficient. A tolerance gauge model
  exists and can be printed if a fit turns out to matter.

## 2026-11-16 — Product direction

Full requirements are in `product.md`.

- **LaserTrack combines scheduled TV channels (FieldStation42) with
  cartridge-triggered playback (240-MP).** Kyle wants both behaviours in one
  device.
- **The cartridge is the centrepiece.** Its look and feel take priority.
- **Cartridges fit a standard cassette case, with a printed J-card.** Two
  screwed halves, visible hex screws on top, NFC tag inside.
- **Parts must be portable between a set-top box and an all-in-one TV.** The
  cartridge receptacle is designed as a standalone module for that reason.
- **V1 uses buttons on the box; the remote comes later.**
- **Navigation stays simple**, following 240-MP.
- **Print material is matte PLA.**
- **Leaning towards reading the NAS share directly and skipping Plex.** Not
  final.

## 2026-11-17 — Cartridge, first pass

Model: `cad/models/cartridge.py`, dimensions in `cad/params.py`.

- **Long-edge insertion, landscape label (N64-style).** Short-edge insertion
  with 2/3 sticking out would look odd. The portrait poster goes on the J-card;
  the cartridge gets a horizontal version of the art.
- **Envelope 101 x 62 x 12.5 mm**, from the measured inside of Kyle's cases
  (103 x 64 x 14, pegless trays). 1.0 mm clearance per side on length and
  height so it drops in and lifts out freely; 0.3 mm allowed for the J-card,
  then 0.6 mm per face. `FIT_CLEARANCE` (0.2) is for printed parts that mate,
  such as the cartridge in the box slot, not for the case.
- **Provisional insertion depth 22 mm** (about 1/3 in, 2/3 visible). Will be
  revisited when the NFC reader position and the slot are designed.
- **Two halves split parallel to the face**: front 5 mm (label recess, screw
  heads), back 7.5 mm (threaded inserts, pocket for NFC tag and weights).
- **M3 x 6 socket head cap screws from the front, into M3 x 4 heat-set
  inserts** in the back half. Inserts because machine screws strip PLA after a
  few cycles. Heads sit 0.2 mm below the face in counterbores.
- **Bevelled top corners (7 mm) mark which way is up**; bottom corners rounded.
- **Perimeter edges are chamfered, not filleted**, so the edge on the build
  plate prints without an overhang. Each half prints face-down.
- **Label recess 0.4 mm deep with notches around the screws.** The sticker
  outline is exported as `cad/out/cartridge_sticker.svg` for the H2D cutter,
  0.3 mm smaller per side than the recess.
- **Grip ribs**: four grooves on each end, above the slot line.
- **Renders for checking models**: `cad/render.py` (PyVista/VTK, dev
  dependency) writes PNGs so Claude can inspect models without FreeCAD.

## Open questions

See the **Open** items in `product.md`. The biggest are how the two reference
projects are combined, the main board, and the cartridge's internal layout
within a cassette's 12 mm thickness.
