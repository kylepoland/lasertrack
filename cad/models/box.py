"""Set-top box, first pass: two curled shells, a chassis plate, inset panels.

Frame: X = width, Y = depth with the FRONT at -Y, Z = up; Z = 0 is the
underside of the body (feet hang below). All dimensions are in params.py.

Look (after Kyle's reference photos): a mint top shell and a tan bottom shell
whose sides curl round, the lime chassis plate showing as a stripe along the
seam, white panels inset in the open front and back ends, an orange knob,
black feet. The cartridge slot's rim sits flush in the top like a bezel.

Parts and how they print (all matte PLA, 0.20 mm layers):
  top_front, top_back  Top shell, split where the slot's back wall is.
                       Print STANDING on the front end face (profile flat on
                       the plate, +Y up). Every curve is then in the layer
                       plane, so the side curls have no overhang. The front
                       tile's slot notch is open at the top of the print; the
                       screw tabs have 45 deg undersides. Use a brim.
  bottom               Bottom shell. Prints FLOOR-DOWN: the lowest part of the
                       side curl is a 45 deg facet, so the curl never overhangs
                       more than 45 deg. Screw columns rise from the floor;
                       screw counterbores in the floor use bridge layers.
  plate                Chassis plate (lime). Prints flat. Carries the slot
                       risers, the Pi standoffs and the NFC reader slot.
  front_panel          Prints face-down (textured face). Window, button and
  back_panel           knob holes, perforated intake; back: ports and jacks.
  button_cap (x5)      Print flange-down.
  knob                 Print top-face-down (indicator groove bridges).
  foot (x4)            Print flat. Glue into the floor pockets.
  reader_cradle        Holds the RC522 upright at READER_BOTTOM_Z. Print flat.

Assembly: the slot (slot.py), Pi and reader go on the plate. Top tiles sit
on the plate. The bottom shell goes under, and eight M3 x 35 screws from
underneath pass up through its columns and the plate into the top tiles'
tabs, clamping all three. The panels drop into the ends and are held by two
M3 x 6 each, up through the floor into a tab.

Run (from cad/):  uv run python models/box.py
Outputs to cad/out/: box_<part>.step/.stl (printed parts, in assembly
position except the cap, knob and foot), box_bought_<part>.stl (stand-ins for
bought parts, render only), box_assembly.step (coloured), box_section_*.stl.
"""

import math
import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build123d import (
    Axis, Box, BuildSketch, Keep, CenterArc, Circle, Color, Compound, Cylinder, Line,
    Locations, Plane, Polyline, Pos, Rectangle, Rot, chamfer, export_step, export_stl,
    extrude, make_face, offset,
)

import cartridge as cart
import params as p
import slot as sl

OUT = Path(__file__).resolve().parent.parent / "out"

W, D, H = p.BOX_W, p.BOX_D, p.BOX_H
HW, HD = W / 2, D / 2
WALL = p.SHELL_WALL
X_IN = HW - WALL                        # inside face of the side walls
PT = p.PLATE_TOP_Z
PB = PT - p.PLATE_THICK
TOP_IN = H - WALL                       # underside of the top
FC = p.FIT_CLEARANCE

# Panels.
FP_FRONT = -HD + p.FRONT_PANEL_INSET
FP_BACK = FP_FRONT + p.PANEL_THICK
BP_OUTER = HD - p.BACK_PANEL_INSET
BP_INNER = BP_OUTER - p.PANEL_THICK
PLATE_FRONT = FP_BACK + p.FRONT_COMPONENT_DEPTH
PLATE_BACK = BP_INNER - FC

# Slot: its own frame (X, Y up, Z to the user) turned so Y -> Z and Z -> -Y.
YS = p.SLOT_CENTER_Y + p.CART_THICKNESS / 2
ZS = H - sl.Y_TOP
SLOT_TF = Pos(0, YS, ZS) * Rot(90, 0, 0)
SLOT_BACK_Y = YS - sl.ZB
SLOT_FRONT_Y = YS - sl.ZF
SLOT_BASE_Z = ZS + sl.Y_BOT
Y_SPLIT = SLOT_BACK_Y + FC              # front tile ends here, back tile starts TILE_GAP later

# Pi 4 board.
PI_Y1 = BP_INNER
PI_Y0 = PI_Y1 - p.PI_L
PI_X1 = p.PI_X0 + p.PI_W
PI_ZB = PT + p.PI_STANDOFF
PI_ZT = PI_ZB + p.PI_T
PI_CX, PI_CY = (p.PI_X0 + PI_X1) / 2, (PI_Y0 + PI_Y1) / 2

# Reader board.
READER_Y0 = SLOT_BACK_Y + p.READER_GAP
READER_Y1 = READER_Y0 + p.READER_T
READER_YC = (READER_Y0 + READER_Y1) / 2

TAB_X_IN = p.SHELL_SCREW_X - p.COLUMN_OD / 2   # inner end of a top-tile tab

COLORS = {"mint": "#8fd3bd", "tan": "#cfae7f", "lime": "#c6e83a", "white": "#f1f0ec",
          "orange": "#f0602c", "black": "#2a2a2a", "grey": "#9aa0a6", "green": "#2f7d4f",
          "board": "#1f5f9f", "dark": "#555555"}


# --- Helpers ---------------------------------------------------------------

def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def xz(face):
    """A face drawn in XY as (x, z) turned into the XZ plane at Y = 0."""
    return Rot(90, 0, 0) * face


