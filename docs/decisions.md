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

## 2026-11-18 — Label recess 1.0 mm deep

- **Recess deepened from 0.4 to 1.0 mm (5 layers).** At 0.4 mm Bambu Studio
  generated no support in the face-down recess. The ESPHome cartridge player
  on Printables, which Kyle has printed successfully, uses a 1 mm recess and
  the slicer supports it. With the default 0.2 mm support gap, 1 mm leaves
  room for real support layers.
- **Front skin is now 2.2 mm** (`LABEL_DEPTH + SKIN_UNDER_LABEL`), keeping
  1.2 mm of solid face under the label. Interior cavity drops from 9.3 to
  8.7 mm. The sticker now sits about 0.8 mm below the frame, which also
  protects its edges.

## 2026-11-18 — Screw layout, bottom text, internal ribs

- **Every screw is equidistant from its two nearest edges.** Kyle's call, for
  looks. Top pair: 7 mm from the top edge and 7 mm from the bevel, which moves
  them in to 11.9 mm from the ends (closer to the centre line). Bottom pair:
  centred in the bottom bar, 5.8 mm from the bottom and 5.8 mm from the ends.
  The label now sits a uniform 11.6 mm (`LABEL_BAND`) in from the top edge,
  bevels and bottom edge.
- **Bottom text 3.5 -> 6.5 mm.** At 3.5 mm Arial Bold strokes are ~0.45 mm, about
  one line with a 0.4 mm nozzle, and printed badly. Strokes scale at ~0.13 x
  the font size, so 6.5 mm is the smallest that gives two-line (0.84 mm)
  strokes. Same as the brand line, which prints well. The cartridge script now
  measures the strokes and fails if more than 25% of the ink is under 0.84 mm.
- **Two internal ribs** (3 lines, 1.26 mm) across the short direction at
  x = +/-22, from the back skin to 0.2 mm under the front skin. Pressing either
  face lands on a rib, so the shell feels solid and sounds less hollow when it
  clicks home. They leave a 42.7 mm centre bay for the NFC tag and side bays
  for weights.
- **Bottom posts are webbed to the corner walls.** At 5.8 mm in, the post sat
  0.02 mm off the wall, a sliver the slicer can't print.

## 2026-11-18 — Cartridge slot: tracks plus ball-plunger detents

Models: `cad/models/slot.py` (slot with baseplate) and the slot features in
`cad/models/cartridge.py`. Research summary: a click feels crisp when
resistance builds and then drops away suddenly (the "tactile ratio" in switch
design), not when force is high. So friction is kept low everywhere except one
detent, and the cartridge lands on a hard floor as the detent drops.

- **Spring ball plungers, not printed springs.** The slot sees every insertion
  for years; with plungers its wearing part is steel, and each cartridge's
  seat only sees that cartridge's insertions. PLA flexures fatigue and creep.
  The feel is tuned by screwing the plungers in or out. PETG printed springs
  are the fallback (Kyle has PETG).
- **Plungers: stainless M6 x 10 hex-socket, 20-pack (Amazon B07T6TBNJN).**
  Easy to get. Ball 3.5 mm and travel 1.0 mm are NOMINAL (typical M6); Amazon
  blocked automated reading, so measure them when they arrive and update
  `params.py`.
- **Plungers press on the back face, not the ends.** An M6 body is 6 mm wide;
  putting it in an end rail would need a track wider than the back half, and it
  would cross the seam. On the back face the ball works on a flat, solid skin
  (doubled to 3.2 mm behind the seat), the plunger sockets are hidden at the
  back of the box, and the preload pushes the cartridge forward against the
  rails. Two plungers at x = +/-30, 6 mm above the floor: clear of a centred NFC
  tag and a reader behind the slot.
- **Detent profile.** A 35 deg, 1.0 mm entry ramp at the bottom edge (35 deg
  rather than shallower because the back face prints on the plate and the ramp
  is an overhang), a short flat, then a 0.6 mm (3-layer) cylindrical seat
  wider than the ball (R 2.25). The seat sits 0.3 mm above the ball, so the
  preload drives the cartridge down onto the floor (no rattle) and the click
  coincides with landing. Insertion climbs 35 deg; removal climbs the 43 deg
  seat rim, so it goes in easier than it comes out.
