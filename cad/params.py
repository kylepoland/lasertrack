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
LABEL_SCREW_CLEARANCE = 1.5 # gap between a top counterbore and the label edge
LABEL_CORNER_RADIUS = 1.0   # softens sticker corners so they don't lift
STICKER_GAP = 0.3           # sticker is this much smaller than the recess, per side

# Engraved text on the front face (centred on the screw lines).
ENGRAVE_DEPTH = 0.6
TEXT_FONT = "Arial"
BRAND_TEXT = "LASERTRACK"
BRAND_TEXT_SIZE = 6.5
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
# Each screw is the same distance from its two nearest edges.
#   Top pair: TOP_SCREW_INSET from the top edge and from the bevel, which puts
#   it further in from the end than the bottom pair.
#   Bottom pair: centred in the bottom bar (half its height), and the same
#   distance in from the end.
TOP_SCREW_INSET = 7.0       # from the top edge and from the bevel
SCREW_CLEARANCE_DIA = 3.4
SCREW_HEAD_DIA = 5.8
SCREW_HEAD_HEIGHT = 0.9
SCREW_LENGTH = 6.0          # under the head
COUNTERBORE_DIA = SCREW_HEAD_DIA + 2 * FIT_CLEARANCE   # 6.2
COUNTERBORE_DEPTH = 6 * LAYER_HEIGHT                   # 1.2: head sits 0.3 below the face;
                            # whole layers so the bridge layers below line up
# Derived screw positions (see TOP_SCREW_INSET above).
TOP_SCREW_X_INSET = (CART_TOP_CHAMFER - TOP_SCREW_INSET
                     + TOP_SCREW_INSET * 2 ** 0.5)      # 11.90 from the end
LABEL_BAND = TOP_SCREW_INSET + COUNTERBORE_DIA / 2 + LABEL_SCREW_CLEARANCE  # 11.6
BOTTOM_SCREW_INSET = LABEL_BAND / 2                     # 5.8 from bottom and end
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
BASE_MARGIN = 8.0           # baseplate beyond the slot body
BASE_HOLE_DIA = SCREW_CLEARANCE_DIA  # M3 mounting holes for the future box
BASE_HOLE_INSET = 4.0
BASE_CHAMFER = 0.6          # bottom edge on the plate
