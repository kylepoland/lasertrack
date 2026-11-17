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

## Open questions

- What the box does, which board drives it, and which NFC reader it uses.
- Cartridge size and how it is retained in the slot.
