"""Cartridge with a contact PCB clamped in its bottom edge (successor to cartridge.py).

Same shells as cartridge.py (outline, label, screws, alignment lip, slot
tracks and detent seats), with three changes:
  - The internal ribs are gone (front ribs and inner ribs). Revisit after a
    v1 print with the board in it.
  - Across the board's length the bottom wall becomes a window frame. A lip
    from each half runs under one long edge of the board, a ledge over it, and
    the board sits in the groove between. The pins push the board up against
    the ledges; the lips stop it dropping out. The seam (Z = SPLIT_Z) runs
    through the board, so each half carries one lip and one ledge, and the
    board drops into the back half before the front half closes over it.
  - The gold contact pads on the board's underside show through the window,
    recessed by the lip thickness. The slot's pins stand that much taller.

The board (electronics/cartridge_pcb, 81 x 7.9 x 1.6 mm) is modelled as a
plain slab with its pads, plus an envelope above it where parts and
connector plugs go; the checks assert nothing printed enters either.

Print orientation: as cartridge.py, both halves face-down. The lips and
ledges are walls in Y (whole lines); their Z faces are whole layers from each
half's face.

Run (from cad/):  uv run python models/cartridge_pcb.py
Outputs to cad/out/: cartridge_pcb_front/back .step/.stl, cartridge_pcb_board
.step/.stl, cartridge_pcb_pads.stl, cartridge_pcb_assembly.step,
cartridge_pcb_section_*.stl (cuts across the bottom edge, for render checks).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build123d import Axis, Box, Compound, Pos, chamfer, export_step, export_stl

import cartridge as c
import params as p

OUT = c.OUT
L, H, T = c.L, c.H, c.T
BOTTOM = c.BOTTOM_Y

# Board and frame, in the cartridge frame.
PZ0, PZ1 = p.CPCB_POCKET_Z
WZ0, WZ1 = p.CPCB_WINDOW_Z
BZ0 = (PZ0 + PZ1) / 2 - p.CPCB_WIDTH / 2
BZ1 = BZ0 + p.CPCB_WIDTH
BX = p.CPCB_LENGTH / 2
POCKET_X = BX + p.CPCB_END_CLEAR
WINDOW_X = POCKET_X - p.CPCB_END_LIP
GROOVE_Y0 = BOTTOM + p.CPCB_LIP                             # board rests here
GROOVE_Y1 = GROOVE_Y0 + p.CPCB_THICK + p.CPCB_GROOVE_PLAY   # ledge underside
LEDGE_Y1 = GROOVE_Y1 + p.CPCB_LEDGE
PAD_Y_SEATED = GROOVE_Y1 - p.CPCB_THICK                     # board pushed up by the pins


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def frame():
    """Lips, ledges and end lips around the board, before splitting at the seam."""
    f = box(-POCKET_X, POCKET_X, BOTTOM, LEDGE_Y1, PZ0, PZ1)
    f -= box(-POCKET_X - 1, POCKET_X + 1, GROOVE_Y0, GROOVE_Y1, PZ0 - 1, PZ1 + 1)   # groove
    f -= box(-WINDOW_X, WINDOW_X, BOTTOM - 1, GROOVE_Y0 + 0.01, WZ0, WZ1)           # window
    f -= box(-POCKET_X - 1, POCKET_X + 1, GROOVE_Y1 - 0.01, LEDGE_Y1 + 1, WZ0, WZ1)  # parts above
    return f


def bay(half, z0, z1):
    """Replace the bottom wall across the board's length with the frame."""
    half -= box(-POCKET_X, POCKET_X, BOTTOM - 1, LEDGE_Y1, PZ0, PZ1)
    return half + (frame() & box(-L, L, BOTTOM - 1, LEDGE_Y1 + 1, z0, z1))


