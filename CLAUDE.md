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
| `software/` | Python for the Raspberry Pi: the LaserTrack daemon, Pi setup scripts. See its README. |
| `electronics/` | Pin-map tables in Markdown; KiCad only if a circuit outgrows a table. |
| `docs/` | `product.md` is the product brief; `decisions.md` logs what was decided and why. |
| `vendor/` | Downloaded STEP models and datasheets for bought parts. |

## CAD basics

- Models are code, written with build123d. Units are millimetres.
- Any dimension shared between two parts (cartridge and slot, board and
  mounting posts) lives in `cad/params.py` and is imported, never retyped.
  Derive dependent values there (e.g. counterbore from the screw head) rather
  than hard-coding the result.
- Each model script exports STEP to `cad/out/`, prints its bounding box and
  volume, and prints the checks that matter for that part (wall thicknesses,
  screw engagement, overlap between mating parts). Put `assert`s on anything
  that can silently go wrong (text placement, whole-layer depths, zero overlap).
- Kyle views models by opening the STEP in FreeCAD (close and reopen to see a
  rebuild; FreeCAD does not reload) and slices in Bambu Studio.

Commands, run from `cad/`:

```bash
uv sync                                   # install Python 3.12 + build123d
uv run python models/cartridge.py         # build one model
uv run python models/slot.py              # slot (imports and checks against the cartridge)
uv run python models/box.py               # set-top box (imports the slot and cartridge; ~15 s)
```

The box build fails if any two parts overlap, printed or bought (bought
parts are modelled as stand-ins: Pi, screen, button board, encoder, reader,
jacks). Its section cuts use plane `split`, not box intersections, which hung
OpenCascade on the bottom shell.

Python is pinned to 3.12 because the CAD kernel has no builds for 3.13+.

## Designing for the printer

Printer: Bambu Lab H2D, 0.4 mm nozzle, 0.20 mm layers, matte PLA, textured
PEI plate. `LINE_WIDTH` (0.42) and `LAYER_HEIGHT` (0.2) are in `params.py`.

- **Decide each part's print orientation before designing its features**, and
  write it in the model's docstring. Most mistakes so far came from features
  that only work in the other orientation.
- **Walls are whole multiples of `LINE_WIDTH`; skins and face-cut depths are
  whole multiples of `LAYER_HEIGHT`.** The slicer then lays full lines and
  layers with no thin gap-fill, and features line up with real layers.
- **The slicer hollows thick walls.** Bambu Studio's standard profile prints
  2 wall loops per side and fills anything thicker with ~15% sparse infill, so
  walls of 5 lines or fewer print solid and thicker CAD walls only add infill,
  not strength. Skins: default is 3 bottom + 5 top layers (1.6 mm solid).
  Use thin shells, then thicken only where something takes load or wear
  (edges that rub a slot, posts that take screws).
- **Features cut into the face that sits on the plate are pockets whose
  ceilings bridge over air.** Small ones (engraved text) bridge fine. Large
  ones need support, and the slicer only generates it if the pocket is deep
  enough: a 0.4 mm label recess got none, 1.0 mm gets support.
- **Counterbores on the plate face need no support** if two one-layer bridge
  layers sit under them: first a slot the width of the clearance hole, then a
  square, then the round hole. The counterbore depth must be whole layers.
- **Edges on the plate get chamfers, not fillets**; a fillet there starts with
  an overhang.

## Fits and hardware

- Clearances are per side:
  - `FIT_CLEARANCE` (0.2) for printed parts that slide together (cartridge in
    the box slot, screw head in its counterbore).
  - `LIP_CLEARANCE` (0.1) for alignment lips meant to press together and hold.
  - Containers bought off the shelf (the cassette case) get about 1 mm, so
    the part drops in and lifts out.
  - Fits are a guess until printed; tune the param, never the geometry.
- **Two-part shells** use posts from one half meeting bosses on the other, and
  a lip on one half that slides into a rebate on the other. Check the overlap
  volume between halves is exactly zero.
