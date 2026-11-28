"""Shopping list for the two custom boards, from the netlists in boards.py.

Run from the repo root:  python3 electronics/tools/bom.py
Writes electronics/board-parts.md. Kyle buys the parts himself (no JLCPCB
assembly, 2026-11-27), so this lists what to order, not LCSC numbers.

Every fitted part in boards.py must have an entry in ORDER, keyed by
(value, footprint); the script stops if one is missing, so the list can't
silently fall behind the schematic. Parts that are only copper (contact pads,
spare pads, solder jumpers) and power flags are skipped.
"""

import sys
from collections import OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import boards  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "board-parts.md"

R0402 = "1%, 0402, 1/16 W, any brand"
CERAMIC = "ceramic, any brand"

# (value, footprint) -> (what to buy, example part number, notes)
ORDER = {
    # --- ICs -----------------------------------------------------------------
    ("CH32V006F8U6", boards.MCU_FP): (
        "WCH CH32V006F8U6 microcontroller, QFN-20 3 x 3 mm", "CH32V006F8U6 (LCSC C42431288)",
        "Sold by LCSC; not usually stocked by DigiKey or Mouser. Flashed in the slot after assembly"),
    ("SRV05-4", "Package_TO_SOT_SMD:SOT-23-6"): (
        "Semtech SRV05-4 ESD protection array, SOT-23-6", "SRV05-4.TCT", "Marking V05"),
    ("74AHCT1G125GW", "Package_TO_SOT_SMD:SOT-353_SC-70-5"): (
        "74AHCT1G125 single buffer, SC-70-5 (SOT-353)", "Nexperia 74AHCT1G125GW,125",
        "Must be AHCT (5 V supply, 3.3 V-compatible input), not AHC"),
    ("W25Q32JVSS", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"): (
        "Winbond W25Q32JV 4 MB SPI flash, SOIC-8 150 mil", "W25Q32JVSSIQ", "Image storage for a screen"),
    ("TPS2553", "Package_TO_SOT_SMD:SOT-23-6"): (
        "TI TPS2553 current-limited power switch, SOT-23-6", "TPS2553DBVR",
        "Not the TPS2552 (enable is active low) and not a -1 (latches off)"),
    ("AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5"): (
        "Diodes Inc AP2112K-3.3 600 mA LDO, SOT-23-5", "AP2112K-3.3TRG1", ""),
    # --- Connectors and pins -------------------------------------------------
    ("LED A", boards.JST.format(n=3)): (
        "JST SH 3-pin vertical SMD header", "JST BM03B-SRSS-TB", "Mates with SHR-03V-S housings or pre-made SH cables"),
    ("LED B", boards.JST.format(n=3)): None,  # same line as LED A
    ("Qwiic", boards.JST.format(n=4)): (
        "JST SH 4-pin vertical SMD header", "JST BM04B-SRSS-TB", "Standard Qwiic / STEMMA QT cables plug in"),
    ("Display (e-ink)", boards.JST.format(n=8)): (
        "JST SH 8-pin vertical SMD header", "JST BM08B-SRSS-TB", ""),
    ("Pogo 5V", boards.POGO_FP): (
        "Mill-Max 0906-2 spring pin, solder mount", "Mill-Max 0906-2-15-20-75-14-11-0",
        "Hand-soldered from the bottom with the board seated in the printed slot"),
    ("To Pi", "Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical"): (
        "2.54 mm male pin header, 1 x 7, straight", "Any (break from a 1 x 40 strip)", ""),
    ("WCH-LinkE", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"): (
        "2.54 mm male pin header, 1 x 2, straight", "Any (break from a 1 x 40 strip)", ""),
    # --- Power ---------------------------------------------------------------
    ("0.5A hold", "Fuse:Fuse_1206_3216Metric"): (
        "Resettable PTC fuse, 1206, I-hold 0.5 A, I-trip about 1 A, rated 6 V or more",
        "e.g. Bourns MF-NSMF050-2 (check the datasheet)", "Backup only: U1 limits the current first"),
    # --- Passives ------------------------------------------------------------
    ("100n", boards.C0402): ("100 nF capacitor, X7R, 16 V or more, 0402", CERAMIC, ""),
    ("1u", boards.C0402): ("1 µF capacitor, X5R or X7R, 16 V preferred (10 V min), 0402", CERAMIC,
                           "Two of the three sit on 5 V"),
    ("4.7u", boards.C0603): ("4.7 µF capacitor, X5R or X7R, 10 V or more, 0603", CERAMIC, ""),
    ("10u", boards.C0603): ("10 µF capacitor, X5R or X7R, 16 V preferred (10 V min), 0603", CERAMIC,
                            "On 5 V: a 16 V part keeps more of its capacitance there"),
    ("100", boards.R0402): ("100 Ω resistor", R0402, ""),
    ("330", boards.R0402): ("330 Ω resistor", R0402, ""),
    ("1k", boards.R0402): ("1 kΩ resistor", R0402, ""),
    ("4.7k", boards.R0402): ("4.7 kΩ resistor", R0402, ""),
    ("10k", boards.R0402): ("10 kΩ resistor", R0402, ""),
    ("43.2k", boards.R0402): ("43.2 kΩ resistor", "1% or better, 0402 (E96 value)",
                              "Sets U1's current limit, about 0.6 A: must be 1%"),
    ("100k", boards.R0402): ("100 kΩ resistor", R0402, ""),
    ("Debug", "LED_SMD:LED_0603_1608Metric"): ("LED, 0603, any colour (red is brightest at 1 mA)",
                                               "Any", "Cathode mark toward pad 1"),
}
PREFIX_ORDER = ["U", "P", "J", "F", "D", "C", "R"]   # table order: ICs, pins, connectors, ... resistors


