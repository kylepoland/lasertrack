"""Shared dimensions (mm). Every model imports from here so parts stay compatible.

Sections: tolerance gauge, print geometry, fits, cassette case, cartridge,
screws, and the cartridge slot. Values marked "measured" come from Kyle's
parts; values marked "nominal" must be measured before they are trusted.
"""

# --- Tolerance gauge -------------------------------------------------------
# Clearance per side between the test tab and each slot.
GAUGE_CLEARANCES = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]

TAB_WIDTH = 20.0      # tab cross-section, long side
TAB_THICKNESS = 4.0   # tab cross-section, short side
TAB_TONGUE = 20.0     # length of the part that goes into the slot
TAB_HANDLE = 15.0     # length of the grip
TAB_HANDLE_WIDTH = 26.0

GAUGE_HEIGHT = 8.0    # plate thickness = slot depth
GAUGE_WALL = 6.0      # material between slots and around the edge
GAUGE_LABEL_SIZE = 4.0
GAUGE_LABEL_DEPTH = 0.6

# --- Print geometry (H2D, 0.4 mm nozzle) -----------------------------------
# Walls are whole multiples of the extrusion line width so the slicer lays
# full lines with no thin gap-fill; skins are whole multiples of layer height.
LINE_WIDTH = 0.42           # Bambu Studio default for a 0.4 mm nozzle
LAYER_HEIGHT = 0.2

# --- Chosen fit -------------------------------------------------------------
FIT_CLEARANCE = 0.20  # per side; default for PLA on the H2D, refine with the gauge if a fit matters

# --- Cassette case (measured inside cavity, pegless tray) -------------------
CASE_INNER_LENGTH = 103.0
CASE_INNER_HEIGHT = 64.0
CASE_INNER_DEPTH = 14.0
J_CARD_ALLOWANCE = 0.3      # J-card front panel sits inside the lid
CASE_CLEARANCE_EDGE = 1.0   # per side, length and height: drops in, lifts out
CASE_CLEARANCE_FACE = 0.6   # per side, thickness: after the J-card allowance

# --- Cartridge envelope -----------------------------------------------------
# Axes: X = long edge (left/right), Y = up (inserts downwards along -Y,
# long edge first), Z = thickness, front face (user side) at +Z.
CART_LENGTH = CASE_INNER_LENGTH - 2 * CASE_CLEARANCE_EDGE          # 101.0
CART_HEIGHT = CASE_INNER_HEIGHT - 2 * CASE_CLEARANCE_EDGE          # 62.0
CART_THICKNESS = (CASE_INNER_DEPTH - J_CARD_ALLOWANCE
                  - 2 * CASE_CLEARANCE_FACE)                       # 12.5
CART_TOP_CHAMFER = 9.0      # bevelled top corners mark which way is up
CART_BOTTOM_RADIUS = 2.5    # bottom corners, in the outline
CART_EDGE_CHAMFER = 0.8     # front/back perimeter; chamfer not fillet so the
                            # edge on the build plate prints without overhang
CART_INSERT_DEPTH = 22.0    # provisional: how far the long edge sits in the slot

# Halves: front (screw heads) and back (threaded inserts), split parallel to the face.
CART_FRONT_HALF = 5.0       # front half thickness; back half is the rest

# Label recess on the front face; sticker is cut to fit inside it.
# The label sits LABEL_BAND in from the top edge, the top bevels and the
# bottom edge (a brand band on top, a cassette-style text bar at the bottom),
# and LABEL_MARGIN in from the sides. Top corners are bevelled parallel to the
# outline's bevel.
LABEL_MARGIN = 4.0          # side frame width between outline and recess
LABEL_DEPTH = 5 * LAYER_HEIGHT # 1.0: deep enough that the slicer supports it face-down
LABEL_BAND = 11.6           # label inset from top edge, bevels and bottom edge;
                            # the screw rows and text lines sit in the middle of it