- **Never assume hardware dimensions.** Ask Kyle what he has and use measured
  values (the screws are low pan heads, 5.8 x 0.9 mm, not the socket heads
  first assumed). Record them in `params.py` with a note that they were measured.
- **Screw mode is a switch** (`SCREW_MODE`): test prints screw M3 straight
  into a 2.6 mm pilot hole in PLA; final parts use heat-set inserts. Posts are
  sized for the insert either way, so switching never changes the outside.

## QC before hand-off, every time

1. Delete `cad/out/renders/*.png`, rebuild, and confirm the printed checks pass.
2. Render every view of every part, plus orthographic section close-ups of
   joints (`--focus X,Y,Z,WIDTH`, optionally `--view front`). `cad/qc_renders.sh`
   runs the full set (cartridge, slot, box, ~130 images). The box is modelled
   Z up with the front at -Y, so its renders pass `--zup`; `part.stl@#rrggbb`
   sets a part's colour. The cartridge and slot commands, for reference:

   ```bash
   r() { uv run python render.py "$@" >/dev/null; }   # a function, not $VAR: zsh won't split it
   r cartridge out/cartridge_front.stl out/cartridge_back.stl
   r cartridge_exploded out/cartridge_front.stl:20 out/cartridge_back.stl
   r front_half out/cartridge_front.stl
   r back_half out/cartridge_back.stl
   r section_top out/cartridge_section_top_front.stl out/cartridge_section_top_back.stl --focus 35.6,25.2,6.25,16
   r section_bottom out/cartridge_section_bottom_front.stl out/cartridge_section_bottom_back.stl --focus 44.7,-25.2,6.25,16
   r back_detent out/cartridge_back.stl --focus 30,-25,0,20 --view back
   r back_track out/cartridge_back.stl --focus 50.5,-22,4,24
   # Slot: modelled Y-up in the cartridge frame, so pass --yup for the full views.
   r slot out/slot.stl --yup
   r slot_assembly out/slot.stl out/slot_plunger.stl out/cartridge_front.stl:0.2 out/cartridge_back.stl:0.2 --yup
   r slot_exploded out/slot.stl out/slot_plunger.stl out/cartridge_front.stl:0,45,0.2 out/cartridge_back.stl:0,45,0.2 --yup
   S=out/slot_section
   r slot_section_plunger ${S}_plunger_slot.stl ${S}_plunger_plunger.stl ${S}_plunger_front.stl ${S}_plunger_back.stl --focus 30,-24,2,22
   r slot_section_rail ${S}_rail_slot.stl ${S}_rail_plunger.stl ${S}_rail_front.stl ${S}_rail_back.stl --focus 48,-21,5,16 --view top
   ```

   With this many images, tile them into contact sheets (matplotlib) to look at
   them all, then open single images where something looks off.

3. Confirm every PNG is newer than the STL it came from. A failed render
   command leaves old images that look like a pass.
4. Look at every image, not just the area that changed. Rewrites break
   untouched features.

## Handing off to Bambu Studio

- Import each part's STEP (not the STL, not the assembly). In the import
  dialog keep Linear Deflection 0.003 and set Angle Deflection to 0.2 so small
  holes aren't faceted.
- Lay each part in the orientation its docstring states (F, then click the
  face).
- Support: on build plate only; if the slicer skips a recess that needs it,
  paint a support enforcer. Keep elephant-foot compensation on; it protects
  tight fits at the seam.
- Kyle's printed experience outranks theory. When he cites something that
  worked on a real print, follow it and design to make it work.

## Electronics

Document wiring as a pin-map table (see `electronics/README.md`). Always state
the logic voltage of each board and the power source of each rail.

## Working agreements

- Record every real decision in `docs/decisions.md` with the reason.
- Kyle's cross-project preferences are in `~/.claude/CLAUDE.md`.
- Printables blocks automated fetching; ask Kyle to paste details from a
  Printables page instead.
