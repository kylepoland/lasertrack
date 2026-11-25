"""Place the LaserTrack boards in KiCad: outline, footprints, nets, ground pours.

Run with KiCad's own Python (it has the pcbnew module), from the repo root:
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3 \
      electronics/tools/layout.py
Writes electronics/cartridge_pcb/cartridge_pcb.kicad_pcb and
electronics/slot_pcb/slot_pcb.kicad_pcb. Routing is not done here.

Board coordinates (mm): the board centre is at (150, 100). x is the CAD x
(along the cartridge, same pad positions as cad/params.py). y points down on
screen and is the CAD z (thickness) less the board's centre line: +y is the
front (label side, CAD +Z) on both boards, -y the back. Outline, pad and pin
positions come from cad/params.py, so the boards match the CAD.

Rules are JLCPCB's standard 2-layer process with margin: 0.15 mm clearance,
0.2 mm tracks (0.4 mm power), 0.6/0.3 mm vias, tented.
Python 3.9 (KiCad's): no newer syntax here.
"""

import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "cad"))

import pcbnew  # noqa: E402

import boards  # noqa: E402
import params as p  # noqa: E402
from kicad_gen import KICAD, LIB_DIR, uid  # noqa: E402

CX, CY = 150.0, 100.0
CART_ZC = (p.CPCB_POCKET_Z[0] + p.CPCB_POCKET_Z[1]) / 2     # board centre line, CAD z


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(CX + x), mm(CY + y))


def cart_y(z):
    """CAD z (thickness) to board y. Seen from the top (looking down the
    cartridge's -Y), +x right, the cartridge front (+Z) is down the screen."""
    return z - CART_ZC


# --- Placement: ref -> (x, y, rotation, side) --------------------------------
# Cartridge strip: x -40.5..40.5, y -3.95..3.95. Parts stay inside the parts
# zone (|y| <= 3.1: the shell's ledges cover the outer 0.85 mm of each long
# edge) and, at x = +/-25.5..34.5, above y = -2.5 (thicker back skin behind
# the detent seats). Pads are on the bottom, centred, at the CPAD_X positions.
CART_PLACE = {
    # LED A at the left end
    "J1": (-37.0, 0.2, 0, "F"),
    "U3": (-31.7, 1.4, 0, "F"), "C4": (-31.7, -1.7, 0, "F"),
    "JP2": (-28.6, 0.6, 90, "F"), "R6": (-26.5, 2, 90, "F"),
    # LED B
    "J2": (-22.35, 0.2, 0, "F"),
    "U4": (-17.1, 1.4, 0, "F"), "C5": (-17.1, -1.7, 0, "F"),
    "JP3": (-14.0, 0.6, 90, "F"), "R7": (-11.9, 2, 90, "F"), "R1": (-11.9, -2, 90, "F"),
    # Spare pads, ESD, MCU
    "J5": (-8.9, 0, 0, "F"),
    "U2": (-4.8, 0, 90, "F"),
    "C1": (-2.37, 1.2, 90, "F"),
    "U1": (0.5, 0, 0, "F"),
    "C2": (3.7, 0, 90, "F"), "R3": (3.7, 2.6, 0, "F"), "R5": (3.7, -2.6, 0, "F"),
    "C3": (5.75, 1.4, 90, "F"), "C6": (5.75, -1.9, 90, "F"),
    "D1": (7.8, 0, 90, "F"), "R2": (7.8, 2.55, 0, "F"), "R4": (7.8, -2.55, 0, "F"),
    # Qwiic pull-ups, display, flash, Qwiic
    "R8": (10.7, 2.55, 0, "F"), "JP1": (10.7, 0, 0, "F"), "R9": (10.7, -2.55, 0, "F"),
    "J4": (18.55, 0, 0, "F"),
    "U5": (28.35, 0.3, 0, "F"),
    "J3": (36.2, 0.2, 0, "F"),
}
for i, x in enumerate(p.CPAD_X):
    CART_PLACE[f"TP{i + 1}"] = (x, 0.0, 0, "B")