LABEL_SCREW_CLEARANCE = 1.5 # minimum gap between any counterbore and the label (checked)
LABEL_CORNER_RADIUS = 1.0   # softens sticker corners so they don't lift
STICKER_GAP = 0.3           # sticker is this much smaller than the recess, per side

# Engraved text on the front face (centred on the screw lines).
ENGRAVE_DEPTH = 0.6
TEXT_FONT = "Arial"
BRAND_TEXT = "LASERTRACK"
BRAND_TEXT_SIZE = 6.5
BRAND_LETTER_GAP = 1.0      # minimum gap between neighbouring letters' boxes. Arial's
                            # own spacing left some letters ~0.4 mm apart, too little for
                            # the slicer to lay walls between them (needs MIN_STROKE)
BAR_TEXT = "HI-FI  \u00b7  120 MIN"
BAR_TEXT_SIZE = 6.5         # was 3.5: strokes came out ~0.45 mm, too thin to print
# Engraved strokes must be at least this wide to print with a 0.4 mm nozzle:
# two extrusion lines. Arial Bold strokes are about 0.13 x the font size, so
# 6.5 mm is the smallest size that clears it (checked by the cartridge script).
MIN_STROKE = 2 * LINE_WIDTH
MAX_THIN_STROKE_FRACTION = 0.25  # share of ink allowed below MIN_STROKE (serifs, tips)

# Grip ribs: grooves on the left and right ends.
RIB_COUNT = 4
RIB_WIDTH = 1.6
RIB_DEPTH = 0.8           # leaves WALL - 0.8 = 1.30 mm (3 lines) behind each groove
RIB_PITCH = 4.0
RIB_CENTER_Y = 8.0          # above the slot line, so they stay visible

# Shell construction.
WALL = 5 * LINE_WIDTH       # 2.10 outer side walls: 2 loops per side + 1 centre line
SKIN_UNDER_LABEL = 6 * LAYER_HEIGHT  # 1.2 of solid face left under the label recess
SKIN_FRONT = LABEL_DEPTH + SKIN_UNDER_LABEL  # 2.2 front face
SKIN_BACK = 8 * LAYER_HEIGHT    # 1.6 back face

# Alignment lip: the back wall's inner half stands up as a lip; the front
# wall's inner half is cut away (rebate) so the lip slides in behind a thin
# outer skirt. Lip and rebate stop around the screw bosses and the ribs.
SKIRT = 3 * LINE_WIDTH      # 1.26 outer skin at the seam; it takes the knocks on insertion
LIP_THICKNESS = 2 * LINE_WIDTH  # 0.84
LIP_HEIGHT = 2.0
LIP_CLEARANCE = 0.1         # per side; snug press. FIT_CLEARANCE (0.2) would slide
LIP_TOP_GAP = 0.2           # rebate is this much taller so the lip never bottoms out

# --- Screws: M3 x 6 low pan head (hex socket) ------------------------------
# Kyle's screws: head 5.8 mm wide, 0.9 mm tall (measured).
# Both rows sit in the middle of their band (top band / bottom bar), level
# with the text. The bottom pair is the same distance in from the end as from
# the bottom edge; the top pair sits further in, toward the logo.
TOP_SCREW_X_INSET = 14.9    # from the end (was 11.9; moved 3 mm toward the logo)
SCREW_CLEARANCE_DIA = 3.4
SCREW_HEAD_DIA = 5.8
SCREW_HEAD_HEIGHT = 0.9
SCREW_LENGTH = 6.0          # under the head
COUNTERBORE_DIA = SCREW_HEAD_DIA + 2 * FIT_CLEARANCE   # 6.2
COUNTERBORE_DEPTH = 6 * LAYER_HEIGHT                   # 1.2: head sits 0.3 below the face;
                            # whole layers so the bridge layers below line up