def key_for(part):
    """Parts that are the same thing to buy share one ORDER entry."""
    if part.value.startswith("Pogo "):
        return ("Pogo 5V", part.footprint)
    if part.value == "LED B":
        return ("LED A", part.footprint)
    return (part.value, part.footprint)


def ref_key(ref):
    letters = ref.rstrip("0123456789")
    return (PREFIX_ORDER.index(letters) if letters in PREFIX_ORDER else 99, letters, int(ref[len(letters):]))


def copper_only(part):
    return (not part.footprint or part.ref.startswith(("TP", "JP"))
            or part.footprint.startswith("lasertrack:SparePads"))


def lines(groups):
    rows, missing = OrderedDict(), []
    for _, parts in groups:
        for part in parts:
            if copper_only(part):
                continue
            key = key_for(part)
            if ORDER.get(key) is None:
                missing.append(f"{part.ref} {key}")
                continue
            rows.setdefault((key, part.dnp), []).append(part.ref)
    assert not missing, f"no ORDER entry for: {missing}"
    for refs in rows.values():
        refs.sort(key=ref_key)
    return OrderedDict(sorted(rows.items(), key=lambda kv: ref_key(kv[1][0])))


def table(rows, dnp):
    out = ["| Qty | Refs | Part | Example part number | Notes |", "|---|---|---|---|---|"]
    for (key, is_dnp), refs in rows.items():
        if is_dnp != dnp:
            continue
        what, pn, note = ORDER[key]
        out.append(f"| {len(refs)} | {', '.join(refs)} | {what} | {pn} | {note} |")
    return out


def main():
    md = ["# Cartridge and slot boards: parts to buy", "",
          "Generated by `electronics/tools/bom.py` from the netlists in `tools/boards.py`;",
          "edit those and rerun, don't edit this file. Quantities are **per board**.",
          "Why each part is there: `cartridge_pcb.md`, `slot_pcb.md`, `docs/cartridge.md`.", "",
          "Passives (resistors, capacitors) are generic: any brand with the listed",
          "value, size and rating. They come cheap in strips of 10 to 100, so order",
          "plenty of spares; 0402 parts are easy to lose.", ""]
    for title, groups, extra in (
            ("Cartridge PCB", boards.cartridge_groups(),
             "Contact pads, spare pads (J5) and solder jumpers (JP1–JP3) are copper on the board: nothing to buy."),
            ("Slot PCB", boards.slot_groups(),
             "Mounting holes take the M3 low pan heads Kyle already has.")):
        rows = lines(groups)
        md += [f"## {title}", "", *table(rows, False), "", extra, ""]
        if any(d for (_, d) in rows):
            md += ["Not fitted on v1 (footprints are on the board; buy only to add them):", "",
                   *table(rows, True), ""]
    md += ["## Also needed", "",
           "| Item | Notes |", "|---|---|",
           "| Bare PCBs | Gerbers in `cartridge_pcb/fab/` and `slot_pcb/fab/`. Cartridge: 4 layers, 1.6 mm, ENIG, "
           "black mask, 0.3 mm via holes (\"0.3mm/(0.4/0.45mm)\"). Slot: 2 layers, 1.6 mm |",
           "| WCH-LinkE programmer | About $8. Programs cartridges through the slot's J2 |",
           "| Dupont jumper wires, female-female | 7 for the Pi header, 2 for the LinkE |",
           "| JST SH cables | Pre-made SH cables (1 mm) for LED chains and the display; Qwiic cables for J3 |",
           "| Assembly supplies, if assembling by hand | A stencil for the cartridge top side (ordered with "
           "the PCBs), solder paste, and a hot plate or hot-air tool: the QFN and 0402 parts can't be done "
           "with an iron alone |",
           ""]
    OUT.write_text("\n".join(md))
    print(f"wrote {OUT.relative_to(ROOT.parent)}")


if __name__ == "__main__":
    main()