def make_front():
    front = c.prism(c.outline(), c.SPLIT_Z, T)
    front = chamfer(front.edges().group_by(Axis.Z)[-1], p.CART_EDGE_CHAMFER)
    front -= c.prism(c.outline(p.WALL), c.SPLIT_Z, c.SKIN_FRONT_Z)
    front += c.prism(c.circles(c.BOSS_R), c.JOINT_Z, c.SKIN_FRONT_Z) & c.prism(c.outline(), c.SPLIT_Z, T)
    rebate = c.band(p.SKIRT, p.WALL + 0.05) - c.circles(c.KEEP_R) - c.rib_zones()
    front -= c.prism(rebate, c.SPLIT_Z, c.SPLIT_Z + p.LIP_HEIGHT + p.LIP_TOP_GAP)
    front -= c.prism(c.label_face(), T - p.LABEL_DEPTH, T)
    front -= c.engraving()
    front -= c.prism(c.circles(p.COUNTERBORE_DIA / 2), c.CB_FLOOR_Z, T)
    lh, cl = p.LAYER_HEIGHT, p.SCREW_CLEARANCE_DIA
    for x, y in c.screw_positions():
        slot = Pos(x, y) * c.Rectangle(p.COUNTERBORE_DIA, cl) & Pos(x, y) * c.Circle(p.COUNTERBORE_DIA / 2)
        front -= c.prism(slot, c.CB_FLOOR_Z - lh, c.CB_FLOOR_Z + 0.01)
        front -= c.prism(Pos(x, y) * c.Rectangle(cl, cl), c.CB_FLOOR_Z - 2 * lh, c.CB_FLOOR_Z)
    front -= c.prism(c.circles(cl / 2), c.JOINT_Z - 0.01, c.CB_FLOOR_Z - 2 * lh + 0.01)
    front = bay(front, c.SPLIT_Z, T + 1)
    return c.cut_ribs(front)


def make_back():
    back = c.prism(c.outline(), 0, c.SPLIT_Z)
    back = chamfer(back.edges().group_by(Axis.Z)[0], p.CART_EDGE_CHAMFER)
    back -= c.prism(c.outline(p.WALL), p.SKIN_BACK, c.SPLIT_Z)
    above = c.outline(p.WALL + p.LIP_CLEARANCE)
    posts = c.circles(c.POST_R)
    r = p.SCREW_ROW_INSET
    webs = None
    for sx in (-1, 1):
        w = (Pos(sx * c.BOT_SX + sx * r / 2, c.BOT_SY) * c.Rectangle(r, 2 * c.POST_R)
             + Pos(sx * c.BOT_SX, c.BOT_SY - r / 2) * c.Rectangle(2 * c.POST_R, r)
             + Pos(sx * c.TOP_SX, c.TOP_SY + r / 2) * c.Rectangle(2 * c.POST_R, r))
        webs = w if webs is None else webs + w
    back += c.prism(posts + webs, p.SKIN_BACK - 0.01, c.SPLIT_Z) & c.prism(c.outline(), 0, c.SPLIT_Z)
    back += c.prism(posts & above, c.SPLIT_Z - 0.01, c.JOINT_Z)
    lip_in = p.SKIRT + p.LIP_CLEARANCE
    lip = c.band(lip_in, lip_in + p.LIP_THICKNESS) - c.circles(c.KEEP_R) - c.rib_zones()
    back += c.prism(lip, c.SPLIT_Z - 0.01, c.SPLIT_Z + p.LIP_HEIGHT)
    pad_h = p.TRACK_LENGTH + 2
    for sx in (-1, 1):
        pad = Pos(sx * (L / 2 - p.TRACK_PAD / 2), BOTTOM + pad_h / 2) * c.Rectangle(p.TRACK_PAD, pad_h)
        back += c.prism(pad & c.outline(), p.SKIN_BACK - 0.01, c.SPLIT_Z)
        seat_pad = Pos(sx * p.PLUNGER_X, (BOTTOM + c.SEAT_Y + p.DETENT_SEAT_R + 2) / 2) * c.Rectangle(
            p.DETENT_LANE + 3, c.SEAT_Y + p.DETENT_SEAT_R + 2 - BOTTOM)
        back += c.prism(seat_pad & c.outline(), p.SKIN_BACK - 0.01, p.SKIN_BACK + p.DETENT_PAD)
    back = bay(back, -1, c.SPLIT_Z)
    back -= c.tracks()
    back -= c.detent_seats()
    back -= c.prism(c.circles(c.HOLE_DIA / 2), c.JOINT_Z - p.HOLE_DEPTH, c.JOINT_Z + 0.01)
    return c.cut_ribs(back)