SCREW_ROW_INSET = LABEL_BAND / 2   # 5.8: both rows, from the top / bottom edge
BOTTOM_SCREW_INSET = SCREW_ROW_INSET  # bottom pair, from the end
UNDER_HEAD = 1.2            # floor under the head that the screw clamps
BOSS_WALL = 3 * LINE_WIDTH  # around the counterbore, hanging from the front skin
# Thread mode. "pla": screw straight into a pilot hole (test prints).
# "insert": M3 x 4 heat-set insert (final). Posts are sized for the insert
# either way, so switching never changes the outside of the part.
SCREW_MODE = "pla"
PILOT_HOLE_DIA = 2.6        # M3 thread-forming into PLA; 2.5-2.8 is typical
INSERT_HOLE_DIA = 4.0       # M3 x 4 heat-set insert (e.g. Ruthex short)
HOLE_DEPTH = 5.5            # 0.7 deeper than the screw reaches
POST_WALL = 4 * LINE_WIDTH  # around the insert; inserts need ~1.5 mm to grip

# Internal ribs: two ribs across the short direction, standing on the back
# skin and stopping just under the front skin. Pressing either face lands on
# a rib, so the cartridge feels solid and sounds less hollow when it clicks
# home. They divide the cavity into a centre bay (NFC tag) and two side bays
# (weights).
INNER_RIB_X = 22.0          # rib centrelines at +/- this
INNER_RIB_THICKNESS = 3 * LINE_WIDTH  # 1.26
INNER_RIB_GAP = 0.2         # below the front skin, so the halves never touch there

# Front ribs: hang from the inside of the front skin, behind the label, where
# the face is thinnest (1.2 mm under the label) and flexed when pressed. They
# stop short of the back skin so an NFC sticker or weights still lie flat
# underneath, and they clear the back half's lip, ribs and posts.
FRONT_RIB_X = (-11.0, 0.0, 11.0)       # rib centrelines; internal, change freely
FRONT_RIB_THICKNESS = 3 * LINE_WIDTH   # 1.26
FRONT_RIB_BACK_GAP = 1.0               # above the back skin (NFC sticker, weights)

# --- Cartridge slot ---------------------------------------------------------
# Tracks: a groove up each end of the cartridge (back half only, off-centre
# in thickness) rides on a rail in the slot. The rails locate the cartridge
# and key it: a cartridge turned label-backwards meets a rail with no groove.
TRACK_Z = 4.0               # groove centre, measured from the back face
TRACK_WIDTH = 3.0
TRACK_DEPTH = 1.2           # into the end face
TRACK_LENGTH = 18.0         # from the bottom edge; stops below the slot line
TRACK_FLARE = 1.0           # groove mouth widens by this per side at the bottom edge
TRACK_PAD = 8 * LINE_WIDTH  # 3.36: end wall thickness behind the track region
RAIL_TOP_GAP = 2.0          # rail stops this far short of the groove's end
RAIL_TIP_CHAMFER = 0.8      # pointed rail top so the groove finds it

# Detent: spring ball plungers through the slot's back wall press on the
# cartridge's back face. Insertion: a shallow ramp at the bottom edge pushes
# the balls in, they ride flat for a few mm, then drop into a seat as the
# cartridge lands on the slot floor. Easy in (ramp angle), firmer out (seat rim).
# Plunger: stainless M6 x 10, hex socket, 20-pack on Amazon (B07T6TBNJN).
# NOMINAL values from typical M6 plungers -- measure when they arrive.
PLUNGER_THREAD = 6.0        # M6 x 1
PLUNGER_LENGTH = 10.0       # nominal
PLUNGER_BALL_DIA = 3.5      # nominal; measure
PLUNGER_BALL_TRAVEL = 1.0   # nominal: free ball protrusion from the body face; measure
PLUNGER_TAP_DIA = 5.0       # the plunger forms its own thread in PLA (teardrop hole)
PLUNGER_X = 30.0            # at +/- this; clear of the NFC area in the middle
PLUNGER_HEIGHT = 6.0        # ball centre above the slot floor
DETENT_DEPTH = 3 * LAYER_HEIGHT   # 0.6 seat depth in the back face (whole layers)
DETENT_SEAT_R = PLUNGER_BALL_DIA / 2 + 0.5  # seat groove radius; wider than the ball
DETENT_SEAT_OFFSET = 0.3    # seat sits this far above the ball so the preload
                            # pushes the cartridge down onto the floor (no rattle)
