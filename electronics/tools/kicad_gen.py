"""Write KiCad schematics, symbols and footprints from a plain Python netlist.

The boards are small, so instead of drawing wires every symbol pin gets a net
label at its end. Two pins with the same label are connected. Symbols come
from KiCad's own libraries (copied into the schematic, as KiCad does) or from
the project library `electronics/lib/lasertrack.kicad_sym`.

Used by `electronics/tools/boards.py`; nothing here knows about LaserTrack.
"""

import json
import re
import uuid
from pathlib import Path

KICAD = Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport")
STOCK_SYMBOLS = KICAD / "symbols"
LIB_DIR = Path(__file__).resolve().parent.parent / "lib"
LOCAL_LIB = "lasertrack"
NS = uuid.UUID("6f1c2a52-6d0e-4d9b-9a35-2f5e0f6c1a10")
GRID = 2.54


# --- S-expressions ----------------------------------------------------------

def parse(text):
    toks = re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', text)
    stack = [[]]
    for t in toks:
        if t == "(":
            stack.append([])
        elif t == ")":
            done = stack.pop()
            stack[-1].append(done)
        else:
            stack[-1].append(t)
    return stack[0][0]


def dump(x, indent=0):
    if not isinstance(x, list):
        return x
    pad = "\t" * indent
    if all(not isinstance(y, list) for y in x):
        return "(" + " ".join(x) + ")"
    parts = []
    for y in x:
        parts.append(dump(y, indent + 1) if isinstance(y, list) else y)
    head = [p for p in parts[:2] if not p.startswith("(")]
    rest = parts[len(head):]
    return "(" + " ".join(head) + "".join("\n" + pad + "\t" + r for r in rest) + "\n" + pad + ")"


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def uq(s):
    return s[1:-1] if s.startswith('"') else s


def child(x, key):
    for y in x:
        if isinstance(y, list) and y and y[0] == key:
            return y
    return None


def uid(*parts):
    return str(uuid.uuid5(NS, "/".join(map(str, parts))))


# --- Symbols ----------------------------------------------------------------

_libs = {}


def _lib(name):
    if name not in _libs:
        path = LIB_DIR / f"{name}.kicad_sym" if name == LOCAL_LIB else STOCK_SYMBOLS / f"{name}.kicad_sym"
        _libs[name] = parse(path.read_text())
    return _libs[name]


def _find(lib, name):
    for e in _lib(lib):
        if isinstance(e, list) and e[0] == "symbol" and uq(e[1]) == name:
            return e
    raise KeyError(f"{lib}:{name} not found")


def load_symbol(lib_id):
    """The symbol as it is embedded in a schematic: renamed 'Lib:Name', with any
    'extends' resolved so the body and pins are included."""
    lib, name = lib_id.split(":")
    sym = _find(lib, name)
    ext = child(sym, "extends")
    if ext:
        parent_name = uq(ext[1])
        parent = _find(lib, parent_name)
        props = [y for y in sym if isinstance(y, list) and y[0] == "property"]
        body = []
        for y in parent[2:]:
            if isinstance(y, list) and y[0] == "property":
                continue
            if isinstance(y, list) and y[0] == "symbol":
                y = ["symbol", q(uq(y[1]).replace(parent_name, name, 1))] + y[2:]
            body.append(y)
        keep = [y for y in sym[2:] if isinstance(y, list) and y[0] not in ("property", "extends")]
        sym = ["symbol", q(name)] + keep + props + body
    sym = [sym[0], q(lib_id)] + sym[2:]
    return sym


def symbol_pins(sym):
    """[(number, name, type, x, y, angle)] in symbol coordinates (Y up)."""
    out = []

    def walk(x):
        if isinstance(x, list):
            if x and x[0] == "pin" and len(x) > 2 and not isinstance(x[1], list):
                at = child(x, "at")
                out.append((uq(child(x, "number")[1]), uq(child(x, "name")[1]), x[1],
                            float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0))
            for y in x:
                walk(y)
    walk(sym)
    return out


def symbol_extent(sym):
    pins = symbol_pins(sym)
    xs = [p[3] for p in pins] or [0]
    ys = [p[4] for p in pins] or [0]
    return min(xs), max(xs), min(ys), max(ys)


# --- Schematic --------------------------------------------------------------

class Part:
    def __init__(self, ref, lib_id, value, footprint, nets, dnp=False, fields=None, note=None):
        self.ref, self.lib_id, self.value, self.footprint = ref, lib_id, value, footprint
        self.nets = nets            # {pin number: net name or None (no connect)}
        self.dnp = dnp
        self.fields = fields or {}
        self.note = note