- **Tracks on the ends, back half only, off-centre (z 2.5–5.5).** They locate
  the cartridge (rails fill the track less `FIT_CLEARANCE` per side) and key it:
  turned label-backwards, the tracks are on the wrong side and the cartridge
  stops on the rails. 1.2 mm deep, running 18 mm up from the bottom edge so
  they're hidden when inserted; the end wall is thickened to 3.36 mm behind
  them. The rails start 6 mm below the mouth with pointed tops.
- **Everything else has clearance** (0.5 mm at the ends, 0.3 mm at the faces)
  so nothing drags before the click; a 1.5 mm lead-in chamfer round the mouth.
- **Slot prints upright, baseplate down, no support.** Plunger holes are
  horizontal 5.0 mm teardrops; the plunger forms its own thread in them (9 mm
  of engagement). Slice the slot with 4+ wall loops so the threads bite
  perimeters rather than sparse infill. Baseplate has four M3 holes for the
  future box.
- **Setting the plungers:** screw in until the ball stands 1.1 mm proud of the
  back wall face (body flush to +0.1), then tune by feel. The slot script
  prints this number from the measured ball values.

## 2026-11-18 — Top screws level with the logo; logo letter spacing

Supersedes the top-screw placement in "Screw layout, bottom text, internal ribs".

- **Top screws and the logo sit in the middle of the top band**, 5.8 mm below
  the top edge, the same as the bottom row and bottom text in the bottom bar.
  `LABEL_BAND` (11.6) is now a plain parameter; both screw rows and both text
  lines are derived from it.
- **Top screws moved 3 mm toward the logo**: 14.9 mm from the ends (was 11.9).
  Counterbore clearances: 2.7 to the top edge, 5.2 to the bevel, 2.7 to the label.
- **Logo letters laid out one by one with 1.0 mm between letter boxes.** With
  Arial's own spacing some letters were ~0.4 mm apart, not enough for the
  slicer to lay walls between them (two lines, 0.84 mm). The logo is now 49.2 mm
  wide (was 44.3). A raster check confirms no plastic narrower than 0.84 mm is
  left between letters; what the check still flags is inside-corner rounding
  and the small counter inside each A.
- **Top posts webbed to the top wall**, like the bottom ones: at 5.8 mm in, the
  post edge sat 0.02 mm off the wall.

## 2026-11-18 — Software architecture

Details in `product.md` (Software, Media).

- **FieldStation42 for channels, plus a small LaserTrack daemon in Python for
  everything else** (option (a)). Scheduling channels is most of FS42's work,
  so rewriting it (option (c)) would waste effort; 240-MP (option (b)) has no
  channels and is C++/Qt under GPL. We borrow 240-MP's look, not its code.
  Python matches FS42 and the `python-plexapi` library.
- **The daemon owns all input** and switches modes by stopping FS42's player
  and starting its own mpv, and back. Buttons change meaning by mode, so
  letting FS42 and mpv read keys directly would make them fight.
- **Cartridges play through Plex; channels read the NAS share.** Supersedes
  the "skip Plex" lean of 2026-11-16, for cartridges only. Kyle wants a
  cartridge to resume where he left off and to show up in Plex's Continue
  Watching on his phone; that needs Plex's saved positions and progress
  reports. Channels must not touch Plex watch history.
- **A cartridge stores only its tag UID**; the box holds the mapping. Tags are
  Kyle's NTAG215 stickers.
- **No menus on the TV; cartridges are assigned from a web page on a phone.**
  Keeps the TV side passive and the button count low, following 240-MP's
  "navigation is not complicated".
- **No duplicate transcoded library for the channels.** Kyle's call: disk
  space is expensive. How channels get playable quality is still open.

## 2026-11-18 — Electronics, first pass

Parts list in `product.md` (Hardware).

