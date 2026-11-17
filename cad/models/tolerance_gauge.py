"""Tolerance gauge: a plate of slots at increasing clearances plus one test tab.

Print both flat as modelled. Push the tab into each slot; the tightest slot
that still slides the way you want is your FIT_CLEARANCE (see params.py).

Run (from cad/):  uv run python models/tolerance_gauge.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from build123d import Box, Pos, Text, export_step, extrude

import params as p

OUT = Path(__file__).resolve().parent.parent / "out"


def make_gauge():
    n = len(p.GAUGE_CLEARANCES)
    cmax = max(p.GAUGE_CLEARANCES)
    pitch = p.TAB_THICKNESS + 2 * cmax + p.GAUGE_WALL
    label_band = p.GAUGE_LABEL_SIZE + 3.0

    length = n * pitch + p.GAUGE_WALL
    width = p.TAB_WIDTH + 2 * cmax + 2 * p.GAUGE_WALL + label_band
    h = p.GAUGE_HEIGHT

    plate = Pos(0, 0, h / 2) * Box(length, width, h)

    slot_y = label_band / 2
    label_y = -width / 2 + p.GAUGE_WALL / 2 + label_band / 2

    for i, c in enumerate(p.GAUGE_CLEARANCES):
        x = (i - (n - 1) / 2) * pitch
        slot = Box(p.TAB_THICKNESS + 2 * c, p.TAB_WIDTH + 2 * c, h)
        plate -= Pos(x, slot_y, h / 2) * slot

        label = Text(f"{c:.2f}"[1:], font_size=p.GAUGE_LABEL_SIZE)
        plate -= Pos(x, label_y, h - p.GAUGE_LABEL_DEPTH) * extrude(
            label, p.GAUGE_LABEL_DEPTH
        )
    return plate


def make_tab():
    t = p.TAB_THICKNESS
    tongue = Pos(p.TAB_TONGUE / 2, 0, t / 2) * Box(p.TAB_TONGUE, p.TAB_WIDTH, t)
    handle = Pos(-p.TAB_HANDLE / 2, 0, t / 2) * Box(
        p.TAB_HANDLE, p.TAB_HANDLE_WIDTH, t
    )
    return tongue + handle


def report(name, part):
    bb = part.bounding_box()
    print(
        f"{name}: {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm, "
        f"volume {part.volume / 1000:.2f} cm3, valid={part.is_valid}"
    )


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    gauge, tab = make_gauge(), make_tab()
    report("gauge", gauge)
    report("tab", tab)
    export_step(gauge, str(OUT / "tolerance_gauge.step"))
    export_step(tab, str(OUT / "tolerance_tab.step"))
    print(f"wrote STEP files to {OUT}")