def _snap(v):
    return round(round(v / GRID) * GRID, 4)


def _effects(size=1.27, justify=None, hide=False):
    e = ["effects", ["font", ["size", str(size), str(size)]]]
    if justify:
        e.append(["justify", justify])
    if hide:
        e.append(["hide", "yes"])
    return e


def write_schematic(path, project, title, rev, groups, paper="A2", notes=()):
    """groups: [(heading, [Part, ...])]. Each group is laid out left to right in
    its own row band."""
    path = Path(path)
    root = uid(project, "root")
    syms = {}
    placed = []
    texts = []
    y = 45.72
    for heading, parts in groups:
        x = 25.4
        row_h = 0
        texts.append((heading, 25.4, y - 6.35, 2.0))
        for part in parts:
            sym = syms.setdefault(part.lib_id, load_symbol(part.lib_id))
            x0, x1, y0, y1 = symbol_extent(sym)
            w = (x1 - x0) + 40.0
            h = (y1 - y0) + 18.0
            if x + w > 560:
                x = 25.4
                y += row_h
                row_h = 0
            px, py = _snap(x - x0 + 20.0), _snap(y + y1 + 6.0)
            placed.append((part, px, py, sym))
            x += w
            row_h = max(row_h, h)
        y += row_h + 7.62

    items = []
    labels = []
    nc = []
    used_pins = set()
    for part, px, py, sym in placed:
        pins = symbol_pins(sym)
        numbers = {p[0] for p in pins}
        missing = numbers - set(part.nets)
        extra = set(part.nets) - numbers
        assert not missing, f"{part.ref}: pins without a net: {sorted(missing)}"
        assert not extra, f"{part.ref}: nets for unknown pins: {sorted(extra)}"
        x0, x1, y0, y1 = symbol_extent(sym)
        if y1 - y0 > 12 and x1 - x0 > 12:        # an IC: name above, value below
            ref_at, val_at = (px + x0, py - y1 - 3.81), (px + x0, py - y0 + 3.81)
        else:
            ref_at, val_at = (px + max(x1, 0) + 2.54, py - 1.27), (px + max(x1, 0) + 2.54, py + 1.27)
        props = [
            ("Reference", part.ref, ref_at, False),
            ("Value", part.value, val_at, False),
            ("Footprint", part.footprint, (px, py + 3.81), True),
            ("Datasheet", part.fields.get("Datasheet", "~"), (px, py + 5.08), True),
        ]
        for k, v in part.fields.items():
            if k != "Datasheet":
                props.append((k, v, (px, py + 6.35), True))
        if part.note:
            props.append(("Note", part.note, (px, py + 7.62), True))
        node = ["symbol", ["lib_id", q(part.lib_id)], ["at", str(px), str(py), "0"], ["unit", "1"],
                ["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "yes"],
                ["dnp", "yes" if part.dnp else "no"], ["uuid", q(uid(project, part.ref))]]
        for k, v, (ax, ay), hide in props:
            node.append(["property", q(k), q(v), ["at", str(round(ax, 4)), str(round(ay, 4)), "0"],
                         _effects(hide=hide, justify="left" if k in ("Reference", "Value") else None)])
        for p in pins:
            node.append(["pin", q(p[0]), ["uuid", q(uid(project, part.ref, "pin", p[0]))]])
        node.append(["instances", ["project", q(project), ["path", q("/" + root),
                                                            ["reference", q(part.ref)], ["unit", "1"]]]])
        items.append(node)
        for num, name, ptype, sx, sy, ang in pins:
            if (part.ref, num) in used_pins:
                continue          # stacked pins (same number twice) get one label
            used_pins.add((part.ref, num))
            ex, ey = round(px + sx, 4), round(py - sy, 4)
            net = part.nets[num]
            if net is None:
                nc.append(["no_connect", ["at", str(ex), str(ey)], ["uuid", q(uid(project, part.ref, num, "nc"))]])
                continue
            out = (ang + 180) % 360
            just = "left" if out in (0, 90) else "right"
            labels.append(["label", q(net), ["at", str(ex), str(ey), str(int(out))],
                           ["fields_autoplaced", "yes"], _effects(justify=just),
                           ["uuid", q(uid(project, part.ref, num, "label"))]])

    sch = ["kicad_sch", ["version", "20231120"], ["generator", q("lasertrack_gen")],
           ["generator_version", q("1.0")], ["uuid", q(root)], ["paper", q(paper)],
           ["title_block", ["title", q(title)], ["rev", q(rev)], ["company", q("LaserTrack")],
            ["comment", "1", q("Generated by electronics/tools/boards.py. Edit that file, not this one.")]],
           ["lib_symbols"] + list(syms.values())]
    sch += items + labels + nc
    for i, (t, tx, ty, size) in enumerate(texts + [(n, 25.4, 20.32 + 3.81 * k, 1.5) for k, n in enumerate(notes)]):
        sch.append(["text", q(t), ["exclude_from_sim", "no"], ["at", str(tx), str(round(ty, 4)), "0"],
                    _effects(size=size, justify="left"), ["uuid", q(uid(project, "text", i))]])
    sch.append(["sheet_instances", ["path", q("/"), ["page", q("1")]]])
    path.write_text(dump(sch) + "\n")

    # Project file and library tables, so KiCad finds the project libraries.
    pro = path.with_suffix(".kicad_pro")
    if not pro.exists():
        pro.write_text(json.dumps({"meta": {"filename": pro.name, "version": 1}}, indent=2) + "\n")
    # Stock libraries are listed too, so kicad-cli finds them without the
    # user's global library tables.
    rel = "${KIPRJMOD}/../lib"
    sym_libs = sorted({p.lib_id.split(":")[0] for g in groups for p in g[1]} - {LOCAL_LIB})
    fp_libs = sorted({p.footprint.split(":")[0] for g in groups for p in g[1] if p.footprint} - {LOCAL_LIB})
    rows = [f'\t(lib (name "{LOCAL_LIB}")(type "KiCad")(uri "{rel}/{LOCAL_LIB}.kicad_sym")(options "")(descr ""))']
    rows += [f'\t(lib (name "{n}")(type "KiCad")(uri "{STOCK_SYMBOLS}/{n}.kicad_sym")(options "")(descr ""))'
             for n in sym_libs]
    (path.parent / "sym-lib-table").write_text("(sym_lib_table\n\t(version 7)\n" + "\n".join(rows) + "\n)\n")
    rows = [f'\t(lib (name "{LOCAL_LIB}")(type "KiCad")(uri "{rel}/{LOCAL_LIB}.pretty")(options "")(descr ""))']
    rows += [f'\t(lib (name "{n}")(type "KiCad")(uri "{KICAD}/footprints/{n}.pretty")(options "")(descr ""))'
             for n in fp_libs]
    (path.parent / "fp-lib-table").write_text("(fp_lib_table\n\t(version 7)\n" + "\n".join(rows) + "\n)\n")
    return placed


# --- Project library: symbols -----------------------------------------------

def ic_symbol(name, ref, footprint, left, right, top=(), bottom=(), descr="", datasheet="~", width=15.24):
    """A rectangle IC. left/right/top/bottom: [(number, name, type)], in order;
    a None entry leaves a gap."""
    pin_len = 2.54
    rows = max(len(left), len(right))
    h = (rows + 1) * GRID
    hw = width / 2
    top_y = _snap(h / 2)
    body = [["rectangle", ["start", str(-hw), str(top_y)], ["end", str(hw), str(round(top_y - h, 4))],
             ["stroke", ["width", "0.254"], ["type", "default"]], ["fill", ["type", "background"]]]]
    pins = []

    def pin(num, pname, ptype, x, y, ang):
        pins.append(["pin", ptype, "line", ["at", str(round(x, 4)), str(round(y, 4)), str(ang)],
                     ["length", str(pin_len)],
                     ["name", q(pname), _effects()], ["number", q(num), _effects()]])

    for i, p in enumerate(left):
        if p:
            pin(p[0], p[1], p[2], -hw - pin_len, top_y - GRID * (i + 1), 0)
    for i, p in enumerate(right):
        if p:
            pin(p[0], p[1], p[2], hw + pin_len, top_y - GRID * (i + 1), 180)
    for i, p in enumerate(top):
        if p:
            pin(p[0], p[1], p[2], (i - (len(top) - 1) / 2) * GRID, top_y + pin_len, 270)
    for i, p in enumerate(bottom):
        if p:
            pin(p[0], p[1], p[2], (i - (len(bottom) - 1) / 2) * GRID, top_y - h - pin_len, 90)
    props = [["property", q("Reference"), q(ref), ["at", "0", str(round(top_y + 3.81, 4)), "0"], _effects()],
             ["property", q("Value"), q(name), ["at", "0", str(round(top_y - h - 3.81, 4)), "0"], _effects()],
             ["property", q("Footprint"), q(footprint), ["at", "0", "0", "0"], _effects(hide=True)],
             ["property", q("Datasheet"), q(datasheet), ["at", "0", "0", "0"], _effects(hide=True)],
             ["property", q("Description"), q(descr), ["at", "0", "0", "0"], _effects(hide=True)]]
    return ["symbol", q(name), ["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "yes"]] + props + [
        ["symbol", q(f"{name}_0_1")] + body, ["symbol", q(f"{name}_1_1")] + pins]


def write_symbol_lib(symbols):
    LIB_DIR.mkdir(parents=True, exist_ok=True)
    lib = ["kicad_symbol_lib", ["version", "20231120"], ["generator", q("lasertrack_gen")],
           ["generator_version", q("1.0")]] + symbols
    (LIB_DIR / f"{LOCAL_LIB}.kicad_sym").write_text(dump(lib) + "\n")
    _libs.pop(LOCAL_LIB, None)


# --- Project library: footprints --------------------------------------------

def _fp(name, descr, items, attr="smd"):
    fp = ["footprint", q(name), ["version", "20240108"], ["generator", q("lasertrack_gen")],
          ["layer", q("F.Cu")], ["descr", q(descr)], ["attr", attr]]
    fp += [["property", q("Reference"), q("REF**"), ["at", "0", "-3", "0"], ["layer", q("F.SilkS")],
            _effects(size=1.0)],
           ["property", q("Value"), q(name), ["at", "0", "3", "0"], ["layer", q("F.Fab")], _effects(size=1.0)]]
    fp += items
    path = LIB_DIR / f"{LOCAL_LIB}.pretty"
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{name}.kicad_mod").write_text(dump(fp) + "\n")


def _rect(layer, w, h, width="0.05"):
    return ["fp_rect", ["start", str(-w / 2), str(-h / 2)], ["end", str(w / 2), str(h / 2)],
            ["stroke", ["width", width], ["type", "solid"]], ["fill", "no"], ["layer", q(layer)]]


def _circle(layer, d, width="0.05"):
    return ["fp_circle", ["center", "0", "0"], ["end", str(d / 2), "0"],
            ["stroke", ["width", width], ["type", "solid"]], ["fill", "no"], ["layer", q(layer)]]


def contact_pad_footprint(name, w, h):
    """Bare gold contact pad: copper and mask opening, no paste (nothing is
    soldered to it). Drawn on F.Cu; place it on the bottom by flipping."""
    pad = ["pad", q("1"), "smd", "rect", ["at", "0", "0"], ["size", str(w), str(h)],
           ["layers", q("F.Cu"), q("F.Mask")]]
    _fp(name, f"{w} x {h} mm bare contact pad for a pogo pin (no paste)",
        [pad, _rect("F.CrtYd", w + 0.5, h + 0.5), _rect("F.Fab", w, h, "0.1")])


def pogo_footprint(name, drill, pad, flange):
    """Through-hole spring pin: plated hole for the tail, flange outline."""
    p = ["pad", q("1"), "thru_hole", "circle", ["at", "0", "0"], ["size", str(pad), str(pad)],
         ["drill", str(drill)], ["layers", q("*.Cu"), q("*.Mask")]]
    _fp(name, f"Mill-Max 0906 spring pin, {drill} mm plated hole, {flange} mm flange",
        [p, _circle("F.SilkS", flange + 0.3, "0.12"), _circle("F.Fab", flange, "0.1"),
         _circle("F.CrtYd", flange + 0.5)], attr="through_hole")


def pad_grid_footprint(name, cols, rows, pitch, pad):
    """Bare SMD pads in a grid, for soldering wires. Numbered along each row."""
    items = []
    for r in range(rows):
        for c in range(cols):
            x = (c - (cols - 1) / 2) * pitch
            y = (r - (rows - 1) / 2) * pitch
            items.append(["pad", q(str(r * cols + c + 1)), "smd", "rect", ["at", str(round(x, 4)), str(round(y, 4))],
                          ["size", str(pad), str(pad)], ["layers", q("F.Cu"), q("F.Mask"), q("F.Paste")]])
    w, h = (cols - 1) * pitch + pad + 0.5, (rows - 1) * pitch + pad + 0.5
    x1 = (-(cols - 1) / 2) * pitch
    y1 = (-(rows - 1) / 2) * pitch - pad / 2 - 0.25
    items += [_rect("F.CrtYd", w, h), _rect("F.Fab", w - 0.5, h - 0.5, "0.1"),
              ["fp_circle", ["center", str(round(x1 - pad / 2 - 0.35, 3)), str(round(y1 + 0.25, 3))],
               ["end", str(round(x1 - pad / 2 - 0.25, 3)), str(round(y1 + 0.25, 3))],
               ["stroke", ["width", "0.1"], ["type", "solid"]], ["fill", "yes"], ["layer", q("F.SilkS")]]]
    _fp(name, f"{rows} x {cols} bare pads, {pitch} mm pitch, for wires", items)
