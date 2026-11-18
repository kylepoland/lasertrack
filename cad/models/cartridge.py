"""Cartridge: two thin-walled shells that fit a cassette case and insert long edge first.

Front half: label recess, engraved text, and the M3 screw heads in counterbores
inside short bosses hanging from the front skin. Below each counterbore, two
one-layer "bridge" layers (a slot, then a square) let it print face-down
without support. Its wall is thinned at the seam
(rebate) to receive the back half's lip.
Back half: posts rising to meet the front bosses, each with a pilot hole for
screwing into PLA or a heat-set insert hole (params.SCREW_MODE),
and a lip around the rim that aligns the halves and holds them together.
Print orientation: both halves face-down on the plate. Back half needs no
support. Front half needs support only in the 0.4 mm label recess; the
engraving bridges on its own and the counterbores use the bridge layers.
In Bambu Studio, flip the front half (it imports face up).

Run (from cad/):  uv run python models/cartridge.py
Outputs to cad/out/: cartridge_front/back .step and .stl, cartridge_assembly.step,
cartridge_sticker.svg (sticker outline for the H2D cutter), and
cartridge_section_*.stl (assembly cut through a screw, for render checks).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build123d import (
    Axis, Box, Circle, Compound, ExportSVG, Face, FontStyle, Polyline, Pos,
    Rectangle, Text, Unit, chamfer, export_step, export_stl, extrude, fillet,
    make_face, offset,
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
    x, y = L / 2 - p.SCREW_INSET_X, H / 2 - p.SCREW_INSET_Y
    return [(sx * x, sy * y) for sx in (-1, 1) for sy in (-1, 1)]


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
    """Wide label: straight top/bottom clear of the screws, bevelled top corners."""
    keep = p.COUNTERBORE_DIA / 2 + p.LABEL_SCREW_CLEARANCE
    sx, sy = L / 2 - p.SCREW_INSET_X, H / 2 - p.SCREW_INSET_Y
    hx, yt, yb = L / 2 - p.LABEL_MARGIN, sy - keep, -(sy - keep)
    k = sx + sy - keep * 2 ** 0.5        # bevel line x + y = k, tangent to the keep-out
    pts = [(-hx, yb), (hx, yb), (hx, k - hx), (k - yt, yt), (-(k - yt), yt), (-hx, k - hx)]
    face = make_face(Polyline(*pts, close=True))
    return fillet(face.vertices(), p.LABEL_CORNER_RADIUS)


def sticker_face() -> Face:
    return offset(label_face(), -p.STICKER_GAP)


# --- 3D helpers -------------------------------------------------------------

def prism(face, z0, z1):
    return extrude(Pos(0, 0, z0) * face, z1 - z0)


def engraving():
    """Brand in the top band, cassette-style text in the bottom bar."""
    y = H / 2 - p.SCREW_INSET_Y
    out = None
    for text, size, ty in ((p.BRAND_TEXT, p.BRAND_TEXT_SIZE, y),
                           (p.BAR_TEXT, p.BAR_TEXT_SIZE, -y)):
        t = Text(text, font_size=size, font=p.TEXT_FONT, font_style=FontStyle.BOLD)
        solid = prism(Pos(0, ty) * t, T - p.ENGRAVE_DEPTH, T)
        out = solid if out is None else out + solid
    return out


def cut_ribs(part):
    for i in range(p.RIB_COUNT):
        y = p.RIB_CENTER_Y + (i - (p.RIB_COUNT - 1) / 2) * p.RIB_PITCH
        for sx in (-1, 1):
            part -= Pos(sx * L / 2, y, T / 2) * Box(2 * p.RIB_DEPTH, p.RIB_WIDTH, T + 2)
    return part


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

    # Posts up to the joint. Below the seam they merge into the wall; above it
    # they are clipped clear of the front half's wall (matters at the bevel).
    posts = circles(POST_R)
    back += prism(posts, p.SKIN_BACK - 0.01, SPLIT_Z) & prism(outline(), 0, SPLIT_Z)
    back += prism(posts & outline(p.WALL + p.LIP_CLEARANCE), SPLIT_Z - 0.01, JOINT_Z)

    lip_in = p.SKIRT + p.LIP_CLEARANCE
    lip = band(lip_in, lip_in + p.LIP_THICKNESS) - circles(KEEP_R) - rib_zones()
    back += prism(lip, SPLIT_Z - 0.01, SPLIT_Z + p.LIP_HEIGHT)

    back -= prism(circles(HOLE_DIA / 2), JOINT_Z - p.HOLE_DEPTH, JOINT_Z + 0.01)
    return cut_ribs(back)


# --- Checks and export ------------------------------------------------------

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
          f"post {p.POST_WALL:.2f} mm")
    print(f"skins: front {p.SKIN_FRONT:.2f} (under label {p.SKIN_FRONT - p.LABEL_DEPTH:.2f}, "
          f"under text {p.SKIN_FRONT - p.ENGRAVE_DEPTH:.2f}), back {p.SKIN_BACK:.2f} mm")
    print(f"screw: head {T - head_top:.2f} below face, joint at {T - JOINT_Z:.2f} below face, "
          f"{JOINT_Z - tip:.2f} of thread in the post "
          f"({p.SCREW_MODE}: {HOLE_DIA} hole, post wall {POST_R - HOLE_DIA / 2:.2f}), tip {tip - hole_bottom:.2f} above "
          f"hole bottom, {hole_bottom:.2f} floor under hole")
    print(f"lip: {p.LIP_HEIGHT} high into {p.LIP_HEIGHT + p.LIP_TOP_GAP} rebate, "
          f"{p.LIP_CLEARANCE} clearance per side")
    # Face-down printing: features cut into the face must be whole layers.
    for name, depth in (("label recess", p.LABEL_DEPTH), ("engraving", p.ENGRAVE_DEPTH),
                        ("counterbore", p.COUNTERBORE_DEPTH), ("front skin", p.SKIN_FRONT)):
        layers = depth / p.LAYER_HEIGHT
        assert abs(layers - round(layers)) < 1e-6, f"{name} is not whole layers"
    print("face features are whole layers: recess "
          f"{p.LABEL_DEPTH / p.LAYER_HEIGHT:.0f}, engraving {p.ENGRAVE_DEPTH / p.LAYER_HEIGHT:.0f}, "
          f"counterbore {p.COUNTERBORE_DEPTH / p.LAYER_HEIGHT:.0f} + 2 bridge layers")
    print(f"interior cavity height: {SKIN_FRONT_Z - p.SKIN_BACK:.2f} mm")
    print(f"halves overlap volume: {(front & back).volume:.3f} mm^3 (want 0)")
    # Each engraved line must sit centred in its band, clear of the label.
    lab = label_face().bounding_box()
    for solid in engraving().solids().group_by(lambda s: round(s.center().Y)):
        bb = Compound(solid).bounding_box()
        clear = bb.min.Y > lab.max.Y or bb.max.Y < lab.min.Y
        print(f"engraving at y {bb.center().Y:+.1f} ({bb.size.X:.1f} wide): "
              f"{'clear of label' if clear else 'OVERLAPS LABEL'}")
        assert clear, "engraving overlaps the label recess"

    st = sticker_face().bounding_box()
    print(f"sticker: {st.size.X:.1f} x {st.size.Y:.1f} mm")


def export_sticker(path):
    svg = ExportSVG(unit=Unit.MM)
    svg.add_layer("cut")
    svg.add_shape(sticker_face(), layer="cut")
    svg.write(str(path))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    front, back = make_front(), make_back()
    for name, part in (("cartridge_front", front), ("cartridge_back", back)):
        export_step(part, str(OUT / f"{name}.step"))
        export_stl(part, str(OUT / f"{name}.stl"))
        report(name, part)
    export_step(Compound([front, back]), str(OUT / "cartridge_assembly.step"))
    export_sticker(OUT / "cartridge_sticker.svg")

    # Section through the right-hand screws (keep x < screw x) for render checks.
    sx = L / 2 - p.SCREW_INSET_X
    keep = Pos(sx - 100, 0, T / 2) * Box(200, H + 2, T + 2)
    export_stl(front & keep, str(OUT / "cartridge_section_front.stl"))
    export_stl(back & keep, str(OUT / "cartridge_section_back.stl"))
    check(front, back)
