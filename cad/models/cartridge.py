"""Cartridge: two thin-walled shells that fit a cassette case and insert long edge first.

Front half: label recess, engraved text, and the M3 screw heads in counterbores
inside short bosses hanging from the front skin. Below each counterbore, two
one-layer "bridge" layers (a slot, then a square) let it print face-down
without support. Its wall is thinned at the seam (rebate) to receive the back
half's lip.
Back half: posts rising to meet the front bosses, each with a pilot hole for
screwing into PLA or a heat-set insert hole (params.SCREW_MODE), a lip around
the rim that aligns the halves, two internal ribs that stiffen the faces, and
the slot interface:
  - a track (groove) up each end, off-centre toward the back, that rides on a
    rail in the slot and keys the cartridge label-forward;
  - two detent seats on the back face near the bottom edge, each with a
    shallow entry ramp, where the slot's ball plungers click in.
Screws: every screw is equidistant from its two nearest edges (top pair: top
edge and bevel; bottom pair: bottom edge and end, centred in the bottom bar).

Print orientation: both halves face-down on the plate (front half: label face;
back half: back face). Back half needs no support. Front half needs support
only in the 1.0 mm label recess; the engraving bridges on its own and the
counterbores use the bridge layers. In Bambu Studio, flip the front half (it
imports face up).

Run (from cad/):  uv run python models/cartridge.py
Outputs to cad/out/: cartridge_front/back .step and .stl, cartridge_assembly.step,
cartridge_sticker.svg (sticker outline for the H2D cutter), and
cartridge_section_*.stl (assembly cut through screws, for render checks).
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from build123d import (
    Axis, Box, Circle, Compound, Cylinder, ExportSVG, Face, FontStyle, Plane,
    Polyline, Pos, Rectangle, Text, Unit, chamfer, export_step, export_stl,
    extrude, fillet, make_face, offset,
)

import params as p

OUT = Path(__file__).resolve().parent.parent / "out"

L, H, T = p.CART_LENGTH, p.CART_HEIGHT, p.CART_THICKNESS
SPLIT_Z = T - p.CART_FRONT_HALF
SKIN_FRONT_Z = T - p.SKIN_FRONT                          # underside of front skin
JOINT_Z = T - p.COUNTERBORE_DEPTH - p.UNDER_HEAD         # boss bottom = post top
BOSS_R = p.COUNTERBORE_DIA / 2 + p.BOSS_WALL
POST_R = p.INSERT_HOLE_DIA / 2 + p.POST_WALL                # same in both screw modes
HOLE_DIA = p.PILOT_HOLE_DIA if p.SCREW_MODE == "pla" else p.INSERT_HOLE_DIA
CB_FLOOR_Z = T - p.COUNTERBORE_DEPTH
KEEP_R = BOSS_R + 0.3                                    # lip/rebate stop short of bosses
BOTTOM_Y = -H / 2

# Screw rows.
TOP_SX, TOP_SY = L / 2 - p.TOP_SCREW_X_INSET, H / 2 - p.TOP_SCREW_INSET
BOT_SX, BOT_SY = L / 2 - p.BOTTOM_SCREW_INSET, -H / 2 + p.BOTTOM_SCREW_INSET

# Detent seat: a groove along X in the back face, centred above the ball.
SEAT_Y = BOTTOM_Y + p.PLUNGER_HEIGHT + p.DETENT_SEAT_OFFSET
SEAT_Z = p.DETENT_DEPTH - p.DETENT_SEAT_R                # axis sits outside the back face


# --- 2D helpers -------------------------------------------------------------

def outline(inset=0.0) -> Face:
    """Front-view outline (bevelled top corners, rounded bottom), optionally inset."""
    hx, hy, c = L / 2, H / 2, p.CART_TOP_CHAMFER
    pts = [(-hx, -hy), (hx, -hy), (hx, hy - c), (hx - c, hy), (-hx + c, hy), (-hx, hy - c)]
    face = make_face(Polyline(*pts, close=True))
    bottom = face.vertices().filter_by(lambda v: v.Y < -hy + 0.01)
    face = fillet(bottom, p.CART_BOTTOM_RADIUS)
    return offset(face, -inset) if inset else face


def band(outer, inner):
    """Ring between two insets of the outline."""
    return outline(outer) - outline(inner)


def screw_positions():
    return [(sx * TOP_SX, TOP_SY) for sx in (-1, 1)] + [(sx * BOT_SX, BOT_SY) for sx in (-1, 1)]


def circles(r):
    out = None
    for x, y in screw_positions():
        c = Pos(x, y) * Circle(r)
        out = c if out is None else out + c
    return out


def rib_zones():
    """Wall regions behind the grip ribs, kept full thickness (no lip or rebate)."""
    span = (p.RIB_COUNT - 1) * p.RIB_PITCH + p.RIB_WIDTH + 3.0
    w = 2 * (p.WALL + 1.0)
    return (Pos(-L / 2, p.RIB_CENTER_Y) * Rectangle(w, span)
            + Pos(L / 2, p.RIB_CENTER_Y) * Rectangle(w, span))


def label_face() -> Face:
    """Wide label LABEL_BAND in from the top, bevels and bottom; LABEL_MARGIN from the sides."""
    d, c = p.LABEL_BAND, p.CART_TOP_CHAMFER
    hx, yt, yb = L / 2 - p.LABEL_MARGIN, H / 2 - d, -H / 2 + d
    k = L / 2 + H / 2 - c - d * 2 ** 0.5   # bevel line x + y = k, parallel to the outer bevel
    pts = [(-hx, yb), (hx, yb), (hx, k - hx), (k - yt, yt), (-(k - yt), yt), (-hx, k - hx)]
    face = make_face(Polyline(*pts, close=True))
    return fillet(face.vertices(), p.LABEL_CORNER_RADIUS)


def sticker_face() -> Face:
    return offset(label_face(), -p.STICKER_GAP)


# --- 3D helpers -------------------------------------------------------------

def prism(face, z0, z1):
    return extrude(Pos(0, 0, z0) * face, z1 - z0)


def yz_prism(pts, x0, x1):
    """Polygon drawn in (Y, Z), extruded along X from x0 to x1."""
    face = make_face(Polyline(*pts, close=True))
    return extrude(Plane.YZ.offset(x0) * face, x1 - x0)


def text_lines():
    return ((p.BRAND_TEXT, p.BRAND_TEXT_SIZE, TOP_SY), (p.BAR_TEXT, p.BAR_TEXT_SIZE, BOT_SY))


def make_text(text, size):
    return Text(text, font_size=size, font=p.TEXT_FONT, font_style=FontStyle.BOLD)


def engraving():
    """Brand in the top band, cassette-style text in the bottom bar."""
    out = None
    for text, size, ty in text_lines():
        solid = prism(Pos(0, ty) * make_text(text, size), T - p.ENGRAVE_DEPTH, T)
        out = solid if out is None else out + solid
    return out


def cut_ribs(part):
    for i in range(p.RIB_COUNT):
        y = p.RIB_CENTER_Y + (i - (p.RIB_COUNT - 1) / 2) * p.RIB_PITCH
        for sx in (-1, 1):
            part -= Pos(sx * L / 2, y, T / 2) * Box(2 * p.RIB_DEPTH, p.RIB_WIDTH, T + 2)
    return part


def tracks():
    """Groove up each end face from the bottom edge, with a flared mouth."""
    z0, z1 = p.TRACK_Z - p.TRACK_WIDTH / 2, p.TRACK_Z + p.TRACK_WIDTH / 2
    f, y0 = p.TRACK_FLARE, BOTTOM_Y - 1
    groove = [(y0, z0), (BOTTOM_Y + p.TRACK_LENGTH, z0), (BOTTOM_Y + p.TRACK_LENGTH, z1), (y0, z1)]
    flare = [(y0, z0 - f - 1), (BOTTOM_Y + 2 * f, z0), (BOTTOM_Y + 2 * f, z1), (y0, z1 + f + 1)]
    out = None
    for sx in (-1, 1):
        x_in, x_out = sx * (L / 2 - p.TRACK_DEPTH), sx * (L / 2 + 1)
        a, b = min(x_in, x_out), max(x_in, x_out)
        cut = yz_prism(groove, a, b) + yz_prism(flare, a, b)
        out = cut if out is None else out + cut
    return out


def detent_seats():
    """Seat groove and entry ramp on the back face at each plunger position."""
    ramp_len = p.DETENT_RAMP_DEPTH / math.tan(math.radians(p.DETENT_RAMP_ANGLE))
    t = math.tan(math.radians(p.DETENT_RAMP_ANGLE))
    ramp = [(BOTTOM_Y - 1, -1), (BOTTOM_Y - 1, p.DETENT_RAMP_DEPTH + t),
            (BOTTOM_Y + ramp_len, 0), (BOTTOM_Y + ramp_len, -1)]
    out = None
    for sx in (-1, 1):
        x = sx * p.PLUNGER_X
        seat = Pos(x, SEAT_Y, SEAT_Z) * Cylinder(p.DETENT_SEAT_R, p.DETENT_LANE, rotation=(0, 90, 0))
        cut = seat + yz_prism(ramp, x - p.DETENT_LANE / 2, x + p.DETENT_LANE / 2)
        out = cut if out is None else out + cut
    return out


# --- Halves -----------------------------------------------------------------

def make_front():
    front = prism(outline(), SPLIT_Z, T)
    front = chamfer(front.edges().group_by(Axis.Z)[-1], p.CART_EDGE_CHAMFER)
    front -= prism(outline(p.WALL), SPLIT_Z, SKIN_FRONT_Z)

    # Bosses hanging from the skin, clipped to the outline at the bevel.
    front += prism(circles(BOSS_R), JOINT_Z, SKIN_FRONT_Z) & prism(outline(), SPLIT_Z, T)

    # Rebate: thin the wall to the skirt where the lip slides in.
    rebate = band(p.SKIRT, p.WALL + 0.05) - circles(KEEP_R) - rib_zones()
    front -= prism(rebate, SPLIT_Z, SPLIT_Z + p.LIP_HEIGHT + p.LIP_TOP_GAP)

    front -= prism(label_face(), T - p.LABEL_DEPTH, T)
    front -= engraving()
    front -= prism(circles(p.COUNTERBORE_DIA / 2), CB_FLOOR_Z, T)
    # Bridge layers (printing face-down, these are the first two layers over
    # the counterbore): a slot across it, then a square, then the round hole.
    lh, c = p.LAYER_HEIGHT, p.SCREW_CLEARANCE_DIA
    for x, y in screw_positions():
        slot = Pos(x, y) * Rectangle(p.COUNTERBORE_DIA, c) & Pos(x, y) * Circle(p.COUNTERBORE_DIA / 2)
        front -= prism(slot, CB_FLOOR_Z - lh, CB_FLOOR_Z + 0.01)
        front -= prism(Pos(x, y) * Rectangle(c, c), CB_FLOOR_Z - 2 * lh, CB_FLOOR_Z)
    front -= prism(circles(c / 2), JOINT_Z - 0.01, CB_FLOOR_Z - 2 * lh + 0.01)
    return cut_ribs(front)


def make_back():
    back = prism(outline(), 0, SPLIT_Z)
    back = chamfer(back.edges().group_by(Axis.Z)[0], p.CART_EDGE_CHAMFER)
    back -= prism(outline(p.WALL), p.SKIN_BACK, SPLIT_Z)
    above = outline(p.WALL + p.LIP_CLEARANCE)   # anything rising past the seam stays inside this

    # Posts up to the joint. Below the seam they merge into the wall; above it
    # they are clipped clear of the front half's wall. The bottom posts sit
    # almost touching the walls, so webs join them to the corner (no sliver gap).
    posts = circles(POST_R)
    webs = None
    for sx in (-1, 1):
        x = sx * BOT_SX
        w = (Pos(x + sx * p.BOTTOM_SCREW_INSET / 2, BOT_SY) * Rectangle(p.BOTTOM_SCREW_INSET, 2 * POST_R)
             + Pos(x, BOT_SY - p.BOTTOM_SCREW_INSET / 2) * Rectangle(2 * POST_R, p.BOTTOM_SCREW_INSET))
        webs = w if webs is None else webs + w
    back += prism(posts + webs, p.SKIN_BACK - 0.01, SPLIT_Z) & prism(outline(), 0, SPLIT_Z)
    back += prism(posts & above, SPLIT_Z - 0.01, JOINT_Z)

    lip_in = p.SKIRT + p.LIP_CLEARANCE
    lip = band(lip_in, lip_in + p.LIP_THICKNESS) - circles(KEEP_R) - rib_zones()
    back += prism(lip, SPLIT_Z - 0.01, SPLIT_Z + p.LIP_HEIGHT)

    # Internal ribs across the short direction, up to just under the front skin.
    ribs = None
    for sx in (-1, 1):
        r = Pos(sx * p.INNER_RIB_X, 0) * Rectangle(p.INNER_RIB_THICKNESS, H)
        ribs = r if ribs is None else ribs + r
    back += prism(ribs & outline(), p.SKIN_BACK - 0.01, SPLIT_Z)
    back += prism(ribs & above, SPLIT_Z - 0.01, SKIN_FRONT_Z - p.INNER_RIB_GAP)

    # Thicker end walls behind the tracks, and a thicker skin behind the seats.
    pad_h = p.TRACK_LENGTH + 2
    for sx in (-1, 1):
        pad = Pos(sx * (L / 2 - p.TRACK_PAD / 2), BOTTOM_Y + pad_h / 2) * Rectangle(p.TRACK_PAD, pad_h)
        back += prism(pad & outline(), p.SKIN_BACK - 0.01, SPLIT_Z)
        seat_pad = Pos(sx * p.PLUNGER_X, (BOTTOM_Y + SEAT_Y + p.DETENT_SEAT_R + 2) / 2) * Rectangle(
            p.DETENT_LANE + 3, SEAT_Y + p.DETENT_SEAT_R + 2 - BOTTOM_Y)
        back += prism(seat_pad & outline(), p.SKIN_BACK - 0.01, p.SKIN_BACK + p.DETENT_PAD)

    back -= tracks()
    back -= detent_seats()
    back -= prism(circles(HOLE_DIA / 2), JOINT_Z - p.HOLE_DEPTH, JOINT_Z + 0.01)
    return cut_ribs(back)


# --- Checks and export ------------------------------------------------------

def thin_stroke_fraction(text, size, res=0.02):
    """Share of the engraved ink narrower than MIN_STROKE (morphological opening)."""
    from matplotlib.path import Path as MPath
    from scipy import ndimage

    t = make_text(text, size)
    bb = t.bounding_box()
    xs = np.arange(bb.min.X - 1, bb.max.X + 1, res)
    ys = np.arange(bb.min.Y - 1, bb.max.Y + 1, res)
    gx, gy = np.meshgrid(xs, ys)
    pts = np.c_[gx.ravel(), gy.ravel()]
    ink = np.zeros(len(pts), bool)
    samples = np.linspace(0, 1, 400)
    for f in t.faces():
        inside = MPath([(v.X, v.Y) for v in f.outer_wire().positions(samples)]).contains_points(pts)
        for w in f.inner_wires():
            inside &= ~MPath([(v.X, v.Y) for v in w.positions(samples)]).contains_points(pts)
        ink |= inside
    ink = ink.reshape(gx.shape)
    r = p.MIN_STROKE / 2 / res
    n = int(math.ceil(r))
    yy, xx = np.ogrid[-n:n + 1, -n:n + 1]
    return 1 - ndimage.binary_opening(ink, xx * xx + yy * yy <= r * r).sum() / ink.sum()


def report(name, part):
    bb = part.bounding_box()
    print(f"{name}: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm, "
          f"volume {part.volume / 1000:.2f} cm^3")


def check(front, back):
    """Numbers to compare against intent before calling the model done."""
    head_top = T - p.COUNTERBORE_DEPTH + p.SCREW_HEAD_HEIGHT
    tip = T - p.COUNTERBORE_DEPTH - p.SCREW_LENGTH
    hole_bottom = JOINT_Z - p.HOLE_DEPTH
    print(f"case clearance per side: length {(p.CASE_INNER_LENGTH - L) / 2:.2f}, "
          f"height {(p.CASE_INNER_HEIGHT - H) / 2:.2f}, "
          f"thickness {(p.CASE_INNER_DEPTH - p.J_CARD_ALLOWANCE - T) / 2:.2f} mm")
    print(f"walls: outer {p.WALL:.2f}, behind ribs {p.WALL - p.RIB_DEPTH:.2f}, "
          f"skirt {p.SKIRT:.2f}, lip {p.LIP_THICKNESS:.2f}, boss {p.BOSS_WALL:.2f}, "
          f"post {p.POST_WALL:.2f}, inner ribs {p.INNER_RIB_THICKNESS:.2f} mm")
    print(f"skins: front {p.SKIN_FRONT:.2f} (under label {p.SKIN_FRONT - p.LABEL_DEPTH:.2f}, "
          f"under text {p.SKIN_FRONT - p.ENGRAVE_DEPTH:.2f}), back {p.SKIN_BACK:.2f} mm")
    print(f"screw: head {T - head_top:.2f} below face, joint at {T - JOINT_Z:.2f} below face, "
          f"{JOINT_Z - tip:.2f} of thread in the post "
          f"({p.SCREW_MODE}: {HOLE_DIA} hole, post wall {POST_R - HOLE_DIA / 2:.2f}), tip {tip - hole_bottom:.2f} above "
          f"hole bottom, {hole_bottom:.2f} floor under hole")
    print(f"lip: {p.LIP_HEIGHT} high into {p.LIP_HEIGHT + p.LIP_TOP_GAP} rebate, "
          f"{p.LIP_CLEARANCE} clearance per side")

    # Screw placement: each screw equidistant from its two nearest edges.
    bevel_k = L / 2 + H / 2 - p.CART_TOP_CHAMFER
    d_top, d_bevel = H / 2 - TOP_SY, (bevel_k - TOP_SX - TOP_SY) / 2 ** 0.5
    d_bot, d_end = BOT_SY + H / 2, L / 2 - BOT_SX
    lab = label_face().bounding_box()
    bar_mid = (BOTTOM_Y + lab.min.Y) / 2
    print(f"top screws at x +/-{TOP_SX:.2f}: {d_top:.2f} from top edge, {d_bevel:.2f} from bevel")
    print(f"bottom screws at x +/-{BOT_SX:.2f}: {d_bot:.2f} from bottom, {d_end:.2f} from end; "
          f"bar centre {bar_mid - BOTTOM_Y:.2f} above bottom")
    assert abs(d_top - d_bevel) < 1e-6 and abs(d_bot - d_end) < 1e-6
    assert abs(bar_mid - BOT_SY) < 1e-6, "bottom screws not centred in the bar"
    gap_top = TOP_SY - p.COUNTERBORE_DIA / 2 - lab.max.Y
    gap_bot = lab.min.Y - (BOT_SY + p.COUNTERBORE_DIA / 2)
    print(f"label to counterbore: top {gap_top:.2f}, bottom {gap_bot:.2f} mm")
    assert min(gap_top, gap_bot) >= p.LABEL_SCREW_CLEARANCE - 1e-6
    # Bevel corner of the label vs top counterbore (distance between parallel bevel lines).
    k_label = L / 2 + H / 2 - p.CART_TOP_CHAMFER - p.LABEL_BAND * 2 ** 0.5
    d = (TOP_SX + TOP_SY - k_label) / 2 ** 0.5 - p.COUNTERBORE_DIA / 2
    print(f"label bevel to top counterbore: {d:.2f} mm")
    assert d >= p.LABEL_SCREW_CLEARANCE - 1e-6

    # Face-down printing: features cut into the face must be whole layers.
    for name, depth in (("label recess", p.LABEL_DEPTH), ("engraving", p.ENGRAVE_DEPTH),
                        ("counterbore", p.COUNTERBORE_DEPTH), ("front skin", p.SKIN_FRONT),
                        ("detent seat", p.DETENT_DEPTH)):
        layers = depth / p.LAYER_HEIGHT
        assert abs(layers - round(layers)) < 1e-6, f"{name} is not whole layers"
    print("face features are whole layers: recess "
          f"{p.LABEL_DEPTH / p.LAYER_HEIGHT:.0f}, engraving {p.ENGRAVE_DEPTH / p.LAYER_HEIGHT:.0f}, "
          f"counterbore {p.COUNTERBORE_DEPTH / p.LAYER_HEIGHT:.0f} + 2 bridge layers, "
          f"detent seat {p.DETENT_DEPTH / p.LAYER_HEIGHT:.0f}")
    print(f"interior cavity height: {SKIN_FRONT_Z - p.SKIN_BACK:.2f} mm; inner ribs stop "
          f"{p.INNER_RIB_GAP} under the front skin; bays: centre "
          f"{2 * p.INNER_RIB_X - p.INNER_RIB_THICKNESS:.1f} wide")
    ov = (front & back).volume
    print(f"halves overlap volume: {ov:.3f} mm^3 (want 0)")
    assert ov < 1e-3, "halves overlap"

    # Engraving: each line centred in its band, clear of label and counterbores,
    # and its strokes wide enough for the nozzle.
    for solid in engraving().solids().group_by(lambda s: s.center().Y > 0):
        bb = Compound(solid).bounding_box()
        clear = bb.min.Y > lab.max.Y or bb.max.Y < lab.min.Y
        side = TOP_SX if bb.center().Y > 0 else BOT_SX
        room = side - p.COUNTERBORE_DIA / 2 - bb.max.X
        print(f"engraving at y {bb.center().Y:+.1f} ({bb.size.X:.1f} x {bb.size.Y:.1f}): "
              f"{'clear of label' if clear else 'OVERLAPS LABEL'}, {room:.1f} mm to counterbores")
        assert clear, "engraving overlaps the label recess"
        assert room > 1.0, "engraving runs into the counterbores"
    for text, size, _ in text_lines():
        frac = thin_stroke_fraction(text, size)
        print(f"'{text}' {size} mm: {frac * 100:.0f}% of ink narrower than {p.MIN_STROKE:.2f} "
              f"(limit {p.MAX_THIN_STROKE_FRACTION * 100:.0f}%)")
        assert frac <= p.MAX_THIN_STROKE_FRACTION, f"'{text}' strokes too thin for the nozzle"

    # Slot interface.
    behind_track = p.TRACK_PAD - p.TRACK_DEPTH
    behind_seat = p.SKIN_BACK + p.DETENT_PAD - p.DETENT_DEPTH
    print(f"tracks: z {p.TRACK_Z - p.TRACK_WIDTH / 2:.1f}-{p.TRACK_Z + p.TRACK_WIDTH / 2:.1f} "
          f"(back half ends at {SPLIT_Z}), {p.TRACK_DEPTH} deep, {behind_track:.2f} wall behind")
    assert p.TRACK_Z + p.TRACK_WIDTH / 2 < SPLIT_Z - 1 and p.TRACK_Z - p.TRACK_WIDTH / 2 > p.CART_EDGE_CHAMFER
    assert p.TRACK_LENGTH < p.CART_INSERT_DEPTH, "track would show above the slot"
    print(f"detent seats at x +/-{p.PLUNGER_X}, {SEAT_Y - BOTTOM_Y:.2f} above bottom edge, "
          f"{p.DETENT_DEPTH:.1f} deep, {behind_seat:.2f} skin behind")
    assert behind_track >= 2 * p.LINE_WIDTH and behind_seat >= 1.0

    st = sticker_face().bounding_box()
    print(f"sticker: {st.size.X:.1f} x {st.size.Y:.1f} mm")


def export_sticker(path):
    svg = ExportSVG(unit=Unit.MM)
    svg.add_layer("cut")
    svg.add_shape(sticker_face(), layer="cut")
    svg.write(str(path))


def build():
    return make_front(), make_back()


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    front, back = build()
    for name, part in (("cartridge_front", front), ("cartridge_back", back)):
        export_step(part, str(OUT / f"{name}.step"))
        export_stl(part, str(OUT / f"{name}.stl"))
        report(name, part)
    export_step(Compound([front, back]), str(OUT / "cartridge_assembly.step"))
    export_sticker(OUT / "cartridge_sticker.svg")

    # Sections through the right-hand screws (keep x below the screw) for render checks.
    for row, sx in (("top", TOP_SX), ("bottom", BOT_SX)):
        keep = Pos(sx - 100, 0, T / 2) * Box(200, H + 2, T + 2)
        export_stl(front & keep, str(OUT / f"cartridge_section_{row}_front.stl"))
        export_stl(back & keep, str(OUT / f"cartridge_section_{row}_back.stl"))
    check(front, back)