def make_board(pushed_up=False):
    """The PCB as a slab, resting on the lips (or pushed up against the ledges)."""
    y0 = PAD_Y_SEATED if pushed_up else GROOVE_Y0
    b = box(-BX, BX, y0, y0 + p.CPCB_THICK, BZ0, BZ1)
    return chamfer(b.edges().filter_by(Axis.Y), p.CPCB_CORNER_CHAMFER)


def make_pads(pushed_up=False):
    y0 = PAD_Y_SEATED if pushed_up else GROOVE_Y0
    zc, (w, d) = (BZ0 + BZ1) / 2, p.CPAD_SIZE
    return [box(x - w / 2, x + w / 2, y0 - 0.05, y0, zc - d / 2, zc + d / 2) for x in p.CPAD_X]


def parts_envelope():
    """Where parts and connector plugs may go above the board (board pushed up)."""
    k = p.CPCB_PART_KEEPOUT
    y0 = PAD_Y_SEATED + p.CPCB_THICK
    env = box(-BX + 0.5, BX - 0.5, y0 + 0.01, y0 + p.CPCB_PART_HEIGHT, WZ0 + k, WZ1 - k)
    # The back skin is thicker behind the detent seats: parts there stay in front of it.
    for x0, x1 in seat_zones():
        env -= box(x0, x1, y0, y0 + p.CPCB_PART_HEIGHT + 1, 0, SEAT_PAD_Z + k)
    return env


SEAT_PAD_Z = p.SKIN_BACK + p.DETENT_PAD


def seat_zones():
    """X ranges where the thickened back skin behind the detent seats narrows the parts area."""
    hw = (p.DETENT_LANE + 3) / 2
    return [(sx * p.PLUNGER_X - hw, sx * p.PLUNGER_X + hw) for sx in (-1, 1)]


