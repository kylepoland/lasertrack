"""Cartridge slot: a pocket the cartridge drops into long edge first, on a small baseplate.

Stand-alone test module for now; it becomes the receptacle module in the box.
Same coordinate frame as the cartridge, with the cartridge sitting in it:
X = long edge, Y = up (the cartridge inserts downwards), Z = thickness with
the cartridge's back face at Z = 0 and the user in front (+Z).

How it locates and clicks:
  - Rails on the two end walls run in the cartridge's end tracks. They fix the
    cartridge in X and Z and key it: turned label-backwards, the tracks are on
    the wrong side and the cartridge stops on the rails.
  - Two M6 spring ball plungers thread through the back wall. Near the end of
    travel the balls climb the cartridge's entry ramps, ride flat for a few mm,
    then drop into the seats just as the cartridge lands on the floor. The seat
    sits slightly above the ball, so the preload holds the cartridge down on the
    floor and forward against the rails: no rattle.
  - Feel is tuned by screwing the plungers in or out (hex key from behind).
  - Everything except the rails has clearance, so nothing drags before the click.

Print orientation: upright, baseplate on the plate, mouth up. No support. The
plunger holes are horizontal teardrops (point up) so they print round enough
for the plunger to form its own thread.

Baseplate: flanges on the two ends only, each with two M3 holes, so nothing
sticks out in front of or behind the slot (room for the NFC reader behind the
back wall). In the box it screws onto four risers on the chassis plate.

Run (from cad/):  uv run python models/slot.py
Outputs to cad/out/: slot.step/.stl, slot_plunger.stl (render only),
slot_assembly.step (slot, plungers, cartridge), slot_section_*.stl.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build123d import (
    Axis, Box, Circle, Compound, Cylinder, Polyline, Pos, Sphere, chamfer,
    export_step, export_stl, extrude, make_face,
)

import cartridge as cart
import params as p

OUT = Path(__file__).resolve().parent.parent / "out"

L, H, T = p.CART_LENGTH, p.CART_HEIGHT, p.CART_THICKNESS
X_IN = L / 2 + p.SLOT_END_CLEAR             # pocket half-length
Z0, Z1 = -p.SLOT_FACE_CLEAR, T + p.SLOT_FACE_CLEAR  # pocket back / front faces
Y_FLOOR = -H / 2                            # cartridge bottom edge rests here
Y_TOP = Y_FLOOR + p.CART_INSERT_DEPTH       # mouth
X_OUT = X_IN + p.SLOT_WALL
ZB, ZF = Z0 - p.SLOT_BACK_WALL, Z1 + p.SLOT_WALL
Y_BOT = Y_FLOOR - p.SLOT_FLOOR
BALL_Y = Y_FLOOR + p.PLUNGER_HEIGHT

# Rail: fills the track less FIT_CLEARANCE per side, and stops FIT_CLEARANCE
# short of the track floor, so the rails fix X and Z to +/- FIT_CLEARANCE.
RAIL_Z0 = p.TRACK_Z - p.TRACK_WIDTH / 2 + p.FIT_CLEARANCE
RAIL_Z1 = p.TRACK_Z + p.TRACK_WIDTH / 2 - p.FIT_CLEARANCE
RAIL_TIP_X = L / 2 - p.TRACK_DEPTH + p.FIT_CLEARANCE
RAIL_TOP = Y_FLOOR + p.TRACK_LENGTH - p.RAIL_TOP_GAP

# The plungers push the cartridge forward until its tracks meet the rails.
CART_SHIFT_Z = p.FIT_CLEARANCE


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def teardrop(r):
    """Hole profile in XY, point up (+Y), for a horizontal hole printed upright."""
    c = r / 2 ** 0.5
    return Circle(r) + make_face(Polyline((-c, c), (0, r * 2 ** 0.5), (c, c), (0, 0), close=True))


def make_rail(sx):
    x0, x1 = sorted((sx * (X_IN + 0.1), sx * RAIL_TIP_X))
    rail = box(x0, x1, Y_FLOOR - 0.01, RAIL_TOP, RAIL_Z0, RAIL_Z1)
    wall_x = sx * (X_IN + 0.1)
    top = rail.edges().group_by(Axis.Y)[-1].filter_by(lambda e: abs(e.center().X - wall_x) > 1e-3)
    return chamfer(top, p.RAIL_TIP_CHAMFER)


def base_holes():
    """(x, z) of the four M3 holes in the baseplate's end flanges."""
    m, i = p.BASE_MARGIN, p.BASE_HOLE_INSET
    return [(sx * (X_OUT + m - i), z) for sx in (-1, 1) for z in (ZB + i, ZF - i)]