DETENT_PRELOAD = 0.1        # ball still compressed this much when seated
DETENT_LANE = 6.0           # seat and ramp length along X
DETENT_RAMP_ANGLE = 35.0    # degrees from the face: sets insertion force. The back
                            # face prints on the plate, so the ramp is an overhang;
                            # 35 deg keeps each layer within ~0.3 mm of the one below
DETENT_RAMP_DEPTH = 1.0     # at the bottom edge
DETENT_PAD = 8 * LAYER_HEIGHT  # 1.6: back skin locally doubled behind the seat

# Slot body. Prints upright, baseplate on the plate, mouth up.
SLOT_END_CLEAR = 0.5        # end face to slot wall; the rails locate the ends
SLOT_FACE_CLEAR = 0.3       # per face; the rails locate in thickness
SLOT_WALL = 8 * LINE_WIDTH  # 3.36 front and end walls
SLOT_BACK_WALL = 9.0        # holds the plunger thread; plunger's socket end sits just behind it
SLOT_FLOOR = 4.0            # under the pocket; the floor is the hard stop
SLOT_LEAD_IN = 1.5          # 45 deg chamfer round the mouth
BASE_THICK = 3.0
BASE_MARGIN = 8.0           # baseplate flanges beyond the slot's END walls only (X).
                            # Flush front and back so the NFC reader can sit right
                            # behind the back wall and the front panel parts in front.
BASE_HOLE_DIA = SCREW_CLEARANCE_DIA  # M3 mounting holes for the future box
BASE_HOLE_INSET = 4.0
BASE_CHAMFER = 0.6          # bottom edge on the plate

# --- Set-top box --------------------------------------------------------------
# Axes: X = width (left/right), Y = depth with the FRONT at -Y, Z = up, Z = 0 is
# the underside of the body (the feet hang below it). Style after Kyle's
# reference photos: a mint top shell and a tan bottom shell whose sides curl
# round, a lime chassis plate showing as a stripe at the seam, and white panels
# inset at the open front and back ends.
BOX_W = 250.0
BOX_D = 150.0
BOX_H = 72.0                # body; the cartridge stands ~40 mm above this
BOX_TOP_RADIUS = 20.0       # side curl of the top shell (outside)
BOX_BOTTOM_RADIUS = 20.0    # side curl of the bottom shell; its lowest part is a
                            # 45 deg facet so the bottom shell prints floor-down
SHELL_WALL = 7 * LINE_WIDTH # 2.94; the top spans 244 mm, so thicker than the
                            # cartridge's 5 lines to feel solid under a hand
BOTTOM_SKIN = 15 * LAYER_HEIGHT  # 3.0 floor (bottom shell prints floor-down)
PLATE_THICK = 15 * LAYER_HEIGHT  # 3.0 chassis plate (prints flat)
PLATE_TOP_Z = 32.0          # seam: bottom shell below, plate, top shell above
TILE_GAP = 0.2              # between the front and back top tiles (a crisp seam line)

# Front and back panels sit inside the open ends of the shells.
PANEL_THICK = 15 * LAYER_HEIGHT  # 3.0; panels print face-down, so whole layers
FRONT_PANEL_INSET = 4.0     # shell edge to panel face; a shadow line round the panel
BACK_PANEL_INSET = 2.0      # less at the back so the Pi's ports reach the panel face
FRONT_COMPONENT_DEPTH = 13.0  # room behind the front panel for its boards; the
                              # chassis plate stops this far behind the panel