def check(front, back):
    ov = (front & back).volume
    print(f"halves overlap volume: {ov:.4f} mm^3 (want 0)")
    assert ov < 1e-3, "halves overlap"
    for name, up in (("resting on the lips", False), ("pushed up by the pins", True)):
        b = make_board(up)
        ov = (b & front).volume + (b & back).volume
        print(f"board / shell overlap, {name}: {ov:.4f} mm^3 (want 0)")
        assert ov < 1e-3, f"board hits the shell ({name})"
    env = parts_envelope()
    ov = (env & front).volume + (env & back).volume
    narrow = WZ1 - p.CPCB_PART_KEEPOUT - (SEAT_PAD_Z + p.CPCB_PART_KEEPOUT)
    print(f"parts envelope {2 * (BX - 0.5):.1f} x {WZ1 - WZ0 - 2 * p.CPCB_PART_KEEPOUT:.2f} x "
          f"{p.CPCB_PART_HEIGHT} mm over the board ({narrow:.2f} wide at x "
          + ", ".join(f"{a:+.1f}..{b:+.1f}" for a, b in seat_zones())
          + f", behind the detent seats): overlap {ov:.4f} mm^3 (want 0)")
    assert ov < 1e-3, "shell enters the parts envelope"

    pocket = PZ1 - PZ0
    side = (pocket - p.CPCB_WIDTH) / 2
    lip_cover = (WZ0 - BZ0, BZ1 - WZ1)
    print(f"pocket z {PZ0:.2f}-{PZ1:.2f} ({pocket:.2f} wide) for a {p.CPCB_WIDTH} board: "
          f"{side:.2f} per side; board z {BZ0:.2f}-{BZ1:.2f}")
    print(f"window z {WZ0:.2f}-{WZ1:.2f} ({WZ1 - WZ0:.2f} wide), x +/-{WINDOW_X:.2f}; lips cover "
          f"{lip_cover[0]:.2f} / {lip_cover[1]:.2f} of the board edges; pads {p.CPAD_SIZE[1]} across leave "
          f"{(WZ1 - WZ0 - p.CPAD_SIZE[1]) / 2:.2f} each side")
    assert side >= 0.2 - 1e-6 and min(lip_cover) >= 0.4
    assert WZ1 - WZ0 - p.CPAD_SIZE[1] >= 2.0, "pads too close to the window edges"
    assert max(abs(x) for x in p.CPAD_X) + p.CPAD_SIZE[0] / 2 < WINDOW_X - 1, "end pad under the end lip"
    print(f"board x +/-{BX:.2f}, pocket x +/-{POCKET_X:.2f}; bottom screw posts start at x "
          f"+/-{c.BOT_SX - c.POST_R:.2f}")
    assert POCKET_X < c.BOT_SX - c.POST_R, "pocket runs into the bottom screw posts"
    # The chamfered corners must stay hidden under the lips: the window's
    # corners have to lie on the board.
    k = p.CPCB_CORNER_CHAMFER
    corner_gap = (WINDOW_X - (BX - k)) - (WZ0 - BZ0)    # > 0 means the cut corner shows
    print(f"corner chamfer {k} mm: window corner {-corner_gap:.2f} mm inside the chamfer line (want > 0)")
    assert corner_gap < 0, "chamfered board corner shows through the window"
    print(f"lip {p.CPCB_LIP:.2f} (y), groove {GROOVE_Y1 - GROOVE_Y0:.2f} for a {p.CPCB_THICK} board, "
          f"ledge {p.CPCB_LEDGE:.2f}; pads {PAD_Y_SEATED - BOTTOM:.2f} above the bottom face when seated")
    # Whole layers from each half's face for every Z face of the frame.
    for name, z, face in (("back pocket", PZ0, 0), ("back window", WZ0, 0),
                          ("front pocket", PZ1, T), ("front window", WZ1, T)):
        n = abs(z - face) / p.LAYER_HEIGHT
        assert abs(n - round(n)) < 1e-6, f"{name} face not on a whole layer"
    for name, v in (("lip", p.CPCB_LIP), ("ledge", p.CPCB_LEDGE)):
        n = v / p.LINE_WIDTH
        assert abs(n - round(n)) < 1e-6, f"{name} not whole lines"
    print("frame faces on whole layers, lip and ledge whole lines")

    # Thinnest wall: the back wall behind the board where the detent entry
    # ramp is cut into the back face (x = +/-PLUNGER_X).
    import math
    ramp_len = p.DETENT_RAMP_DEPTH / math.tan(math.radians(p.DETENT_RAMP_ANGLE))
    depth_at_groove = max(0.0, p.DETENT_RAMP_DEPTH * (1 - (GROOVE_Y0 - BOTTOM) / ramp_len))
    print(f"back wall behind the board at the detent ramp: {PZ0 - depth_at_groove:.2f} mm "
          f"(pocket face {PZ0:.2f} less ramp {depth_at_groove:.2f})")
    assert PZ0 - depth_at_groove >= 3 * p.LINE_WIDTH - 1e-6


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    front, back = make_front(), make_back()
    board, pads = make_board(), make_pads()
    for name, part in (("cartridge_pcb_front", front), ("cartridge_pcb_back", back),
                       ("cartridge_pcb_board", board)):
        export_step(part, str(OUT / f"{name}.step"))
        export_stl(part, str(OUT / f"{name}.stl"))
        c.report(name, part)
    export_stl(Compound(pads), str(OUT / "cartridge_pcb_pads.stl"))
    export_step(Compound([front, back, board, *pads]), str(OUT / "cartridge_pcb_assembly.step"))

    # Sections across the bottom edge (keep x below the cut): mid-board, through
    # the right detent seat, and through the board's right end.
    for name, x in (("mid", 0.0), ("seat", p.PLUNGER_X), ("end", BX - 0.3)):
        keep = Pos(x - 100, 0, T / 2) * Box(200, H + 2, T + 2)
        for part_name, part in (("front", front), ("back", back), ("board", board)):
            export_stl(part & keep, str(OUT / f"cartridge_pcb_section_{name}_{part_name}.stl"))
    check(front, back)