def make_slot():
    slot = box(-X_OUT, X_OUT, Y_BOT, Y_TOP, ZB, ZF)
    m = p.BASE_MARGIN
    base = box(-X_OUT - m, X_OUT + m, Y_BOT, Y_BOT + p.BASE_THICK, ZB, ZF)
    base = chamfer(base.edges().group_by(Axis.Y)[0], p.BASE_CHAMFER)
    slot += base
    slot -= box(-X_IN, X_IN, Y_FLOOR, Y_TOP + 1, Z0, Z1)

    # Lead-in: chamfer round the mouth so the cartridge finds the pocket.
    rim = slot.edges().filter_by(
        lambda e: abs(e.center().Y - Y_TOP) < 1e-6 and abs(e.center().X) <= X_IN + 1e-3
        and Z0 - 1e-3 <= e.center().Z <= Z1 + 1e-3)
    assert len(rim) == 4, f"expected 4 mouth edges, got {len(rim)}"
    slot = chamfer(rim, p.SLOT_LEAD_IN)

    for sx in (-1, 1):
        slot += make_rail(sx)
        hole = Pos(sx * p.PLUNGER_X, BALL_Y) * teardrop(p.PLUNGER_TAP_DIA / 2)
        slot -= extrude(Pos(0, 0, ZB - 1) * hole, Z0 - ZB + 1.01)

    # Mounting holes in the end flanges.
    for x, z in base_holes():
            slot -= Pos(x, Y_BOT + p.BASE_THICK / 2, z) * Cylinder(
                p.BASE_HOLE_DIA / 2, p.BASE_THICK + 2, rotation=(90, 0, 0))
    return slot


def ball_seated_z():
    """Ball centre Z when it sits in the seat (cartridge pushed forward)."""
    rb, rg = p.PLUNGER_BALL_DIA / 2, p.DETENT_SEAT_R
    dy = p.DETENT_SEAT_OFFSET
    assert dy < rg - rb, "seat offset too big: the ball can't settle into the seat"
    seat_axis_z = CART_SHIFT_Z + cart.SEAT_Z
    return seat_axis_z + math.sqrt((rg - rb) ** 2 - dy ** 2)


def make_plungers():
    """Plungers as bought (body + ball), set to the design preload, balls seated."""
    rb = p.PLUNGER_BALL_DIA / 2
    free_tip = ball_seated_z() + rb + p.DETENT_PRELOAD
    body_face = free_tip - p.PLUNGER_BALL_TRAVEL
    out = []
    for sx in (-1, 1):
        x = sx * p.PLUNGER_X
        body = Pos(x, BALL_Y, body_face - p.PLUNGER_LENGTH / 2) * Cylinder(
            p.PLUNGER_THREAD / 2 - 0.05, p.PLUNGER_LENGTH)
        ball = Pos(x, BALL_Y, ball_seated_z()) * Sphere(rb)
        out.append(body + ball)
    return out, free_tip, body_face