- **Raspberry Pi 4 only, no microcontroller in V1.** The RC522, buttons, knob,
  IR receiver and screen all wire to Pi GPIO. Considered a Raspberry Pi Pico
  as a USB front-panel controller. It would give instant-on (the Pi takes
  20–30 s to boot), precise LED timing, a self-contained receptacle module,
  and protect the Pi from wiring mistakes, at the cost of a second program and
  a serial link. For buttons and NFC it adds no reliability: Linux's kernel
  drivers (`gpio-keys`, `rotary-encoder`) work on interrupts and don't drop
  presses, and NFC reliability depends on the antenna, not the board. Plain
  cartridge LEDs can run from a GPIO pin through a transistor. A Pico comes in
  only if the cartridge LEDs become colour effects: addressable LEDs and
  smooth hardware fades on the Pi 4 would use the PWM block that drives the
  headphone-jack audio, which the CRT needs.
- **Output chosen by a DIP switch read at boot** through a conditional
  `[gpioN=1]` section in `config.txt`. Only one TV is connected at a time and
  it rarely changes, so a boot-time switch is simplest and most reliable.
  Mirroring both outputs at once was considered and dropped (fiddly on a Pi 4);
  an HDMI-to-composite converter was rejected because the Pi's own composite
  looks better on a CRT.
- **1.54" 240×240 IPS LCD (ST7789), not OLED.** A colour OLED's blacks look
  better, but a channel number shown for hours would burn in. The LCD also
  has more pixels (240×240 vs 128×128).
- **Controls: Power, Play/Pause, Stop/Eject, Ch ▲, Ch ▼, and a volume knob
  with push-to-mute.** Power is on GPIO3, which can both shut the Pi down
  safely and wake it.
- **IR receiver in V1; the remote itself later.** The receiver costs about $1
  and Linux supports it out of the box; adding the window to the front panel
  now avoids redesigning the box. A custom printed remote is a separate
  project (its own microcontroller, battery life, enclosure).
- **Also in the box:** heatsink and temperature-switched fan, panel-mount
  back-panel ports (USB-C, HDMI, Ethernet, RCA), official 5 V 3 A supply.

## Open questions

See the **Open** items in `product.md`. The biggest are how channels play the
Blu-ray rips without a duplicate library, which NAS and network the box uses,
and the cartridge's internal layout within a cassette's 12 mm thickness.

## 2026-11-19 — Software v1

Code: `software/`; setup and test plan in `software/README.md`.

- **Pi OS 64-bit with desktop (Trixie).** FieldStation42's docs recommend
  Trixie, and its player opens a window, so the desktop session is kept.
  Running without a desktop was not confirmed in its docs.
- **`software/` holds the Pi code**, separate from `firmware/`, which stays
  for PlatformIO microcontroller projects.
- **Media share mounted read-only.** Only `//192.168.1.157/storage/media` is
  mounted, at `/mnt/media`, with `ro` and read-only file modes; setup refuses
  to finish unless a test write fails. Kyle's priority is that nothing on the
  Pi can harm the library. A read-only OMV user for the Pi is the next layer
  (server-side, so it holds even if the Pi is misconfigured).
- **FieldStation42 sees the library through symlinks.** FS42 has no SMB
  support of its own; its docs recommend symlinking content folders into its
  catalog. A symlink is only a pointer; removing it removes the pointer.
- **FS42 runs as our own systemd user service (`fs42.service`)**, started and
  stopped by the daemon. Not FS42's `install_services.sh`, so the service name
  and behaviour are known and nothing starts it behind the daemon's back.
  Both start from the desktop session (XDG autostart) because they need its
  Wayland display.
- **One `mpv.conf` for both players.** FS42 sets no decoder options and has no
  setting to pass them, but its mpv reads `~/.config/mpv/mpv.conf`.
- **The MKV question is answered by measuring.** `lasertrack probe` sorts every
  file by codec (Pi 4: H.264 8-bit and HEVC in hardware; MPEG-2, VC-1, AV1 and
  H.264 10-bit in software). `lasertrack bench` plays samples on the real
  output and counts dropped frames per decoder setting. Fixes for failing
  files are chosen after seeing how many there are.
- **Cartridges on composite play a Plex transcode (720x480, 2 Mbps).** The NAS
  has hardware transcoding, and the Pi then never decodes a Blu-ray stream for
  a cartridge, whatever its codec. HDMI direct-plays the file.
- **Plex sign-in by plex.tv/link code.** No password typed on the Pi; the
  token is in a 0600 file. The server is found by name through the account,
  so its IP isn't hard-coded.