def xz_prism(face, y0, y1):
    """Face drawn as (x, z), extruded along +Y from y0 to y1."""
    return extrude(Pos(0, y0, 0) * xz(face), amount=y1 - y0, dir=(0, 1, 0))


def rect_z(z0, z1):
    return Pos(0, (z0 + z1) / 2) * Rectangle(W + 40, z1 - z0)


def zcyl(x, y, z0, z1, d):
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(d / 2, z1 - z0)


def ycyl(x, z, y0, y1, d):
    return Pos(x, (y0 + y1) / 2, z) * Cylinder(d / 2, y1 - y0, rotation=(90, 0, 0))


def teardrop_z(x, y, z0, z1, d, up=1):
    """Vertical (Z) hole in a part printed with +Y (up=1) or -Y (up=-1) up."""
    face = sl.teardrop(d / 2)
    if up < 0:
        face = Rot(0, 0, 180) * face
    return extrude(Pos(x, y, z0) * face, z1 - z0)


def counterbore_up(x, y, z_top):
    """M3 hole up through a floor printed face-down: counterbore at Z = 0,
    two one-layer bridge layers (slot, then square), then the round hole."""
    cb, c, lh, d = p.COUNTERBORE_DIA, p.SCREW_CLEARANCE_DIA, p.LAYER_HEIGHT, p.COUNTERBORE_DEPTH
    cut = zcyl(x, y, -1, d, cb)
    cut += extrude(Pos(x, y, d - 0.01) * (Rectangle(cb, c) & Circle(cb / 2)), lh + 0.01)
    cut += box(x - c / 2, x + c / 2, y - c / 2, y + c / 2, d + lh - 0.01, d + 2 * lh)
    cut += zcyl(x, y, d + 2 * lh - 0.01, z_top, c)
    return cut


def union(parts):
    out = None
    for s in parts:
        out = s if out is None else out + s
    return out


# --- Profiles (drawn as (x, z)) --------------------------------------------

def outer_profile():
    """Box cross-section: flat top and floor, curled sides. The lowest part of
    each bottom curl is a 45 deg facet (prints floor-down without overhang)."""
    rt, rb = p.BOX_TOP_RADIUS, p.BOX_BOTTOM_RADIUS
    s = math.sqrt(0.5)
    xa, za = HW - rb + rb * s, rb - rb * s      # 45 deg point on the bottom arc
    xb = xa - za                                # facet meets the floor
    edges = [
        Line((-xb, 0), (xb, 0)),
        Line((xb, 0), (xa, za)),
        CenterArc((HW - rb, rb), rb, -45, 45),
        Line((HW, rb), (HW, H - rt)),
        CenterArc((HW - rt, H - rt), rt, 0, 90),
        Line((HW - rt, H), (-(HW - rt), H)),
        CenterArc((-(HW - rt), H - rt), rt, 90, 90),
        Line((-HW, H - rt), (-HW, rb)),
        CenterArc((-(HW - rb), rb), rb, 180, 45),
        Line((-xa, za), (-xb, 0)),
    ]
    return make_face(edges)


OUTER = outer_profile()
INNER = offset(OUTER, -WALL) & rect_z(p.BOTTOM_SKIN, H)   # floor is whole layers (3.0)
TOP_PROFILE = (OUTER & rect_z(PT, H + 1)) - INNER
BOTTOM_PROFILE = (OUTER & rect_z(-1, PB)) - INNER
PANEL_FACE = offset(INNER, -FC)


# --- Top shell ---------------------------------------------------------------

def tile_tab(sx, y0):
    """Tab under the top tile's side wall that the shell screw threads into.
    Its -Y edge is a 45 deg ramp (the tile prints with +Y up)."""
    h = p.TILE_TAB_HALF
    xw, xi = sx * (X_IN + 0.5), sx * TAB_X_IN
    ramp = abs(xw - xi)
    pts = [(xw, y0 + h), (xi, y0 + h), (xi, y0 - h), (xw, y0 - h - ramp)]
    tab = extrude(Pos(0, 0, PT) * make_face(Polyline(*pts, close=True)), p.TILE_TAB_THICK)
    return tab - teardrop_z(sx * p.SHELL_SCREW_X, y0, PT - 1, PT + p.TILE_TAB_THICK + 1, p.PILOT_HOLE_DIA)


def make_top(y0, y1):
    tile = xz_prism(TOP_PROFILE, y0, y1)
    for sx in (-1, 1):
        for sy in p.SHELL_SCREW_Y:
            if y0 < sy < y1:
                tile += tile_tab(sx, sy) & box(-HW, HW, y0, y1, PT, H)
    return tile


def make_top_front():
    tile = make_top(-HD, Y_SPLIT)
    nx = sl.X_OUT + FC
    tile -= box(-nx, nx, SLOT_FRONT_Y - FC, Y_SPLIT + 1, TOP_IN - 1, H + 1)
    return tile