# Slot board: x -42..42, y -9.3..9.3 (CAD z -8.3..10.3 -> y = z - 1.0). Pins on
# top at the pad positions; everything else on the bottom (the top sits
# against the slot's pocket ceiling). Screw heads (5.8 mm) under the board.
SLOT_ZC = (p.SPCB_Z[0] + p.SPCB_Z[1]) / 2
PIN_Y = CART_ZC + p.FIT_CLEARANCE - SLOT_ZC   # pins at CAD z 6.15 (cartridge pushed forward)
SCREW_Y = p.SPCB_SCREW_Z - SLOT_ZC
SLOT_PLACE = {
    # Headers: pin 1 is at the footprint origin; positions shared with the slot's relief grooves.
    "J1": (p.SPCB_HEADERS[0][0], p.SPCB_HEADER_Z - (p.SPCB_Z[0] + p.SPCB_Z[1]) / 2, 90, "B"),
    "J2": (p.SPCB_HEADERS[1][0], p.SPCB_HEADER_Z - (p.SPCB_Z[0] + p.SPCB_Z[1]) / 2, 90, "B"),
    "F1": (-30.0, -1, 0, "B"), "C1": (-30.0, 1.6, 0, "B"),
    "U1": (-24.0, -1, 0, "B"), "C2": (-24.0, 1.9, 0, "B"), "R7": (-20.6, 1.9, 0, "B"),
    "C3": (-20.6, -1, 90, "B"), "R1": (-17.0, -1, 90, "B"),
    "U2": (30.0, -1, 0, "B"), "C4": (30.0, 1.9, 0, "B"), "C5": (33.6, -1, 90, "B"),
    "R2": (-7.0, 2.6, 0, "B"), "R3": (7.0, 2.6, 0, "B"),
    "R4": (10.4, 0.8, 90, "B"), "R5": (12.2, 0.8, 90, "B"),
    "R6": (21.0, 2.6, 0, "B"),
}
for i, x in enumerate(p.CPAD_X):
    SLOT_PLACE[f"P{i + 1}"] = (x, PIN_Y, 0, "F")


# --- Board building -----------------------------------------------------------

def footprint_path(lib):
    if lib == "lasertrack":
        return str(LIB_DIR / "lasertrack.pretty")
    return str(KICAD / "footprints" / f"{lib}.pretty")


def outline(board, length, y0, y1, chamfer):
    hx = length / 2
    k = chamfer
    pts = [(-hx + k, y0), (hx - k, y0), (hx, y0 + k), (hx, y1 - k), (hx - k, y1), (-hx + k, y1),
           (-hx, y1 - k), (-hx, y0 + k)]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pt(*a))
        s.SetEnd(pt(*b))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.1))
        board.Add(s)


def rules(board):
    board.SetCopperLayerCount(2)
    ds = board.GetDesignSettings()
    ds.m_MinClearance = mm(0.15)
    ds.m_TrackMinWidth = mm(0.15)
    ds.m_ViasMinSize = mm(0.5)
    ds.m_MinThroughDrill = mm(0.3)
    ds.m_CopperEdgeClearance = mm(0.3)
    ds.SetBoardThickness(mm(1.6))
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(mm(0.15))
    nc.SetTrackWidth(mm(0.2))
    nc.SetViaDiameter(mm(0.6))
    nc.SetViaDrill(mm(0.3))
    for attr in ("m_TentViasFront", "m_TentViasBack"):
        if hasattr(ds, attr):
            setattr(ds, attr, True)


def add_text(board, text, x, y, layer, size=0.8):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetPosition(pt(x, y))
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(0.15))
    if layer == pcbnew.B_SilkS:
        t.SetMirrored(True)
    board.Add(t)