def check(slot, front, back, plungers, free_tip, body_face):
    rb = p.PLUNGER_BALL_DIA / 2
    print(f"pocket {2 * X_IN:.2f} x {Z1 - Z0:.2f}, {p.CART_INSERT_DEPTH} deep; "
          f"clearance per side: ends {p.SLOT_END_CLEAR}, faces {p.SLOT_FACE_CLEAR}")
    print(f"rails: {RAIL_Z1 - RAIL_Z0:.2f} wide in a {p.TRACK_WIDTH} track, tip "
          f"{RAIL_TIP_X - (L / 2 - p.TRACK_DEPTH):.2f} off the track floor, top {RAIL_TOP - Y_FLOOR:.1f} "
          f"above the floor (track ends at {p.TRACK_LENGTH}); cartridge meets the rails after "
          f"{Y_TOP - RAIL_TOP:.1f} mm of travel")
    print(f"walls: ends/front {p.SLOT_WALL:.2f}, back {p.SLOT_BACK_WALL}, floor {p.SLOT_FLOOR}")

    seated_tip = ball_seated_z() + rb
    flat_comp = free_tip - CART_SHIFT_Z
    rim = math.degrees(math.asin(math.sqrt(p.DETENT_SEAT_R ** 2 - (p.DETENT_SEAT_R - p.DETENT_DEPTH) ** 2)
                                 / p.DETENT_SEAT_R))
    print(f"plunger: ball tip {free_tip - Z0:.2f} proud of the back wall face (body "
          f"{body_face - Z0:+.2f}), socket end {ZB - (body_face - p.PLUNGER_LENGTH):.2f} behind the wall, "
          f"{min(body_face, Z0) - max(body_face - p.PLUNGER_LENGTH, ZB):.1f} mm of thread in the wall")
    print(f"ball travel used: {flat_comp:.2f} of {p.PLUNGER_BALL_TRAVEL} on the flat, "
          f"{free_tip - seated_tip:.2f} left when seated; ramp {p.DETENT_RAMP_DEPTH} deep at "
          f"{p.DETENT_RAMP_ANGLE:.0f} deg, seat rim {rim:.0f} deg (removal)")
    print(f"ball meets the ramp {Y_TOP - Y_FLOOR - p.PLUNGER_HEIGHT:.1f} mm into the insertion; "
          f"clicks at {p.CART_INSERT_DEPTH} mm")
    assert flat_comp < p.PLUNGER_BALL_TRAVEL - 0.2, "ball bottoms out on the flat"
    assert p.DETENT_RAMP_DEPTH > flat_comp, "ball misses the entry ramp"
    assert body_face > CART_SHIFT_Z - 0.6 and body_face < CART_SHIFT_Z, "plunger body hits the cartridge"

    # Overlaps: slot vs cartridge, centred and pushed forward; ball vs seat.
    for name, dz in (("centred", 0.0), ("pushed forward", CART_SHIFT_Z)):
        ov = sum((slot & (Pos(0, 0, dz) * h)).volume for h in (front, back))
        print(f"slot / cartridge overlap ({name}): {ov:.4f} mm^3 (want 0)")
        assert ov < 1e-2
    shifted = Pos(0, 0, CART_SHIFT_Z) * back
    ov = sum((pl & shifted).volume for pl in plungers)
    print(f"ball / seated cartridge overlap: {ov:.4f} mm^3 (want ~0)")
    assert ov < 1e-2

    bb = slot.bounding_box()
    print(f"footprint {bb.size.X:.1f} x {bb.size.Z:.1f}, height {bb.size.Y:.1f} mm")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    slot = make_slot()
    front, back = cart.build()
    plungers, free_tip, body_face = make_plungers()
    export_step(slot, str(OUT / "slot.step"))
    export_stl(slot, str(OUT / "slot.stl"))
    export_stl(Compound(plungers), str(OUT / "slot_plunger.stl"))
    fwd = Pos(0, 0, CART_SHIFT_Z)
    export_step(Compound([slot, *plungers, fwd * front, fwd * back]), str(OUT / "slot_assembly.step"))
    bb = slot.bounding_box()
    print(f"slot: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm, volume {slot.volume / 1000:.2f} cm^3")

    # Sections for render checks: through the right plunger (keep x < PLUNGER_X)
    # and horizontally through the rails (keep y below the cut).
    parts = {"slot": slot, "front": fwd * front, "back": fwd * back, "plunger": Compound(plungers)}
    keep_x = Pos(p.PLUNGER_X - 100, 0, 0) * Box(200, 200, 200)
    keep_y = Pos(0, Y_FLOOR + 10 - 100, 0) * Box(300, 200, 200)
    for name, part in parts.items():
        export_stl(part & keep_x, str(OUT / f"slot_section_plunger_{name}.stl"))
        export_stl(part & keep_y, str(OUT / f"slot_section_rail_{name}.stl"))
    check(slot, front, back, plungers, free_tip, body_face)
