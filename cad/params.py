"""Shared dimensions (mm). Every model imports from here so parts stay compatible.

Nothing project-specific is decided yet; the values below only drive the
tolerance gauge. Once the gauge is printed, set FIT_CLEARANCE to the value
that felt right and the box/cartridge models will use it.
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
# Sides sit LABEL_MARGIN in from the outline; top and bottom edges stop
# LABEL_SCREW_CLEARANCE short of the counterbores, leaving a band at the top
# (brand) and a bar at the bottom (cassette-style text). Top corners are
# bevelled parallel to the outline's bevel.
LABEL_MARGIN = 4.0          # side frame width between outline and recess
LABEL_DEPTH = 0.4
LABEL_SCREW_CLEARANCE = 1.5 # gap between counterbore and recess edge
LABEL_CORNER_RADIUS = 1.0   # softens sticker corners so they don't lift
STICKER_GAP = 0.3           # sticker is this much smaller than the recess, per side

# Engraved text on the front face (centred on the screw lines).
ENGRAVE_DEPTH = 0.6
TEXT_FONT = "Arial"
BRAND_TEXT = "LASERTRACK"
BRAND_TEXT_SIZE = 6.5
BAR_TEXT = "HI-FI  \u00b7  120 MIN"
BAR_TEXT_SIZE = 3.5

# Grip ribs: grooves on the left and right ends.
RIB_COUNT = 4
RIB_WIDTH = 1.6
RIB_DEPTH = 0.8           # leaves WALL - 0.8 = 1.30 mm (3 lines) behind each groove
RIB_PITCH = 4.0
RIB_CENTER_Y = 8.0          # above the slot line, so they stay visible

# Shell construction.
WALL = 5 * LINE_WIDTH       # 2.10 outer side walls: 2 loops per side + 1 centre line
SKIN_FRONT = 8 * LAYER_HEIGHT   # 1.6 front face
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
SCREW_INSET_X = 9.0         # from the left/right ends; clears the 9 mm bevel
SCREW_INSET_Y = 7.0         # from the top/bottom edges
SCREW_CLEARANCE_DIA = 3.4
SCREW_HEAD_DIA = 5.8
SCREW_HEAD_HEIGHT = 0.9
SCREW_LENGTH = 6.0          # under the head
COUNTERBORE_DIA = SCREW_HEAD_DIA + 2 * FIT_CLEARANCE   # 6.2
COUNTERBORE_DEPTH = 6 * LAYER_HEIGHT                   # 1.2: head sits 0.3 below the face;
                            # whole layers so the bridge layers below line up
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
