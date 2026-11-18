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

## 2026-11-17 — Cartridge front face, second pass

- **Label is a plain wide shape with no screw notches.** The notched outline
  was fiddly to cut and apply. Top and bottom edges now stop 1.5 mm short of
  the counterbores; top corners are bevelled parallel to the outer bevel;
  1 mm corner radius so sticker corners don't lift. Sticker is 92.4 x 38.4 mm,
  about 2.4:1, which happens to match the 2.39:1 cinemascope ratio.
- **Top band carries an engraved "LASERTRACK"** (6.5 mm Arial Bold); **bottom
  bar carries fake cassette text** ("HI-FI · 120 MIN", 3.5 mm). Engraved
  0.6 mm deep. The bottom bar sits inside the slot when inserted, so it is
  only seen in the hand.
- **Outer top bevel increased from 7 to 9 mm** for more presence.
- **Screws moved to 9 mm from the ends** (7 mm from top/bottom) so the top
  counterbores keep about 2 mm of wall against the bigger bevel.

## 2026-11-18 — Cartridge as thin shells with posts and an alignment lip

Supersedes the solid halves and back pocket from the first pass.

- **Walls are whole multiples of the 0.42 mm line width** (H2D, 0.4 mm
  nozzle): outer walls 5 lines (2.10), seam skirt 3 lines (1.26), lip 2
  lines (0.84), counterbore bosses 3 lines (1.26), insert posts 4 lines (1.68,
  inserts need about 1.5 mm to grip). Face skins are 8 layers (1.6 mm).
  Plastic per cartridge dropped from about 54 to 25 cm^3; the 9.3 mm interior
  is free for the NFC tag and weights.
- **Why these thicknesses, given the slicer hollows thick walls.** Bambu
  Studio's standard profile prints 2 wall loops and fills anything thicker with
  sparse infill (about 15%). Every wall here is 5 lines or fewer, so it prints
  as perimeters only, effectively solid; the 1.6 mm skins equal the default 3
  bottom + 5 top shell layers, so they are solid too. Making walls thicker in
  CAD would add infill, not strength. The skirt went from 2 to 3 lines and the
  outer wall from 4 to 5 because the seam edge takes knocks every time the
  cartridge goes into the slot.
- **Screw joint near the front face.** Bosses hang from the front skin around
  each counterbore; posts rise from the back skin to meet them 4.4 mm below the
  face. The heat-set insert sits at the top of the post, so the screw only
  crosses a 1.2 mm floor under its head and 4.8 mm of it is in the insert.
- **Lip and rebate at the seam.** The back wall's inner half stands up as a
  2 mm lip; the front wall's inner half is cut away 2.2 mm deep so the lip
  slides in behind a 1.26 mm outer skirt. 0.1 mm clearance per side for a snug
  press that holds without screws (`FIT_CLEARANCE` 0.2 would slide). The lip
  stops around the corner bosses and behind the grip ribs, where the wall
  stays full thickness.
- **Grip grooves reduced to 0.8 mm deep** so 3 lines (1.30 mm) of wall remain behind them.
- **Orthographic close-up renders** (`render.py --focus`) are used to check
  sections through the joint.

## 2026-11-18 — Low pan-head screws; QC before hand-off

- **Screws are Kyle's M3 x 6 low pan heads: 5.8 mm head, 0.9 mm tall.**
  Counterbore is 6.2 mm (head + `FIT_CLEARANCE` per side) and 1.1 mm deep, so
  the head sits 0.2 mm below the face. The earlier 3.2 mm counterbore was sized
  for socket head cap screws and was far too deep.
- **The joint moved up to 2.3 mm below the face.** Posts now rise 8.6 mm from
  the back skin into the front half; the screw crosses a 1.2 mm floor and has
  4.8 mm of thread in the M3 x 4 insert. Insert hole is 5.5 deep (0.7 below
  the screw tip).
- **QC rule.** A text-placement error (both engraved lines stacked in the
  middle) reached Kyle because only some views were re-rendered after a
  rewrite. Before handing off any model: clear `cad/out/renders/`, rebuild,
  render every view of every part, look at all of them, and confirm the
  printed checks pass. The cartridge script now asserts that each engraved
  line sits clear of the label.

## 2026-11-18 — Print orientation corrected

- **Front half prints face up; back half prints back-face down.** The earlier
  note ("each half face-down, no supports") was wrong for the front half:
  face-down, the label recess, engraving and counterbores are pockets on the
  plate whose ceilings bridge over air, and the 92 x 38 mm label pocket (only
  0.4 mm deep) would sag. Face up, those features are top surfaces and the
  label floor comes out flat for the sticker. The hidden underside (skin and
  bosses) takes tree supports from the build plate.
- **Slicer:** import the two STEP files (not the assembly, not STL), Bambu
  Studio's 0.20 mm Standard profile for the H2D, matte PLA, textured PEI plate.
  Supports on for the front half only: tree (auto), on build plate only. Check
  the preview that no support lands in the 2.2 mm rebate at the seam; paint a
  support blocker there if it does. Keep elephant-foot compensation on (it
  protects the 0.1 mm lip clearance).

## 2026-11-18 — Both halves print face-down; test screws go into PLA

Supersedes "Print orientation corrected" above.

- **Front half prints face-down, with support only in the label recess.** Kyle
  has printed a cartridge with a label recess this way (support in the recess)
  and it worked; it also puts the textured-plate finish on the show face.
  The engraving (0.6 mm, small letter spans) bridges without support.
- **Counterbores print face-down without support** using bridge layers: the
  first layer over the counterbore leaves a slot the width of the clearance
  hole, the next leaves a square, then the round hole continues. Each layer
  bridges onto solid material. For this to line up with real layers the
  counterbore is a whole number of layers: 1.2 mm (head 0.3 mm below the face).
  The model asserts that every feature cut into the face is whole layers.
- **Test prints screw straight into PLA** (`SCREW_MODE = "pla"`, 2.6 mm pilot
  hole, 2.4 mm of post wall around it). Final cartridges switch to
  `"insert"` (4.0 mm hole for M3 x 4 heat-set inserts). Posts are sized for
  the insert in both modes, so switching never changes the outside.
- **Slicer:** import the two STEP files, flip the front half face-down. Support
  on, on build plate only; if it doesn't put support in the label recess,
  paint a support enforcer on the recess. No support needed anywhere else.

## Open questions

See the **Open** items in `product.md`. The biggest are how the two reference
projects are combined, the main board, and the cartridge's internal layout
within a cassette's 12 mm thickness.