- **Own RC522 driver.** The common Python libraries return only the first 4
  bytes of a 7-byte NTAG215 UID. The driver does the full ISO 14443A select
  and halts the tag after each read so the next poll wakes it again. Removal
  needs 3 missed polls (~0.5 s) so a single missed read doesn't eject.
- **RC522 on SPI0 CE0, reset on GPIO 25** (`electronics/rc522.md`). CE1 is
  left for the LCD; GPIO 3 for the power button.
- **Simulated reader** on the web page, so Plex playback can be tested before
  the reader is wired.
- **Composite is NTSC 480i** (`video=Composite-1:720x480@60ie`), assumed for a
  North American CRT. `setup_pi.sh output` switches between composite and HDMI
  until the DIP switch exists.

## 2026-11-19 — Raw MKVs play on the Pi 4: measured, no re-encoding

First run on the Pi (Pi 4 2 GB, Wi-Fi, composite 480i). `lasertrack probe`
over the whole library (1,660 files): 1,238 H.264 1080p (median 26, max
41 Mbps), 172 HEVC 10-bit **4K** (Seinfeld, Casper; median 66, max 86 Mbps),
178 HEVC 10-bit SD (Golden Girls), 72 VC-1 1080p (3 films, The Office S5).
Audio is mostly DTS-HD MA.

`lasertrack bench` on the CRT showed every dropped frame was at the display,
never the decoder: mpv's default high-quality scalers can't take 1080p/4K down
to 480 lines on the Pi 4's GPU (25% dropped for H.264).

- **`profile=fast` in `mpv.conf`** (cheap bilinear scaling): H.264 dropped
  0%. At 480 lines the quality difference can't be seen.
- **`hwdec=v4l2m2m-copy,drm`**: H.264 on the Pi's stateful decoder, HEVC
  (including 4K 10-bit) zero-copy via `drm` (`drm-copy` dropped 43%, software
  11%). VC-1 falls through to software.
- **Result with that `mpv.conf`: 0% dropped in every group over Wi-Fi**,
  including the 86 Mbps 4K file. VC-1 is marginal (0% and 1.8% in two runs)
  and may stutter occasionally; `vd-lavc-skiploopfilter=all` is the next
  lever if it does.
- **So channels read the raw files** and the "no duplicate library" goal holds.
  Supersedes the open question in `product.md` (Media).
- **Plex is reached directly at `http://192.168.1.232:32400`.** Discovery
  through plex.tv worked but tried dead addresses (Docker bridge, IPv6) for
  about a minute first.
- **FieldStation42's first catalog build is slow** over Wi-Fi: it ffprobes
  each file one at a time for duration (~22 min for 1,660 files), then again
  for chapters. Results are cached, so later rebuilds only see new files.

## 2026-11-20 — First end-to-end run: channels and a cartridge on the CRT

- **FS42 channels need a bump folder even when commercial-free.** It fills
  the gap between a show's end and the next slot with bumps, and failed to
  schedule (`KeyError: 'bump_dir'`) without one. `lasertrack fs42-setup` now
  generates placeholder station-ID clips (colour bars with the channel name;
  10, 30, 60 s) on the SD card, and sets `break_strategy: "end"` so all
  filler comes after the show, never inside a film. Real bumps or commercials
  can replace them; their look is not decided.
- **Placeholder clips rather than FS42's "autobump".** Autobump renders a web
  page through a browser engine, a heavy and untested dependency on a 2 GB Pi.
- **FS42's schedule agent is on** (`main_config.json`: add a week when a day
  is left). `--add_week` built only ~3.5 days.
- **Channels verified:** channel 3 tuned to Interstellar at the scheduled
  point, H.264 on the hardware decoder, 0 dropped frames, mpv ~83% of one
  core. Audio goes to the 3.5 mm jack (PipeWire's default "Built-in Audio",
  bcm2835 Headphones), so composite carries sound without extra setup.
- **Cartridge verified (simulated tag):** insert → UNASSIGNED card and FS42
  stopped → assign Casper from the web page → plays. Plex sends the 4K HEVC
  film as 718x404 H.264 at ~1.3 Mbps (hardware decoded, 0 drops). Remove →
  channels return.
- **Plex ignores positions under 60 s** and keeps the previous one. A
  cartridge pulled in its first minute doesn't move the saved position. This
  is Plex's rule; no change needed.