# Shell screws: M3 from underneath, through a column in the bottom shell and
# the plate, into a tab on the top tile. One screw clamps all three parts.
# M3 x 35 pan head (to buy). Counterbored in the floor (bridge layers, prints
# floor-down without support).
SHELL_SCREW_X = 108.0       # flat part of the floor ends at ~113 (curl facet)
SHELL_SCREW_Y = (-44.0, -29.0, 12.0, 37.0)   # 2 per side on each top tile; the back pair
                            # stays clear of the Pi standoffs (y -11.5 and 46.5)
SHELL_SCREW_LENGTH = 35.0
TILE_TAB_THICK = 14 * LINE_WIDTH   # 5.88: tab under the top tile's side wall
TILE_TAB_HALF = 5.0         # tab half-length along Y around the screw
COLUMN_OD = 8.0
# Panels: two M3 x 6 (Kyle's) up through the floor into a tab on each panel.
PANEL_TAB_X = 80.0
PANEL_TAB_DEPTH = 10.0      # along Y, into the box
PANEL_TAB_WIDTH = 14.0      # along X
PANEL_TAB_THICK = 12 * LINE_WIDTH  # 5.04 along Z, standing on the floor (a wall in the print)

# Feet: four printed bars glued into shallow pockets in the floor.
FOOT_W = 10.0               # X
FOOT_L = 40.0               # Y
FOOT_H = 5.0
FOOT_X = 85.0
FOOT_Y = 45.0
FOOT_POCKET = 5 * LAYER_HEIGHT   # 1.0
FOOT_CLEARANCE = 0.2

# Slot placement: the slot's top is flush with the box top (its rim shows as
# a bezel); it stands on four risers on the chassis plate.
SLOT_CENTER_Y = -30.0       # cartridge mid-thickness, from the box centre
RISER_OD = 8.0
SLOT_SCREW_PILOT = PILOT_HOLE_DIA

# Raspberry Pi 4 (Kyle's). NOMINAL from the Pi 4 drawing: 85 x 56 board, M2.5
# holes 3.5 in from the edges, 58 mm apart along the board. Ethernet/USB end
# faces the back panel; USB-C/HDMI/AV edge faces the middle (cable room); GPIO
# edge faces the right side.
PI_L = 85.0
PI_W = 56.0
PI_T = 1.6
PI_HOLE_INSET = 3.5
PI_HOLE_SPAN = 58.0
PI_X0 = 60.5                # board's left (cable) edge; keeps the GPIO plugs under the curl
PI_STANDOFF = 8.0           # plate top to board underside
PI_STANDOFF_OD = 6.0
PI_PILOT = 2.2              # M2.5 thread-forming into PLA
PI_PORT_OVERHANG = 2.5      # NOMINAL: Ethernet/USB faces beyond the board edge
PI_PORT_HEIGHT = 16.0       # USB stack above the board
PI_PORT_DEPTH = 21.0        # Ethernet jack length along the board
PI_FAN_STACK = 17.0         # heatsink + 30 mm fan above the board (envelope)
PI_GPIO_STACK = 22.5        # header + Dupont housings above the board
PI_PLUG = (20.0, 12.0, 9.0) # envelope of a cable plug on the cable edge (X, Y, Z)

# Top grille over the Pi's fan: slots along Y.
GRILLE_SLOT_W = 2.5
GRILLE_PITCH = 5.0
GRILLE_X = 36.0             # extent across the slots (kept on the flat top)
GRILLE_Y = 50.0             # slot length

# NFC reader (Kyle's RC522). NOMINAL 60 x 40 board, header on a short edge,
# antenna loop at the other end. Stands upright behind the slot's back wall,
# through a slot in the plate, resting on a printed cradle on the floor.
READER_W = 60.0
READER_H = 40.0
READER_T = 1.6
READER_GAP = 3.0            # behind the slot's back wall (plunger sockets stick out 0.9)
READER_X = -10.0            # board centre; the loop sits ~10 off-centre, so the
                            # loop is roughly centred on the cartridge
