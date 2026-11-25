"""Check the KiCad boards, with their parts, against the printed parts.

Imports the STEP that KiCad exports for each board (parts included) and
places it in the cartridge / slot frame:
  - cartridge PCB: pushed up against the ledges (seated in the slot), and
    resting on the lips;
  - slot PCB: against its pocket ceiling.
Then asserts zero overlap with the cartridge halves and the slot.

Export the boards first (from the repo root):
  K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
  $K pcb export step --user-origin=150x100mm --subst-models --force \
     -o cad/out/cartridge_pcb_kicad.step electronics/cartridge_pcb/cartridge_pcb.kicad_pcb
  $K pcb export step --user-origin=150x100mm --subst-models --force \
     -o cad/out/slot_pcb_kicad.step electronics/slot_pcb/slot_pcb.kicad_pcb

KiCad's STEP frame: x = board x, y = up the screen (= -board y), z = up from
the board's underside. Board y is CAD z less the board's centre line, so
rotating -90 deg about X maps it onto the CAD frame.

Run (from cad/):  uv run python models/pcb_fit.py
Outputs: cad/out/pcb_fit_cartridge.stl, pcb_fit_slot.stl (boards in place, for renders).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build123d import Compound, Pos, Rot, export_stl, import_step

import cartridge_pcb as cp
import params as p
import slot as sl
import slot_pcb as sp

OUT = cp.OUT


def placed(step, y_bottom, z_centre, dz=0.0):
    shape = import_step(str(step))
    return Pos(0, y_bottom, z_centre + dz) * Rot(-90, 0, 0) * shape


def overlap(a, b):
    total = 0.0
    for s in a.solids():
        r = s & b
        total += r.volume if r is not None else 0.0
    return total


def main():
    front, back = cp.make_front(), cp.make_back()
    zc = (cp.BZ0 + cp.BZ1) / 2
    ok = True

    cart_step = OUT / "cartridge_pcb_kicad.step"
    for name, y0 in (("seated (pushed up)", cp.PAD_Y_SEATED), ("resting on the lips", cp.GROOVE_Y0)):
        board = placed(cart_step, y0, zc)
        bb = board.bounding_box()
        ov = overlap(board, front) + overlap(board, back)
        print(f"cartridge PCB {name}: x {bb.min.X:.2f}..{bb.max.X:.2f}, y {bb.min.Y:.2f}..{bb.max.Y:.2f}, "
              f"z {bb.min.Z:.2f}..{bb.max.Z:.2f}; overlap with the shell {ov:.4f} mm^3 (want 0)")
        ok &= ov < 1e-2
        if y0 == cp.PAD_Y_SEATED:
            export_stl(board, str(OUT / "pcb_fit_cartridge.stl"))
            tall = bb.max.Y - (y0 + p.CPCB_THICK)
            print(f"  tallest part {tall:.2f} mm above the board (envelope {p.CPCB_PART_HEIGHT})")

    slot = sp.make_slot()
    slot_zc = (p.SPCB_Z[0] + p.SPCB_Z[1]) / 2
    board = placed(OUT / "slot_pcb_kicad.step", sp.SPCB_TOP - p.SPCB_THICK, slot_zc)
    bb = board.bounding_box()
    ov = overlap(board, slot)
    print(f"slot PCB: x {bb.min.X:.2f}..{bb.max.X:.2f}, y {bb.min.Y:.2f}..{bb.max.Y:.2f}, "
          f"z {bb.min.Z:.2f}..{bb.max.Z:.2f}; overlap with the slot {ov:.4f} mm^3 (want 0)")
    print(f"  parts hang {sp.Y_BOT - bb.min.Y:.2f} mm below the slot's underside (risers in the box)")
    ok &= ov < 1e-2
    export_stl(board, str(OUT / "pcb_fit_slot.stl"))
    fwd = Pos(0, 0, sl.CART_SHIFT_Z)
    cart_board = placed(cart_step, cp.PAD_Y_SEATED, zc, sl.CART_SHIFT_Z)
    ov = overlap(board, cart_board) + overlap(board, fwd * front) + overlap(board, fwd * back)
    print(f"slot PCB vs seated cartridge and its PCB: {ov:.4f} mm^3 (want 0)")
    ok &= ov < 1e-2
    assert ok, "a board collides with a printed part"


if __name__ == "__main__":
    main()
