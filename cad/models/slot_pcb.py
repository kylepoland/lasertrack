"""Cartridge slot with pogo pins (successor to slot.py, for cartridge_pcb.py).

Same pocket, rails, ball plungers and baseplate as slot.py. What changes:
  - Six pogo pins (Mill-Max 0906-2) stand up through holes in the floor, one
    under each contact pad of the cartridge PCB.
  - The pins are soldered to the slot PCB (electronics/slot_pcb). It sits in a
    pocket in the slot's underside with the pin flanges against the pocket
    ceiling, held by four M3 low pan-head screws up into the back wall. The
    pocket walls locate the board, so the pins line up with their holes.
  - The floor above the board (SPCB_FLOOR) sets how far the pin tips stand up,
    and so how far the pins compress when a cartridge is seated. The slot body
    is 1 mm deeper under the pocket than slot.py's.

The cartridge lands on the floor as the detent clicks; the pins push its
board up against the ledges and stay at about mid-stroke.

Print orientation: as slot.py, upright with the baseplate on the plate and
the mouth up. The PCB pocket is then a recess in the first layers whose
ceiling bridges 84 mm: the pin holes and the screw holes break it up, but
check in Bambu Studio whether it wants support (paint an enforcer if so).

Run (from cad/):  uv run python models/slot_pcb.py
Outputs to cad/out/: slot_pcb.step/.stl, slot_pcb_board.stl, slot_pcb_pins.stl,
slot_pcb_assembly.step, slot_pcb_section_*.stl.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build123d import Axis, Box, Compound, Cylinder, Pos, chamfer, export_step, export_stl, extrude

import cartridge_pcb as cp
import params as p
import slot as sl

OUT = sl.OUT
box = sl.box

# Vertical stack: cartridge bottom face on the floor (Y_FLOOR), floor above the
# board, board pocket, slot underside.
SPCB_TOP = sl.Y_FLOOR - p.SPCB_FLOOR                     # board top = pin flange underside
POCKET_Y0 = SPCB_TOP - p.SPCB_THICK - p.SPCB_POCKET_PLAY
Y_BOT = POCKET_Y0                                        # slot underside
PIN_Z = (cp.BZ0 + cp.BZ1) / 2 + sl.CART_SHIFT_Z          # pad centre, cartridge pushed forward
assert abs(cp.BOTTOM - sl.Y_FLOOR) < 1e-9  # same frame: the cartridge sits on the floor
FREE_TIP = SPCB_TOP + p.POGO_LENGTH
COMPRESSION = FREE_TIP - cp.PAD_Y_SEATED


def make_slot():
    slot = box(-sl.X_OUT, sl.X_OUT, Y_BOT, sl.Y_TOP, sl.ZB, sl.ZF)
    m = p.BASE_MARGIN
    base = box(-sl.X_OUT - m, sl.X_OUT + m, Y_BOT, Y_BOT + p.BASE_THICK, sl.ZB, sl.ZF)
    base = chamfer(base.edges().group_by(Axis.Y)[0], p.BASE_CHAMFER)
    slot += base
    slot -= box(-sl.X_IN, sl.X_IN, sl.Y_FLOOR, sl.Y_TOP + 1, sl.Z0, sl.Z1)
    rim = slot.edges().filter_by(
        lambda e: abs(e.center().Y - sl.Y_TOP) < 1e-6 and abs(e.center().X) <= sl.X_IN + 1e-3
        and sl.Z0 - 1e-3 <= e.center().Z <= sl.Z1 + 1e-3)
    assert len(rim) == 4, f"expected 4 mouth edges, got {len(rim)}"
    slot = chamfer(rim, p.SLOT_LEAD_IN)
    for sx in (-1, 1):
        slot += sl.make_rail(sx)
        hole = Pos(sx * p.PLUNGER_X, sl.BALL_Y) * sl.teardrop(p.PLUNGER_TAP_DIA / 2)
        slot -= extrude(Pos(0, 0, sl.ZB - 1) * hole, sl.Z0 - sl.ZB + 1.01)
    for x, z in base_holes():
        slot -= Pos(x, Y_BOT + p.BASE_THICK / 2, z) * Cylinder(
            p.BASE_HOLE_DIA / 2, p.BASE_THICK + 2, rotation=(90, 0, 0))

    # Board pocket in the underside, pin holes through the floor, screw pilots.
    cl = p.SPCB_POCKET_CLEAR
    z0, z1 = p.SPCB_Z
    slot -= box(-p.SPCB_LENGTH / 2 - cl, p.SPCB_LENGTH / 2 + cl, Y_BOT - 1, SPCB_TOP, z0 - cl, z1 + cl)
    for x in p.CPAD_X:
        slot -= Pos(x, (SPCB_TOP + sl.Y_FLOOR) / 2, PIN_Z) * Cylinder(
            p.POGO_HOLE_DIA / 2, sl.Y_FLOOR - SPCB_TOP + 0.02, rotation=(90, 0, 0))
    # Relief grooves over the header pin tails that come through the board.
    w, d = p.SPCB_HEADER_RELIEF
    for x1, n in p.SPCB_HEADERS:
        slot -= box(x1 - w / 2, x1 + (n - 1) * 2.54 + w / 2, SPCB_TOP - 0.01, SPCB_TOP + d,
                    p.SPCB_HEADER_Z - w / 2, p.SPCB_HEADER_Z + w / 2)
    hole = p.PILOT_HOLE_DIA if p.SCREW_MODE == "pla" else p.INSERT_HOLE_DIA
    for x in p.SPCB_SCREW_X:
        slot -= Pos(x, SPCB_TOP + p.HOLE_DEPTH / 2 - 0.01, p.SPCB_SCREW_Z) * Cylinder(
            hole / 2, p.HOLE_DEPTH + 0.02, rotation=(90, 0, 0))
    return slot


def base_holes():
    mm, i = p.BASE_MARGIN, p.BASE_HOLE_INSET
    return [(sx * (sl.X_OUT + mm - i), z) for sx in (-1, 1) for z in (sl.ZB + i, sl.ZF - i)]


def make_board():
    z0, z1 = p.SPCB_Z
    b = box(-p.SPCB_LENGTH / 2, p.SPCB_LENGTH / 2, SPCB_TOP - p.SPCB_THICK, SPCB_TOP, z0, z1)
    b = chamfer(b.edges().filter_by(Axis.Y), p.SPCB_CORNER_CHAMFER)
    for x in p.SPCB_SCREW_X:
        b -= Pos(x, SPCB_TOP - p.SPCB_THICK / 2, p.SPCB_SCREW_Z) * Cylinder(
            p.SCREW_CLEARANCE_DIA / 2, p.SPCB_THICK + 1, rotation=(90, 0, 0))
    return b


def make_pins(seated=True):
    """Pogo pins on the board: flange, barrel, plunger (compressed to the pad when seated)."""
    tip = cp.PAD_Y_SEATED if seated else FREE_TIP
    out = []
    for x in p.CPAD_X:
        flange_h = 0.41
        pin = Pos(x, SPCB_TOP + flange_h / 2, PIN_Z) * Cylinder(p.POGO_FLANGE_DIA / 2, flange_h, rotation=(90, 0, 0))
        barrel_top = SPCB_TOP + p.POGO_BARREL_H
        pin += Pos(x, (SPCB_TOP + barrel_top) / 2, PIN_Z) * Cylinder(
            p.POGO_BARREL_DIA / 2, p.POGO_BARREL_H, rotation=(90, 0, 0))
        pin += Pos(x, (barrel_top + tip) / 2, PIN_Z) * Cylinder(
            p.POGO_PLUNGER_DIA / 2, tip - barrel_top, rotation=(90, 0, 0))
        tail = p.POGO_TAIL
        pin += Pos(x, SPCB_TOP - tail[1] / 2, PIN_Z) * Cylinder(tail[0] / 2, tail[1], rotation=(90, 0, 0))
        out.append(pin)
    return out


def make_screws():
    """M3 low pan heads under the board (render and overlap check only)."""
    out = []
    y_head = SPCB_TOP - p.SPCB_THICK
    for x in p.SPCB_SCREW_X:
        s = Pos(x, y_head - p.SCREW_HEAD_HEIGHT / 2, p.SPCB_SCREW_Z) * Cylinder(
            p.SCREW_HEAD_DIA / 2, p.SCREW_HEAD_HEIGHT, rotation=(90, 0, 0))
        out.append(s)
    return out


def check(slot, front, back, board, pcb, pins):
    import math
    print(f"floor {p.SPCB_FLOOR:.2f} over the board; board top y {SPCB_TOP:.2f}, slot underside "
          f"y {Y_BOT:.2f} ({sl.Y_FLOOR - Y_BOT:.2f} under the pocket; slot.py has {p.SLOT_FLOOR})")
    print(f"pins at z {PIN_Z:.2f} (pad centre {(cp.BZ0 + cp.BZ1) / 2:.2f} + {sl.CART_SHIFT_Z} forward), "
          f"x {', '.join(f'{x:+.0f}' for x in p.CPAD_X)}")
    print(f"pin tip free {FREE_TIP - sl.Y_FLOOR:+.2f} above the floor; pad seated "
          f"{cp.PAD_Y_SEATED - sl.Y_FLOOR:+.2f}; compression {COMPRESSION:.2f} of {p.POGO_STROKE} "
          f"(rated mid-stroke {p.POGO_MID})")
    assert 0.4 <= COMPRESSION <= p.POGO_STROKE - 0.4, "pins too close to an end of their stroke"
    barrel_top = SPCB_TOP + p.POGO_BARREL_H
    print(f"barrel top {sl.Y_FLOOR - barrel_top:.2f} below the floor; floor holes "
          f"{p.POGO_HOLE_DIA} for a {p.POGO_FLANGE_DIA} flange / {p.POGO_BARREL_DIA} barrel")
    assert barrel_top < sl.Y_FLOOR - 0.2
    # Pins reach the pads inside the window even with the cartridge centred.
    for name, dz in (("centred", 0.0), ("pushed forward", sl.CART_SHIFT_Z)):
        zc = (cp.BZ0 + cp.BZ1) / 2 + dz
        off = abs(PIN_Z - zc)
        edge = min(p.CPAD_SIZE[1] / 2, (cp.WZ1 - cp.WZ0) / 2) - p.POGO_PLUNGER_DIA / 2
        print(f"pin vs pad ({name}): {off:.2f} off centre, {edge - off:.2f} to spare")
        assert off < edge
    end_play = p.SLOT_END_CLEAR
    print(f"pin vs pad along x: cartridge end play +/-{end_play}, pad half-length "
          f"{p.CPAD_SIZE[0] / 2}, plunger radius {p.POGO_PLUNGER_DIA / 2:.2f}")
    assert end_play + p.POGO_PLUNGER_DIA / 2 < p.CPAD_SIZE[0] / 2

    # Overlaps.
    fwd = Pos(0, 0, sl.CART_SHIFT_Z)
    for name, part in (("slot / board", slot & board), ("slot / pins", slot & Compound(pins)),
                       ("pins / cartridge front", Compound(pins) & (fwd * front)),
                       ("pins / cartridge back", Compound(pins) & (fwd * back)),
                       ("slot / cartridge front", slot & (fwd * front)),
                       ("slot / cartridge back", slot & (fwd * back)),
                       ("slot / cartridge PCB", slot & (fwd * pcb)),
                       ("slot / screw heads", slot & Compound(make_screws()))):
        v = part.volume
        print(f"{name} overlap: {v:.4f} mm^3 (want 0)")
        assert v < 1e-2, f"{name} overlap"
    # Pins touch the pads (contact, not overlap).
    v = (Compound(pins) & (fwd * pcb)).volume
    print(f"pins / cartridge PCB overlap: {v:.4f} mm^3 (touching)")
    assert v < 1e-2
    w, d = p.SPCB_HEADER_RELIEF
    print(f"header relief grooves {w} wide, {d} deep: {p.SPCB_FLOOR - d:.2f} of floor left above them")
    assert p.SPCB_FLOOR - d >= 1.0
    pocket_ceiling_span = p.SPCB_LENGTH + 2 * p.SPCB_POCKET_CLEAR
    print(f"pocket {pocket_ceiling_span:.1f} x {p.SPCB_Z[1] - p.SPCB_Z[0] + 2 * p.SPCB_POCKET_CLEAR:.1f}, "
          f"{SPCB_TOP - Y_BOT:.2f} deep; screws at x {p.SPCB_SCREW_X}, z {p.SPCB_SCREW_Z} "
          f"({p.SCREW_LENGTH - p.SPCB_THICK:.1f} mm into the back wall)")
    wall = (sl.Z0 - sl.ZB)
    assert sl.ZB < p.SPCB_SCREW_Z - p.SCREW_HEAD_DIA / 2 and p.SPCB_Z[0] < p.SPCB_SCREW_Z - p.SCREW_HEAD_DIA / 2
    print(f"back wall {wall:.1f} thick; pilot hole leaves "
          f"{min(p.SPCB_SCREW_Z - sl.ZB, sl.Z0 - p.SPCB_SCREW_Z) - p.PILOT_HOLE_DIA / 2:.2f} each side")
    plunger_low = sl.BALL_Y - p.PLUNGER_TAP_DIA / 2
    pilot_top = SPCB_TOP + p.HOLE_DEPTH
    near = min(abs(abs(x) - p.PLUNGER_X) for x in p.SPCB_SCREW_X)
    print(f"pilot holes reach y {pilot_top:.2f}; plunger holes start at y {plunger_low:.2f}, "
          f"nearest screw {near:.0f} mm from a plunger in x")
    assert pilot_top < plunger_low or near > p.PLUNGER_TAP_DIA


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    slot = make_slot()
    front, back = cp.make_front(), cp.make_back()
    pcb = cp.make_board(pushed_up=True)
    board = make_board()
    pins = make_pins(seated=True)
    plungers, free_tip, body_face = sl.make_plungers()
    export_step(slot, str(OUT / "slot_pcb.step"))
    export_stl(slot, str(OUT / "slot_pcb.stl"))
    export_stl(board, str(OUT / "slot_pcb_board.stl"))
    export_stl(Compound(pins), str(OUT / "slot_pcb_pins.stl"))
    export_stl(Compound(make_pins(seated=False)), str(OUT / "slot_pcb_pins_free.stl"))
    export_stl(Compound(make_screws()), str(OUT / "slot_pcb_screws.stl"))
    export_stl(Compound(plungers), str(OUT / "slot_pcb_plunger.stl"))
    fwd = Pos(0, 0, sl.CART_SHIFT_Z)
    export_step(Compound([slot, board, *pins, *plungers, fwd * front, fwd * back, fwd * pcb]),
                str(OUT / "slot_pcb_assembly.step"))
    bb = slot.bounding_box()
    print(f"slot_pcb: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm, volume {slot.volume / 1000:.2f} cm^3")

    # Sections: across the slot through a pin (keep x below it) and through a screw.
    parts = {"slot": slot, "board": board, "pins": Compound(pins), "front": fwd * front,
             "back": fwd * back, "pcb": fwd * pcb, "screws": Compound(make_screws())}
    for name, x in (("pin", p.CPAD_X[4]), ("screw", p.SPCB_SCREW_X[2])):
        keep = Pos(x - 100, 0, 0) * Box(200, 200, 200)
        for part_name, part in parts.items():
            export_stl(part & keep, str(OUT / f"slot_pcb_section_{name}_{part_name}.stl"))
    sl.check(slot, front, back, plungers, free_tip, body_face)
    check(slot, front, back, board, pcb, pins)
