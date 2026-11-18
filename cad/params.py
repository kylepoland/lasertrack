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
CART_TOP_CHAMFER = 7.0      # bevelled top corners mark which way is up
CART_BOTTOM_RADIUS = 2.5    # bottom corners, in the outline
CART_EDGE_CHAMFER = 0.8     # front/back perimeter; chamfer not fillet so the
                            # edge on the build plate prints without overhang
CART_INSERT_DEPTH = 22.0    # provisional: how far the long edge sits in the slot

# Halves: front (screw heads) and back (threaded inserts), split parallel to the face.
CART_FRONT_HALF = 5.0       # front half thickness; back half is the rest

# Label recess on the front face; sticker is cut to fit inside it.
LABEL_MARGIN = 4.0          # frame width between outline and recess
LABEL_DEPTH = 0.4
LABEL_SCREW_CLEARANCE = 1.5 # gap between counterbore and recess edge
STICKER_GAP = 0.3           # sticker is this much smaller than the recess, per side

# Grip ribs: grooves on the left and right ends.
RIB_COUNT = 4
RIB_WIDTH = 1.6
RIB_DEPTH = 1.2
RIB_PITCH = 4.0
RIB_CENTER_Y = 8.0          # above the slot line, so they stay visible

# Back-half pocket for the NFC tag and weights.
POCKET_WALL = 3.0
POCKET_DEPTH = 4.0
POCKET_BOSS_RADIUS = 4.5    # material kept around each insert

# --- Screws: M3 x 6 socket head cap screws into heat-set inserts ------------
SCREW_INSET = 7.0           # from the side and top/bottom edges
SCREW_CLEARANCE_DIA = 3.4
SCREW_HEAD_DIA = 5.5
SCREW_HEAD_HEIGHT = 3.0
SCREW_LENGTH = 6.0          # under the head
COUNTERBORE_DIA = 6.0
COUNTERBORE_DEPTH = 3.2     # head sits 0.2 below the face
INSERT_HOLE_DIA = 4.0       # M3 x 4 heat-set insert (e.g. Ruthex short)
INSERT_HOLE_DEPTH = 5.0
