"""Cartridge: two screwed halves that fit a cassette case and insert long edge first.

Front half carries the label recess and the M3 screw heads (user side).
Back half carries the heat-set inserts and a pocket for the NFC tag and weights.
Print each half face-down on the plate (front half: label face down; back half:
back face down), so the mating faces print on top and need no supports.

Run (from cad/):  uv run python models/cartridge.py
Outputs to cad/out/: cartridge_front.step, cartridge_back.step,
cartridge_assembly.step, matching .stl files, and cartridge_sticker.svg
(the sticker outline for the H2D cutter).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build123d import (
    Axis, Box, Circle, Compound, Cylinder, ExportSVG, Face, Keep, Plane, Polyline, Pos,
    Rectangle, Unit, chamfer, export_step, export_stl, extrude, fillet, make_face, offset,
    split,
)

import params as p

OUT = Path(__file__).resolve().parent.parent / "out"

L, H, T = p.CART_LENGTH, p.CART_HEIGHT, p.CART_THICKNESS
SPLIT_Z = T - p.CART_FRONT_HALF


def outline() -> Face:
    """Front-view outline: bevelled top corners, rounded bottom corners."""
    hx, hy, c = L / 2, H / 2, p.CART_TOP_CHAMFER
    pts = [(-hx, -hy), (hx, -hy), (hx, hy - c), (hx - c, hy), (-hx + c, hy), (-hx, hy - c)]
    face = make_face(Polyline(*pts, close=True))
    bottom = face.vertices().filter_by(lambda v: v.Y < -hy + 0.01)
    return fillet(bottom, p.CART_BOTTOM_RADIUS)


def screw_positions():
    x, y = L / 2 - p.SCREW_INSET, H / 2 - p.SCREW_INSET
    return [(sx * x, sy * y) for sx in (-1, 1) for sy in (-1, 1)]


def circles(r):
    out = None
    for x, y in screw_positions():
        c = Pos(x, y) * Circle(r)
        out = c if out is None else out + c
    return out


def label_face() -> Face:
    r = p.COUNTERBORE_DIA / 2 + p.LABEL_SCREW_CLEARANCE
    return offset(outline(), -p.LABEL_MARGIN) - circles(r)


def sticker_face() -> Face:
    return offset(label_face(), -p.STICKER_GAP)


def make_body():
    body = extrude(outline(), T)
    rims = body.edges().group_by(Axis.Z)
    body = chamfer(rims[0] + rims[-1], p.CART_EDGE_CHAMFER)

    # Label recess in the front face.
    body -= extrude(Pos(0, 0, T) * label_face(), -p.LABEL_DEPTH)

    # Grip ribs on both ends.
    for i in range(p.RIB_COUNT):
        y = p.RIB_CENTER_Y + (i - (p.RIB_COUNT - 1) / 2) * p.RIB_PITCH
        for sx in (-1, 1):
            body -= Pos(sx * L / 2, y, T / 2) * Box(2 * p.RIB_DEPTH, p.RIB_WIDTH, T + 2)

    # Screws: counterbore + clearance through the front half, insert hole in the back.
    for x, y in screw_positions():
        cb = p.COUNTERBORE_DEPTH
        body -= Pos(x, y, T - cb / 2) * Cylinder(p.COUNTERBORE_DIA / 2, cb)
        body -= Pos(x, y, (SPLIT_Z + T) / 2) * Cylinder(p.SCREW_CLEARANCE_DIA / 2, T - SPLIT_Z)
        d = p.INSERT_HOLE_DEPTH
        body -= Pos(x, y, SPLIT_Z - d / 2) * Cylinder(p.INSERT_HOLE_DIA / 2, d)
    return body


def make_halves():
    body = make_body()
    cut = Plane.XY.offset(SPLIT_Z)
    front = split(body, bisect_by=cut, keep=Keep.TOP)
    back = split(body, bisect_by=cut, keep=Keep.BOTTOM)

    # Bosses around the inserts, filled out to the corner so no slivers remain.
    pocket = offset(outline(), -p.POCKET_WALL) - circles(p.POCKET_BOSS_RADIUS)
    for x, y in screw_positions():
        sx, sy = (1 if x > 0 else -1), (1 if y > 0 else -1)
        pocket -= Pos(x + sx * 10, y + sy * 10) * Rectangle(20, 20)
    back -= extrude(Pos(0, 0, SPLIT_Z) * pocket, -p.POCKET_DEPTH)
    return front, back


def report(name, part):
    bb = part.bounding_box()
    print(f"{name}: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm, "
          f"volume {part.volume / 1000:.2f} cm^3")


def check(front, back):
    """Numbers to compare against intent before calling the model done."""
    head_top = T - p.COUNTERBORE_DEPTH + p.SCREW_HEAD_HEIGHT
    tip = T - p.COUNTERBORE_DEPTH - p.SCREW_LENGTH
    print(f"case clearance per side: length {(p.CASE_INNER_LENGTH - L) / 2:.2f}, "
          f"height {(p.CASE_INNER_HEIGHT - H) / 2:.2f}, "
          f"thickness {(p.CASE_INNER_DEPTH - p.J_CARD_ALLOWANCE - T) / 2:.2f} mm")
    print(f"screw head below face: {T - head_top:.2f} mm")
    print(f"screw tip {SPLIT_Z - tip:.2f} mm into back half "
          f"(insert hole {p.INSERT_HOLE_DEPTH} deep, back half {SPLIT_Z:.2f} thick)")
    print(f"back wall behind pocket: {SPLIT_Z - p.POCKET_DEPTH:.2f} mm; "
          f"behind insert: {SPLIT_Z - p.INSERT_HOLE_DEPTH:.2f} mm")
    print(f"material under screw head: {T - p.COUNTERBORE_DEPTH - SPLIT_Z:.2f} mm")
    print(f"halves overlap volume: {(front & back).volume:.3f} mm^3 (want 0)")
    st = sticker_face().bounding_box()
    print(f"sticker: {st.size.X:.1f} x {st.size.Y:.1f} mm, "
          f"{sticker_face().area / 100:.1f} cm^2")
    print(f"visible above slot: {H - p.CART_INSERT_DEPTH:.1f} of {H:.1f} mm "
          f"({100 * (H - p.CART_INSERT_DEPTH) / H:.0f}%)")


def export_sticker(path):
    svg = ExportSVG(unit=Unit.MM)
    svg.add_layer("cut")
    svg.add_shape(sticker_face(), layer="cut")
    svg.write(str(path))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    front, back = make_halves()
    for name, part in (("cartridge_front", front), ("cartridge_back", back)):
        export_step(part, str(OUT / f"{name}.step"))
        export_stl(part, str(OUT / f"{name}.stl"))
        report(name, part)
    export_step(Compound([front, back]), str(OUT / "cartridge_assembly.step"))
    export_sticker(OUT / "cartridge_sticker.svg")
    check(front, back)
