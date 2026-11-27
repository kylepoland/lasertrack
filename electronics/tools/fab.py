"""Export JLCPCB fabrication and assembly files for a KiCad board.

Usage (from the repo root, with KiCad closed or the board saved):
    python3 electronics/tools/fab.py electronics/cartridge_pcb/cartridge_pcb.kicad_pcb

Writes to <board folder>/fab/:
    <name>_gerbers.zip   Gerbers + drill files: upload this for the board quote.
    <name>_bom.csv       Assembly BOM (Comment, Designator, Footprint, LCSC Part #).
    <name>_cpl.csv       Pick-and-place (Designator, Mid X, Mid Y, Layer, Rotation).

Settings follow JLCPCB's KiCad guide: Protel extensions, no X2 / netlist
attributes, silkscreen clipped by the solder mask, Excellon drill in mm with
separate PTH / NPTH files. Zones are refilled before plotting.

Left out of the BOM and CPL (not parts JLCPCB places): DNP parts, contact
pads (TP*, gold copper on the board), spare pads (J5), solder jumpers (JP*).
Parts with no LCSC number stay in the BOM with that column blank; JLCPCB's
upload page tries to match them (by Comment and Footprint) and lets you choose. Check every part's
rotation in JLCPCB's placement preview: KiCad and JLCPCB disagree on some
footprints' zero angle.
"""

import csv
import subprocess
import sys
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
LAYERS = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
NOT_PLACED = ("TP", "JP", "J5")  # reference prefixes JLCPCB does not place

# LCSC numbers for parts whose schematic symbol has no LCSC field yet, keyed
# by (value, footprint). All JLCPCB Basic parts (no extended-part fee),
# checked on jlcpcb.com 2026-11-26. To move into boards.py (symbol fields)
# the next time the schematic is regenerated.
LCSC = {
    ("100n", "C_0402_1005Metric"): "C1525",    # Samsung CL05B104KO5NNNC, 16 V X7R
    ("4.7u", "C_0603_1608Metric"): "C19666",   # Samsung CL10A475KO8NNNC, 16 V X5R
    ("10u", "C_0603_1608Metric"): "C19702",    # Samsung CL10A106KP8NNNC, 10 V X5R
    ("Debug", "LED_0603_1608Metric"): "C2286", # KENTO KT-0603R red (~1.3 mA via 1k at 3.3 V)
    ("100", "R_0402_1005Metric"): "C25076",    # UNI-ROYAL 0402WGF1000TCE
    ("100k", "R_0402_1005Metric"): "C25741",   # 0402WGF1003TCE
    ("1k", "R_0402_1005Metric"): "C11702",     # 0402WGF1001TCE
    ("330", "R_0402_1005Metric"): "C25104",    # 0402WGF3300TCE
    ("4.7k", "R_0402_1005Metric"): "C25900",   # 0402WGF4701TCE
}


def cli(*args):
    r = subprocess.run([KICAD_CLI, *args], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"kicad-cli {' '.join(args[:3])} failed:\n{r.stdout}{r.stderr}")


def placed(ref):
    return not ref.startswith(NOT_PLACED)


def package(fp):
    """Plain package name for the BOM's Footprint column. KiCad's names carry
    both sizes ("R_0402_1005Metric"), and JLCPCB's matcher read the metric
    1005 as the imperial 01005."""
    parts = fp.split("_")
    if parts[0] in ("R", "C", "LED") and len(parts) > 1:
        return parts[1]
    return fp


def comment(ref, value, fp):
    """A Comment JLCPCB's matcher can use: the JST part number for the
    connectors (their values are names like "Qwiic"), "LED" for LEDs."""
    if fp.startswith("JST_SH_"):
        return fp.split("_")[2]
    if ref.startswith("D"):
        return "LED"
    return value


def main():
    board = Path(sys.argv[1]).resolve()
    sch = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else board.with_suffix(".kicad_sch")
    name = board.stem
    out = board.parent / "fab"
    out.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        g = Path(tmp) / "gerbers"
        g.mkdir()
        cli("pcb", "export", "gerbers", "--layers", LAYERS, "--no-x2", "--no-netlist",
            "--subtract-soldermask", "--check-zones", "-o", str(g), str(board))
        cli("pcb", "export", "drill", "--format", "excellon", "--excellon-units", "mm",
            "--excellon-zeros-format", "decimal", "--excellon-separate-th",
            "--generate-map", "--map-format", "gerberx2", "-o", str(g) + "/", str(board))
        files = sorted(f for f in g.iterdir() if f.suffix != ".gbrjob")
        with zipfile.ZipFile(out / f"{name}_gerbers.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for f in files:
                z.write(f, f.name)
        print(f"{name}_gerbers.zip: {len(files)} files: {', '.join(f.name for f in files)}")

        raw = Path(tmp) / "bom.csv"
        cli("sch", "export", "bom", "--fields", "Reference,Value,Footprint,LCSC,${DNP}",
            "--labels", "ref,value,footprint,lcsc,dnp", "--group-by", "", "-o", str(raw), str(sch))
        groups = defaultdict(list)
        skipped = []
        with open(raw) as f:
            for row in csv.DictReader(f):
                ref = row["ref"]
                if row["dnp"] or not placed(ref):
                    skipped.append(ref)
                    continue
                fp = row["footprint"].split(":")[-1]
                lcsc = row["lcsc"] or LCSC.get((row["value"], fp), "")
                groups[(comment(ref, row["value"], fp), package(fp), lcsc)].append(ref)
        with open(out / f"{name}_bom.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
            for (value, fp, lcsc), refs in sorted(groups.items(), key=lambda kv: kv[1][0]):
                w.writerow([value, ",".join(refs), fp, lcsc])
        missing = [",".join(r) for (v, fp, l), r in groups.items() if not l]
        print(f"{name}_bom.csv: {len(groups)} lines, {sum(map(len, groups.values()))} parts; "
              f"left out {', '.join(skipped)}")
        print(f"  no LCSC number yet: {'; '.join(missing) or 'none'}")

        raw = Path(tmp) / "pos.csv"
        cli("pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "both",
            "--exclude-dnp", "-o", str(raw), str(board))
        n = 0
        with open(raw) as f, open(out / f"{name}_cpl.csv", "w", newline="") as o:
            w = csv.writer(o)
            w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
            for row in csv.DictReader(f):
                if not placed(row["Ref"]):
                    continue
                side = "Top" if row["Side"].lower() == "top" else "Bottom"
                w.writerow([row["Ref"], f"{float(row['PosX']):.3f}mm", f"{float(row['PosY']):.3f}mm",
                            side, f"{float(row['Rot']):g}"])
                n += 1
        print(f"{name}_cpl.csv: {n} parts")
    print(f"written to {out}")


if __name__ == "__main__":
    main()