def grille_slots():
    n = int(p.GRILLE_X // p.GRILLE_PITCH)
    cx = min(PI_CX, HW - p.BOX_TOP_RADIUS - p.GRILLE_X / 2 - 1)   # stay on the flat top
    out = []
    for i in range(n):
        x = cx + (i - (n - 1) / 2) * p.GRILLE_PITCH
        out.append(box(x - p.GRILLE_SLOT_W / 2, x + p.GRILLE_SLOT_W / 2,
                       PI_CY - p.GRILLE_Y / 2, PI_CY + p.GRILLE_Y / 2, TOP_IN - 1, H + 1))
    return union(out)


def make_top_back():
    return make_top(Y_SPLIT + p.TILE_GAP, HD) - grille_slots()


# --- Bottom shell --------------------------------------------------------------

def panel_tab_positions():
    """(x, y) of each panel screw: two per panel, centred in the tab."""
    yf = FP_BACK + p.PANEL_TAB_DEPTH / 2
    yb = BP_INNER - p.PANEL_TAB_DEPTH / 2
    return [(sx * p.PANEL_TAB_X, y) for y in (yf, yb) for sx in (-1, 1)]


def foot_positions():
    return [(sx * p.FOOT_X, sy * p.FOOT_Y) for sx in (-1, 1) for sy in (-1, 1)]


def make_bottom():
    bottom = xz_prism(BOTTOM_PROFILE, -HD, HD)
    for sx in (-1, 1):
        for sy in p.SHELL_SCREW_Y:
            x = sx * p.SHELL_SCREW_X
            bottom += zcyl(x, sy, p.BOTTOM_SKIN - 0.01, PB, p.COLUMN_OD)
            bottom -= counterbore_up(x, sy, PB + 1)
    for x, y in panel_tab_positions():
        bottom -= counterbore_up(x, y, p.BOTTOM_SKIN + 1)
    fw, fl = p.FOOT_W + 2 * p.FOOT_CLEARANCE, p.FOOT_L + 2 * p.FOOT_CLEARANCE
    for x, y in foot_positions():
        bottom -= box(x - fw / 2, x + fw / 2, y - fl / 2, y + fl / 2, -1, p.FOOT_POCKET)
    return bottom


# --- Chassis plate -------------------------------------------------------------

def pi_holes():
    xs = (p.PI_X0 + p.PI_HOLE_INSET, PI_X1 - p.PI_HOLE_INSET)
    ys = (PI_Y0 + p.PI_HOLE_INSET, PI_Y0 + p.PI_HOLE_INSET + p.PI_HOLE_SPAN)
    return [(x, y) for x in xs for y in ys]


def riser_positions():
    """Slot baseplate holes in box coordinates."""
    return [(x, YS - z) for x, z in sl.base_holes()]


def make_plate():
    plate = box(-HW, HW, PLATE_FRONT, PLATE_BACK, PB, PT)
    for sx in (-1, 1):   # side strips run the full length: the lime stripe at the seam
        x0, x1 = sorted((sx * X_IN, sx * HW))
        plate += box(x0, x1, -HD, HD, PB, PT)
    for sx in (-1, 1):
        for sy in p.SHELL_SCREW_Y:
            plate -= zcyl(sx * p.SHELL_SCREW_X, sy, PB - 1, PT + 1, p.SCREW_CLEARANCE_DIA)
    for x, y in pi_holes():
        plate += zcyl(x, y, PT - 0.01, PI_ZB, p.PI_STANDOFF_OD)
        plate -= zcyl(x, y, PB + 1.0, PI_ZB + 1, p.PI_PILOT)
    for x, y in riser_positions():
        plate += zcyl(x, y, PT - 0.01, SLOT_BASE_Z, p.RISER_OD)
        plate -= zcyl(x, y, PB + 1.0, SLOT_BASE_Z + 1, p.SLOT_SCREW_PILOT)
    # Reader passes down through the plate; the slot locates it front-to-back.
    rx0, rx1 = p.READER_X - p.READER_W / 2 - 0.5, p.READER_X + p.READER_W / 2 + 0.5
    plate -= box(rx0, rx1, READER_Y0 - 0.2, READER_Y1 + 0.2, PB - 1, PT + 1)
    # Wire pass-through between the compartments.
    plate -= Pos(-60, 10, (PB + PT) / 2) * extrude(Pos(0, 0, -5) * Rectangle(30, 12), 10)
    return plate


# --- Panels --------------------------------------------------------------------

def panel_body(y0, y1):
    return xz_prism(PANEL_FACE, y0, y1)


def panel_tabs(y_face, direction):
    """Tabs at the panel's bottom edge, standing on the floor, with gussets.
    direction: +1 = tab runs toward +Y from the panel's inner face."""
    out = []
    z0, z1 = p.BOTTOM_SKIN, p.BOTTOM_SKIN + p.PANEL_TAB_THICK
    ya, yb = sorted((y_face - direction * 0.01, y_face + direction * p.PANEL_TAB_DEPTH))
    gy = y_face + direction * 8.0
    for sx in (-1, 1):
        x = sx * p.PANEL_TAB_X
        tab = box(x - p.PANEL_TAB_WIDTH / 2, x + p.PANEL_TAB_WIDTH / 2, ya, yb, z0, z1)
        for gx in (x - p.PANEL_TAB_WIDTH / 2, x + p.PANEL_TAB_WIDTH / 2 - 4 * p.LINE_WIDTH):
            tri = make_face(Polyline((y_face - direction * 0.01, z1 - 0.01), (gy, z1 - 0.01),
                                     (y_face - direction * 0.01, z1 + 8.0), close=True))
            tab += extrude(Plane.YZ.offset(gx) * tri, 4 * p.LINE_WIDTH)
        y = y_face + direction * p.PANEL_TAB_DEPTH / 2
        tab -= teardrop_z(x, y, z0 - 1, z1 + 1, p.PILOT_HOLE_DIA, up=direction)
        out.append(tab)
    return union(out)


def front_keepouts():
    """Circles (x, z, r) and rects (x0, x1, z0, z1) the perforation stays clear of."""
    k = p.PERF_KEEPOUT
    circles = [(x, p.CONTROL_Z, p.CAP_DIA / 2 + FC + k) for x in p.BUTTON_X]
    circles += [(p.IR_X, p.CONTROL_Z, p.IR_HOLE / 2 + k), (p.LED_X, p.LED_Z, p.LED_HOLE / 2 + k),
                (p.ENC_X, p.CONTROL_Z, p.KNOB_DIA / 2 + k)]
    b = p.BUTTON_BOARD
    i = p.BUTTON_BOARD_HOLE_INSET
    circles += [(x, z, 3.0 + 1.0) for x in (b[0] + i, b[1] - i) for z in (b[2] + i, b[3] - i)]
    lw, lh = p.LCD_BOARD
    rects = [(p.LCD_X - lw / 2 - k, p.LCD_X + lw / 2 + k, p.CONTROL_Z - lh / 2 - k, p.CONTROL_Z + lh / 2 + k)]
    tb = panel_text().bounding_box()
    rects.append((tb.min.X - k, tb.max.X + k, tb.min.Y - k, tb.max.Y + k))
    for sx in (-1, 1):
        x = sx * p.PANEL_TAB_X
        rects.append((x - p.PANEL_TAB_WIDTH / 2 - k, x + p.PANEL_TAB_WIDTH / 2 + k, 0, p.BOTTOM_SKIN + p.PANEL_TAB_THICK + 8 + k))
    return circles, rects


def inside_panel(x, z, margin):
    """Is (x, z) at least `margin` inside the panel outline? (corners approximated
    by the arcs, which is conservative at the bottom facet)"""
    rt = p.BOX_TOP_RADIUS - WALL - FC - margin
    rb = p.BOX_BOTTOM_RADIUS - WALL - FC - margin
    lim = X_IN - FC - margin
    if abs(x) > lim or z < p.BOTTOM_SKIN + FC + margin or z > TOP_IN - FC - margin:
        return False
    ax = abs(x)
    if ax > HW - p.BOX_TOP_RADIUS and z > H - p.BOX_TOP_RADIUS:
        return math.hypot(ax - (HW - p.BOX_TOP_RADIUS), z - (H - p.BOX_TOP_RADIUS)) <= rt
    if ax > HW - p.BOX_BOTTOM_RADIUS and z < p.BOX_BOTTOM_RADIUS:
        return math.hypot(ax - (HW - p.BOX_BOTTOM_RADIUS), z - p.BOX_BOTTOM_RADIUS) <= rb
    return True


def perforation_points():
    circles, rects = front_keepouts()
    pitch, r = p.PERF_PITCH, p.PERF_DIA / 2
    pts = []
    row = 0
    z = p.BOTTOM_SKIN
    while z < H:
        x0 = -HW + (pitch / 2 if row % 2 else 0)
        x = x0
        while x < HW:
            ok = inside_panel(x, z, p.PERF_EDGE)
            ok = ok and all(math.hypot(x - cx, z - cz) > cr + r for cx, cz, cr in circles)
            ok = ok and not any(a - r < x < b + r and c - r < z < d + r for a, b, c, d in rects)
            if ok:
                pts.append((x, z))
            x += pitch
        z += pitch * math.sqrt(3) / 2
        row += 1
    return pts


def panel_text():
    return Pos(p.PANEL_TEXT_X, p.PANEL_TEXT_Z) * cart.make_text(p.PANEL_TEXT, p.BRAND_TEXT_SIZE, p.BRAND_LETTER_GAP)


def lcd_posts():
    hx, hz = p.LCD_HOLES[0] / 2, p.LCD_HOLES[1] / 2
    return [(p.LCD_X + sx * hx, p.CONTROL_Z + sz * hz) for sx in (-1, 1) for sz in (-1, 1)]


def button_board_posts():
    b, i = p.BUTTON_BOARD, p.BUTTON_BOARD_HOLE_INSET
    return [(x, z) for x in (b[0] + i, b[1] - i) for z in (b[2] + i, b[3] - i)]


BUTTON_BOARD_Y = FP_BACK + p.CAP_FLANGE + p.TACT_HEIGHT   # perfboard front face
LCD_POST_OD = 4.4   # small, so the posts clear the glass between the PCB holes


def make_front_panel():
    panel = panel_body(FP_FRONT, FP_BACK)
    cz = p.CONTROL_Z
    a = p.LCD_ACTIVE / 2 + p.LCD_WINDOW_MARGIN
    panel -= box(p.LCD_X - a, p.LCD_X + a, FP_FRONT - 1, FP_BACK + 1, cz - a, cz + a)
    for x, z in lcd_posts():
        panel += ycyl(x, z, FP_BACK - 0.01, FP_BACK + p.LCD_FACE_HEIGHT, LCD_POST_OD)
        panel -= ycyl(x, z, FP_BACK + 0.6, FP_BACK + p.LCD_FACE_HEIGHT + 1, p.LCD_PILOT)
    for x in p.BUTTON_X:
        panel -= ycyl(x, cz, FP_FRONT - 1, FP_BACK + 1, p.CAP_DIA + 2 * FC)
    for x, z in button_board_posts():
        panel += ycyl(x, z, FP_BACK - 0.01, BUTTON_BOARD_Y, 6.0)
        panel -= ycyl(x, z, FP_BACK + 1.0, BUTTON_BOARD_Y + 1, p.PILOT_HOLE_DIA)
    panel -= ycyl(p.IR_X, cz, FP_FRONT - 1, FP_BACK + 1, p.IR_HOLE)
    panel -= ycyl(p.LED_X, p.LED_Z, FP_FRONT - 1, FP_BACK + 1, p.LED_HOLE)
    panel -= ycyl(p.ENC_X, cz, FP_FRONT - 1, FP_BACK + 1, p.ENC_HOLE)
    with BuildSketch() as sk:
        with Locations(*perforation_points()):
            Circle(p.PERF_DIA / 2)
    panel -= xz_prism(sk.sketch, FP_FRONT - 1, FP_BACK + 1)
    panel -= xz_prism(panel_text(), FP_FRONT - 1, FP_FRONT + p.ENGRAVE_DEPTH)
    panel += panel_tabs(FP_BACK, +1)
    return panel


def make_back_panel():
    panel = panel_body(BP_INNER, BP_OUTER)
    z = p.BACK_ROW_Z
    panel -= box(p.PI_X0, PI_X1, BP_INNER - 1, BP_OUTER + 1, PI_ZT - 0.5, PI_ZT + p.PI_PORT_HEIGHT + 1.0)
    panel -= ycyl(p.DC_JACK_X, z, BP_INNER - 1, BP_OUTER + 1, p.DC_JACK_HOLE)
    panel -= ycyl(p.AV_JACK_X, z, BP_INNER - 1, BP_OUTER + 1, p.AV_JACK_HOLE)
    panel -= ycyl(p.TOGGLE_X, z, BP_INNER - 1, BP_OUTER + 1, p.TOGGLE_HOLE)
    hw, hh = p.HDMI_CUTOUT
    panel -= box(p.HDMI_X - hw / 2, p.HDMI_X + hw / 2, BP_INNER - 1, BP_OUTER + 1, z - hh / 2, z + hh / 2)
    for sx in (-1, 1):
        panel -= ycyl(p.HDMI_X + sx * p.HDMI_EAR_SPAN / 2, z, BP_INNER - 1, BP_OUTER + 1, p.PILOT_HOLE_DIA)
    panel += panel_tabs(BP_INNER, -1)
    return panel


# --- Small printed parts (own frame, print orientation) ------------------------

def make_button_cap():
    """Flange at Z = 0 (print flange-down), cap face at the top."""
    f, t = p.CAP_FLANGE, p.PANEL_THICK + p.CAP_PROUD
    cap = zcyl(0, 0, 0, f, p.CAP_FLANGE_DIA) + zcyl(0, 0, f - 0.01, f + t, p.CAP_DIA)
    return chamfer(cap.edges().group_by(Axis.Z)[-1], 0.6)


def make_knob():
    """Knob face at Z = 0 (print face-down), D bore from the back (top)."""
    h, r = p.KNOB_H, p.KNOB_DIA / 2
    knob = zcyl(0, 0, 0, h, p.KNOB_DIA)
    knob = chamfer(knob.edges().group_by(Axis.Z)[0], 1.0)
    knob = chamfer(knob.edges().group_by(Axis.Z)[-1], 0.6)
    for i in range(p.KNOB_GRIP_COUNT):
        a = 2 * math.pi * i / p.KNOB_GRIP_COUNT
        knob -= zcyl((r + 0.4) * math.cos(a), (r + 0.4) * math.sin(a), 2.0, h + 1, 2.4)
    knob -= box(-0.6, 0.6, 3.0, r - 3.0, -1, 3 * p.LAYER_HEIGHT)    # indicator on the face
    rs = p.ENC_SHAFT_DIA / 2 + 0.1
    # D bore: the flat sits 0.1 mm further out than the shaft's flat.
    bore = Circle(rs) & Pos(0, (p.ENC_SHAFT_FLAT + 0.2 - rs) - rs) * Rectangle(2 * rs, 2 * rs)
    knob -= extrude(Pos(0, 0, h - p.KNOB_BORE_DEPTH) * bore, p.KNOB_BORE_DEPTH + 1)
    return knob


def make_foot():
    """Bar foot, in its print orientation (top up); its top KNOB goes into the floor pocket."""
    f = box(-p.FOOT_W / 2, p.FOOT_W / 2, -p.FOOT_L / 2, p.FOOT_L / 2, 0, p.FOOT_H + p.FOOT_POCKET)
    return chamfer(f.edges().group_by(Axis.Z)[0], 1.0)


def make_reader_cradle():
    """Block on the floor; the reader's bottom edge sits in its groove."""
    x0, x1 = p.READER_X - 20, p.READER_X + 20
    top = p.READER_BOTTOM_Z + 2.0
    c = box(x0, x1, READER_YC - 5, READER_YC + 5, p.BOTTOM_SKIN, top)
    c -= box(x0 - 1, x1 + 1, READER_YC - p.READER_T / 2 - FC, READER_YC + p.READER_T / 2 + FC,
             p.READER_BOTTOM_Z, top + 1)
    return c


# --- Placements of the small parts in the assembly ------------------------------

def placed_caps(cap):
    return [Pos(x, FP_BACK + p.CAP_FLANGE, p.CONTROL_Z) * Rot(90, 0, 0) * cap for x in p.BUTTON_X]


def placed_knob(knob):
    # Knob face toward the user (-Y), its back KNOB_GAP in front of the panel.
    y_face = FP_FRONT - p.KNOB_GAP - p.KNOB_H
    return Pos(p.ENC_X, y_face, p.CONTROL_Z) * Rot(-90, 0, 0) * knob


def placed_feet(foot):
    return [Pos(x, y, -p.FOOT_H) * foot for x, y in foot_positions()]


# --- Bought parts (stand-ins for clash checks and renders) ------------------------

def bought_parts():
    out = {}
    slot = SLOT_TF * sl.make_slot()
    plungers, _, _ = sl.make_plungers()
    front, back = cart.build()
    fwd = Pos(0, 0, sl.CART_SHIFT_Z)
    out["slot"] = slot
    out["plungers"] = SLOT_TF * Compound(plungers)
    out["cartridge_front"] = SLOT_TF * fwd * front
    out["cartridge_back"] = SLOT_TF * fwd * back

    x0, x1 = p.PI_X0, PI_X1
    pi = [box(x0, x1, PI_Y0, PI_Y1, PI_ZB, PI_ZT),
          box(x0 + 1, x1 - 1, PI_Y1 - p.PI_PORT_DEPTH, PI_Y1 + p.PI_PORT_OVERHANG, PI_ZT, PI_ZT + p.PI_PORT_HEIGHT),
          box(PI_CX - 15, PI_CX + 15, PI_CY - 15, PI_CY + 15, PI_ZT, PI_ZT + p.PI_FAN_STACK)]
    gx = x1 - p.PI_HOLE_INSET
    pi.append(box(gx - 3, gx + 3, PI_Y0 + 7, PI_Y0 + 58, PI_ZT, PI_ZT + p.PI_GPIO_STACK))
    out["pi"] = Compound(pi)
    px, py, pz = p.PI_PLUG
    plugs = [box(x0 - px, x0 + 0.5, PI_Y0 + y - py / 2, PI_Y0 + y + py / 2,
                 PI_ZT + 1.5 - pz / 2, PI_ZT + 1.5 + pz / 2) for y in (11.2, 26.0, 39.5, 54.0)]
    out["pi_plugs"] = Compound(plugs)

    cz = p.CONTROL_Z
    lw, lh = p.LCD_BOARD
    lcd = [box(p.LCD_X - lw / 2, p.LCD_X + lw / 2, FP_BACK + p.LCD_FACE_HEIGHT, FP_BACK + p.LCD_FACE_HEIGHT + 1.6,
               cz - lh / 2, cz + lh / 2),
           box(p.LCD_X - 16, p.LCD_X + 16, FP_BACK + 0.01, FP_BACK + p.LCD_FACE_HEIGHT, cz - 15.5, cz + 15.5)]
    out["lcd"] = Compound(lcd)

    b = p.BUTTON_BOARD
    bb = [box(b[0], b[1], BUTTON_BOARD_Y, BUTTON_BOARD_Y + p.BUTTON_BOARD_T, b[2], b[3])]
    s = p.TACT_SIZE / 2
    for x in p.BUTTON_X:
        bb.append(box(x - s, x + s, BUTTON_BOARD_Y - 3.5, BUTTON_BOARD_Y, cz - s, cz + s))
        bb.append(ycyl(x, cz, FP_BACK + p.CAP_FLANGE + 0.01, BUTTON_BOARD_Y - 3.4, 3.5))
    bb.append(box(p.IR_X - 3, p.IR_X + 3, FP_BACK + 1.0, BUTTON_BOARD_Y, cz - 4, cz + 4))
    out["button_board"] = Compound(bb)

    ex, ez, ed = p.ENC_BODY
    rs = p.ENC_SHAFT_DIA / 2
    shaft = Circle(rs) & Pos(0, -rs + p.ENC_SHAFT_FLAT - rs) * Rectangle(2 * rs, 2 * rs)
    y_tip = FP_FRONT - p.KNOB_GAP - p.KNOB_H + (p.KNOB_H - p.KNOB_BORE_DEPTH) + 0.5
    enc = [box(p.ENC_X - ex / 2, p.ENC_X + ex / 2, FP_BACK + 0.01, FP_BACK + ed, cz - ez / 2, cz + ez / 2),
           ycyl(p.ENC_X, cz, FP_FRONT - 1.0, FP_BACK + 0.02, 7.0),
           Pos(p.ENC_X, 0, cz) * extrude(Pos(0, y_tip, 0) * Rot(-90, 0, 0) * shaft, amount=FP_FRONT - 1.0 - y_tip, dir=(0, 1, 0))]
    out["encoder"] = Compound(enc)

    out["reader"] = box(p.READER_X - p.READER_W / 2, p.READER_X + p.READER_W / 2, READER_Y0, READER_Y1,
                        p.READER_BOTTOM_Z, p.READER_BOTTOM_Z + p.READER_H)

    z = p.BACK_ROW_Z
    out["dc_jack"] = ycyl(p.DC_JACK_X, z, BP_INNER - 18, BP_INNER - 0.01, 11.0)
    out["av_jack"] = ycyl(p.AV_JACK_X, z, BP_INNER - 18, BP_INNER - 0.01, 8.0)
    out["toggle"] = box(p.TOGGLE_X - 4, p.TOGGLE_X + 4, BP_INNER - 13, BP_INNER - 0.01, z - 6.5, z + 6.5)
    out["hdmi"] = box(p.HDMI_X - 10, p.HDMI_X + 10, BP_INNER - 25, BP_INNER - 0.01, z - 5, z + 5)
    return out


# --- Build, check, export -----------------------------------------------------

def printed_parts():
    cap, knob, foot = make_button_cap(), make_knob(), make_foot()
    parts = {
        "top_front": make_top_front(), "top_back": make_top_back(), "bottom": make_bottom(),
        "plate": make_plate(), "front_panel": make_front_panel(), "back_panel": make_back_panel(),
        "reader_cradle": make_reader_cradle(),
    }
    loose = {"button_cap": cap, "knob": knob, "foot": foot}
    placed = {f"cap{i}": c for i, c in enumerate(placed_caps(cap))}
    placed["knob"] = placed_knob(knob)
    placed.update({f"foot{i}": f for i, f in enumerate(placed_feet(foot))})
    return parts, loose, placed


def overlap(a, b):
    ba, bb = a.bounding_box(), b.bounding_box()
    if (ba.max.X < bb.min.X or bb.max.X < ba.min.X or ba.max.Y < bb.min.Y or bb.max.Y < ba.min.Y
            or ba.max.Z < bb.min.Z or bb.max.Z < ba.min.Z):
        return 0.0
    return (a & b).volume


def check(parts, placed, bought):
    print(f"body {W:.0f} x {D:.0f} x {H:.0f} mm (+{p.FOOT_H:.0f} feet); seam (plate) at z {PB:.1f}-{PT:.1f}")
    print(f"walls: shell {WALL:.2f} ({WALL / p.LINE_WIDTH:.0f} lines), floor {p.BOTTOM_SKIN:.1f}, "
          f"plate {p.PLATE_THICK:.1f}, panels {p.PANEL_THICK:.1f} mm")
    for name, v, unit in (("shell wall", WALL, p.LINE_WIDTH), ("tile tab", p.TILE_TAB_THICK, p.LINE_WIDTH),
                          ("panel tab", p.PANEL_TAB_THICK, p.LINE_WIDTH), ("floor", p.BOTTOM_SKIN, p.LAYER_HEIGHT),
                          ("plate", p.PLATE_THICK, p.LAYER_HEIGHT), ("panel", p.PANEL_THICK, p.LAYER_HEIGHT),
                          ("foot pocket", p.FOOT_POCKET, p.LAYER_HEIGHT), ("cap flange", p.CAP_FLANGE, p.LAYER_HEIGHT)):
        n = v / unit
        assert abs(n - round(n)) < 1e-6, f"{name} is not a whole number of lines/layers"

    # Slot and cartridge.
    slot_top = (SLOT_TF * sl.make_slot()).bounding_box().max.Z
    cb = (bought["cartridge_front"] + bought["cartridge_back"]).bounding_box()
    print(f"slot top at z {slot_top:.2f} (box top {H}), base on risers at z {SLOT_BASE_Z:.1f} "
          f"({SLOT_BASE_Z - PT:.1f} tall); slot y {SLOT_FRONT_Y:.2f} to {SLOT_BACK_Y:.2f}")
    assert abs(slot_top - H) < 1e-6, "slot rim not flush with the top"
    print(f"cartridge: {cb.max.Z - H:.1f} mm stands above the top; label face {cb.min.Y + HD:.1f} mm "
          f"behind the front edge")

    # Screw stacks.
    cb_floor = p.BOTTOM_SKIN - p.COUNTERBORE_DEPTH
    thread = p.SHELL_SCREW_LENGTH - (cb_floor + (PB - p.BOTTOM_SKIN) + p.PLATE_THICK)
    print(f"shell screws M3 x {p.SHELL_SCREW_LENGTH:.0f}: {cb_floor:.1f} floor + {PB - p.BOTTOM_SKIN:.2f} column "
          f"+ {p.PLATE_THICK:.1f} plate, {thread:.2f} into the {p.TILE_TAB_THICK:.2f} tab")
    assert 3.0 <= thread <= p.TILE_TAB_THICK - 0.5, "shell screw thread length off"
    pthread = p.SCREW_LENGTH - cb_floor
    print(f"panel screws M3 x {p.SCREW_LENGTH:.0f}: {pthread:.1f} into the {p.PANEL_TAB_THICK:.2f} tab")
    assert pthread < p.PANEL_TAB_THICK - 0.5
    rs = p.COUNTERBORE_DIA / 2
    s = math.sqrt(0.5)
    flat = HW - p.BOX_BOTTOM_RADIUS + p.BOX_BOTTOM_RADIUS * s - (p.BOX_BOTTOM_RADIUS - p.BOX_BOTTOM_RADIUS * s)
    print(f"floor flat to x +/-{flat:.1f}; shell screw counterbores reach {p.SHELL_SCREW_X + rs:.1f}")
    assert p.SHELL_SCREW_X + rs < flat - 1

    # Fit on the H2D (single nozzle ~325 x 320 x 325).
    stand = {"top_front": Y_SPLIT + HD, "top_back": HD - Y_SPLIT - p.TILE_GAP}
    print("top tiles print standing: " + ", ".join(f"{k} {v:.1f} tall" for k, v in stand.items()))
    for name in ("bottom", "plate", "front_panel", "back_panel"):
        bb = parts[name].bounding_box()
        assert bb.size.X <= 325 and bb.size.Y <= 320, f"{name} too big for the plate"

    # Room checks.
    print(f"plate front edge {PLATE_FRONT - FP_BACK:.1f} behind the front panel; "
          f"button board {BUTTON_BOARD_Y - FP_BACK:.1f}-{BUTTON_BOARD_Y + p.BUTTON_BOARD_T - FP_BACK:.1f} behind it")
    print(f"Pi board at z {PI_ZB:.1f}, x {p.PI_X0:.1f}-{PI_X1:.1f}, y {PI_Y0:.2f}-{PI_Y1:.2f}; "
          f"ports {p.PI_PORT_OVERHANG - p.PANEL_THICK:+.2f} from the back panel face")
    print(f"reader: y {READER_Y0:.2f}-{READER_Y1:.2f} ({p.READER_GAP} behind the slot), z "
          f"{p.READER_BOTTOM_Z:.1f}-{p.READER_BOTTOM_Z + p.READER_H:.1f} (top inside {TOP_IN:.2f})")
    print(f"front panel: {len(perforation_points())} intake holes")

    # Every pair of parts must not overlap (touching faces are fine).
    items = dict(parts)
    items.update(placed)
    items.update({f"[{k}]": v for k, v in bought.items()})
    allowed = {frozenset(x) for x in (("[slot]", "[plungers]"), ("[slot]", "[cartridge_front]"),
                                      ("[slot]", "[cartridge_back]"), ("[plungers]", "[cartridge_back]"),
                                      ("[cartridge_front]", "[cartridge_back]"), ("[pi]", "[pi_plugs]"))}
    bad = []
    for (na, a), (nb, b) in combinations(items.items(), 2):
        if frozenset((na, nb)) in allowed:
            continue
        v = overlap(a, b)
        if v > 1e-2:
            bad.append((na, nb, v))
    for na, nb, v in bad:
        print(f"  OVERLAP {na} / {nb}: {v:.3f} mm^3")
    print(f"overlap check: {len(items)} parts, {len(bad)} overlapping pairs (want 0)")
    assert not bad, "parts overlap"


def export_all(parts, loose, placed, bought):
    OUT.mkdir(exist_ok=True)
    colours = {"top_front": "mint", "top_back": "mint", "bottom": "tan", "plate": "lime",
               "front_panel": "white", "back_panel": "white", "reader_cradle": "grey",
               "button_cap": "white", "knob": "orange", "foot": "black"}
    for name, part in {**parts, **loose}.items():
        export_step(part, str(OUT / f"box_{name}.step"))
        export_stl(part, str(OUT / f"box_{name}.stl"))
        bb = part.bounding_box()
        print(f"box_{name}: {bb.size.X:.1f} x {bb.size.Y:.1f} x {bb.size.Z:.1f} mm, "
              f"volume {part.volume / 1000:.1f} cm^3")
    groups = {"caps": [v for k, v in placed.items() if k.startswith("cap")],
              "knob_placed": [placed["knob"]],
              "feet": [v for k, v in placed.items() if k.startswith("foot")]}
    for name, ps in groups.items():
        export_stl(Compound(ps), str(OUT / f"box_{name}.stl"))
    for name, part in bought.items():
        export_stl(part, str(OUT / f"box_bought_{name}.stl"))

    asm = []
    for name, part in parts.items():
        part.color = Color(COLORS[colours[name]])
        part.label = name
        asm.append(part)
    for name, ps in groups.items():
        c = Compound(ps)
        c.color = Color(COLORS[{"caps": "white", "knob_placed": "orange", "feet": "black"}[name]])
        c.label = name
        asm.append(c)
    for name, part in bought.items():
        c = Compound([part]) if not isinstance(part, Compound) else part
        c.color = Color(COLORS["green" if name.startswith("pi") else "board" if name in ("lcd", "reader", "button_board")
                              else "white" if name == "slot" else "grey"])
        c.label = name
        asm.append(c)
    export_step(Compound(asm), str(OUT / "box_assembly.step"))

    # Sections for render checks.
    every = {**parts, **groups_flat(groups), **{f"bought_{k}": v for k, v in bought.items()}}
    # Each cut is a plane whose normal points at the half thrown away. Plane
    # splits, not box intersections: intersecting the bottom shell with a box
    # hung OpenCascade.
    cuts = {
        "x0": ((0.05, 0, 0), (1, 0, 0)),                          # keep x < 0: slot, reader
        "pi": ((PI_CX, 0, 0), (1, 0, 0)),                         # keep x < Pi centre
        "screw": ((0, p.SHELL_SCREW_Y[2] + 0.05, 0), (0, 1, 0)),  # keep y < a screw
        "slot": ((0, p.SLOT_CENTER_Y + 0.05, 0), (0, -1, 0)),     # keep y > slot centre
    }
    for cname, (origin, normal) in cuts.items():
        plane = Plane(origin=origin, z_dir=normal)
        for name, part in every.items():
            sec = part.split(plane, keep=Keep.BOTTOM)
            if isinstance(sec, list):
                sec = Compound(list(sec)) if sec else None
            if sec is not None and sec.volume > 1e-3:
                export_stl(sec, str(OUT / f"box_section_{cname}_{name}.stl"))


def groups_flat(groups):
    return {name: Compound(ps) for name, ps in groups.items()}


if __name__ == "__main__":
    import time
    t0 = time.time()
    parts, loose, placed = printed_parts()
    bought = bought_parts()
    print(f"built in {time.time() - t0:.0f} s", flush=True)
    check(parts, placed, bought)
    print(f"checked in {time.time() - t0:.0f} s", flush=True)
    export_all(parts, loose, placed, bought)
    print(f"exported in {time.time() - t0:.0f} s", flush=True)
