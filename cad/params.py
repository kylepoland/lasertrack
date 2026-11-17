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