READER_BOTTOM_Z = 26.0      # tune after the read test: set by the cradle height

# --- Front panel parts ----------------------------------------------------
# Every part is a parameter block so a different screen or button can be
# swapped in by editing values here.
CONTROL_Z = 44.0            # centre line of the screen, buttons, IR and knob

# Screen: Adafruit 1.54" 240x240 IPS, ST7789 (product 3787). NOMINAL from the
# product page: board ~43.7 x 41.8, M2.5 holes on 36.8 x 35.6, active area
# 27.7 square. Measure when it arrives.
LCD_X = -88.0
LCD_BOARD = (43.7, 41.8)
LCD_HOLES = (36.8, 35.6)
LCD_ACTIVE = 27.7
LCD_WINDOW_MARGIN = 0.6     # window larger than the active area, per side
LCD_FACE_HEIGHT = 3.0       # NOMINAL: PCB top to glass face (sets post length)
LCD_PILOT = 2.2             # M2.5

# Buttons: 12 x 12 mm tactile switches (7.3 mm tall with plunger) soldered to
# a strip of perfboard behind the panel, pressed through printed caps.
BUTTON_X = (-48.0, -30.0, -12.0, 6.0, 24.0)   # Power, Play/Pause, Stop, Ch up, Ch down
CAP_DIA = 10.0
CAP_PROUD = 2.0             # in front of the panel face
CAP_FLANGE_DIA = 13.0       # behind the panel; keeps the cap in
CAP_FLANGE = 6 * LAYER_HEIGHT   # 1.2
TACT_SIZE = 12.0
TACT_HEIGHT = 7.3           # board to plunger top
BUTTON_BOARD = (-60.0, 60.0, 30.0, 60.0)   # perfboard x0, x1, z0, z1 (cut to size)
BUTTON_BOARD_T = 1.6
BUTTON_BOARD_HOLE_INSET = 3.0
IR_X = 48.0                 # TSOP38238 on the button board
IR_HOLE = 6.0
LED_X, LED_Z = -48.0, 56.0  # 3 mm status LED above Power
LED_HOLE = 3.2

# Volume: EC11 rotary encoder with push, M7 bushing, 6 mm D shaft.
ENC_X = 88.0
ENC_HOLE = 7.4
ENC_BODY = (12.5, 12.5, 7.0)   # behind the panel (X, Z, depth)
ENC_SHAFT_DIA = 6.0
ENC_SHAFT_FLAT = 4.5        # across the D flat
KNOB_DIA = 32.0
KNOB_H = 14.0
KNOB_GAP = 1.5              # knob to panel face
KNOB_BORE_DEPTH = 10.0
KNOB_GRIP_COUNT = 24        # shallow flutes round the side

# Perforated intake round the controls (the fan pulls air in here and out the top).
PERF_DIA = 2.4
PERF_PITCH = 4.8
PERF_KEEPOUT = 3.0          # clear ring round each control
PERF_EDGE = 6.0             # clear band inside the panel edge

PANEL_TEXT = "LASERTRACK"
PANEL_TEXT_Z = 58.0
PANEL_TEXT_X = -12.0

# --- Back panel parts -----------------------------------------------------
BACK_ROW_Z = 50.0
DC_JACK_X, DC_JACK_HOLE = 40.0, 8.0     # 5.5 x 2.1 panel jack; NOMINAL hole, check the jack bought
AV_JACK_X, AV_JACK_HOLE = 18.0, 6.2     # 3.5 mm 4-pole panel extension to the Pi's AV jack
HDMI_X = -12.0                          # panel-mount HDMI extension (micro-HDMI to HDMI)
HDMI_CUTOUT = (16.0, 7.0)               # NOMINAL; check the cable bought
HDMI_EAR_SPAN = 28.0
TOGGLE_X, TOGGLE_HOLE = -42.0, 6.2      # mini toggle: HDMI / composite, read at boot