def ground_zone(board, net, layer, length, y0, y1):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(net)
    z.SetLocalClearance(mm(0.2))
    z.SetMinThickness(mm(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in ((-length / 2, y0), (length / 2, y0), (length / 2, y1), (-length / 2, y1)):
        ol.Append(mm(CX + x), mm(CY + y))
    board.Add(z)
    return z


RULES = {
    "rules": {"min_clearance": 0.15, "min_copper_edge_clearance": 0.3, "min_track_width": 0.15,
              "min_via_diameter": 0.5, "min_via_annular_width": 0.1, "min_through_hole_diameter": 0.3,
              "min_hole_to_hole": 0.25, "min_silk_clearance": 0.0, "solder_mask_min_width": 0.0},
}
NETCLASS = {"name": "Default", "clearance": 0.15, "track_width": 0.2, "via_diameter": 0.6, "via_drill": 0.3,
            "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
            "wire_width": 6, "bus_width": 12, "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)",
            "schematic_color": "rgba(0, 0, 0, 0.000)", "priority": 2147483647}


def write_project_rules(project):
    """DRC reads its constraints from the project file, so they go there."""
    import json
    pro = ROOT / "electronics" / project / f"{project}.kicad_pro"
    data = json.loads(pro.read_text()) if pro.exists() else {}
    data.setdefault("meta", {"filename": pro.name, "version": 1})
    data.setdefault("board", {}).setdefault("design_settings", {}).update(RULES)
    data["net_settings"] = {"classes": [NETCLASS], "meta": {"version": 3}}
    pro.write_text(json.dumps(data, indent=2) + "\n")
    # Mounting holes come from a stock library the schematic doesn't use.
    tbl = pro.parent / "fp-lib-table"
    t = tbl.read_text()
    if '"MountingHole"' not in t:
        row = f'\t(lib (name "MountingHole")(type "KiCad")(uri "{KICAD}/footprints/MountingHole.pretty")(options "")(descr ""))\n'
        tbl.write_text(t.rstrip().rstrip(")") + row + ")\n")


def build(project, groups, place, length, y0, y1, chamfer, texts=(), zones=True, holes=()):
    board = pcbnew.BOARD()
    rules(board)
    outline(board, length, y0, y1, chamfer)
    nets = {}

    def net(name):
        if name not in nets:
            n = pcbnew.NETINFO_ITEM(board, "/" + name)
            board.Add(n)
            nets[name] = n
        return nets[name]

    missing = []
    for _, parts in groups:
        for part in parts:
            if not part.footprint:
                continue          # power flags
            if part.ref not in place:
                missing.append(part.ref)
                continue
            lib, name = part.footprint.split(":")
            fp = pcbnew.FootprintLoad(footprint_path(lib), name)
            fp.SetFPID(pcbnew.LIB_ID(lib, name))
            fp.SetReference(part.ref)
            fp.SetValue(part.value)
            fp.SetPath(pcbnew.KIID_PATH("/" + uid(project, part.ref)))
            x, y, rot, side = place[part.ref]
            fp.SetPosition(pt(x, y))
            fp.SetOrientationDegrees(rot)
            for pad in fp.Pads():
                n = part.nets.get(pad.GetNumber())
                if n:
                    pad.SetNet(net(n))
            if part.dnp and hasattr(fp, "SetDNP"):
                fp.SetDNP(True)
            for k, v in part.fields.items():
                if k == "Datasheet":
                    continue
                try:
                    f = pcbnew.PCB_FIELD(fp, fp.GetNextFieldId(), k)
                    f.SetText(v)
                    f.SetVisible(False)
                    fp.AddField(f)
                except Exception:   # older API: skip the field, the BOM step adds it
                    pass
            fp.Reference().SetVisible(False)
            fp.Value().SetVisible(False)
            board.Add(fp)
            if side == "B":
                try:
                    fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
                except (AttributeError, TypeError):
                    fp.Flip(fp.GetPosition(), False)
    assert not missing, f"{project}: no placement for {missing}"
    for i, (x, y) in enumerate(holes):
        fp = pcbnew.FootprintLoad(footprint_path("MountingHole"), "MountingHole_3.2mm_M3")
        fp.SetFPID(pcbnew.LIB_ID("MountingHole", "MountingHole_3.2mm_M3"))
        fp.SetReference(f"H{i + 1}")
        fp.SetPosition(pt(x, y))
        fp.Reference().SetVisible(False)
        board.Add(fp)
    for text, x, y, layer in texts:
        add_text(board, text, x, y, layer)
    if zones and "GND" in nets:
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            ground_zone(board, nets["GND"], layer, length, y0, y1)
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    write_project_rules(project)
    out = ROOT / "electronics" / project / f"{project}.kicad_pcb"
    pcbnew.SaveBoard(str(out), board)
    print(f"{project}: {len(board.GetFootprints())} footprints, {len(nets)} nets -> {out.relative_to(ROOT)}")
    return board


if __name__ == "__main__":
    w = p.CPCB_WIDTH / 2
    build("cartridge_pcb", boards.cartridge_groups(), CART_PLACE, p.CPCB_LENGTH, -w, w,
          p.CPCB_CORNER_CHAMFER,
          texts=[("LASERTRACK CART v1", 0.0, 3.4, pcbnew.F_Fab)])
    z0, z1 = p.SPCB_Z
    build("slot_pcb", boards.slot_groups(), SLOT_PLACE, p.SPCB_LENGTH, z0 - SLOT_ZC, z1 - SLOT_ZC,
          p.SPCB_CORNER_CHAMFER,
          texts=[("LASERTRACK SLOT v1", 0.0, -6.5, pcbnew.B_SilkS)],
          holes=[(x, SCREW_Y) for x in p.SPCB_SCREW_X])
