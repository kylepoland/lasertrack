"""The two LaserTrack boards as netlists: the cartridge PCB and the slot PCB.

Run from the repo root:  python3 electronics/tools/boards.py
Writes electronics/cartridge_pcb/ and electronics/slot_pcb/ (KiCad projects:
schematic, project file, library tables) and the project library in
electronics/lib/. Then check them:
  kicad-cli sch erc electronics/cartridge_pcb/cartridge_pcb.kicad_sch
  kicad-cli sch erc electronics/slot_pcb/slot_pcb.kicad_sch

Design notes, part choices and the reasons are in docs/cartridge.md; the pin
map is in electronics/cartridge_pcb.md. Pin functions of the CH32V006F8U6 come
from WCH's CH32V006 datasheet V1.8, table 2-1-1 (QFN20 column).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kicad_gen import (Part, contact_pad_footprint, ic_symbol, pad_grid_footprint, pogo_footprint,  # noqa: E402
                       write_schematic, write_symbol_lib)

ROOT = Path(__file__).resolve().parent.parent

R0402 = "Resistor_SMD:R_0402_1005Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
JUMP2 = "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm"
JUMP3 = "Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm"
JST = "Connector_JST:JST_SH_BM{n:02d}B-SRSS-TB_1x{n:02d}-1MP_P1.00mm_Vertical"
MCU_FP = "Package_DFN_QFN:QFN-20-1EP_3x3mm_P0.4mm_EP1.65x1.65mm"
PAD_FP = "lasertrack:ContactPad_3x4mm"
POGO_FP = "lasertrack:MillMax_0906_TH"


def R(ref, value, a, b, **kw):
    return Part(ref, "Device:R", value, R0402, {"1": a, "2": b}, **kw)


def C(ref, value, a, b="GND", fp=C0402, **kw):
    return Part(ref, "Device:C", value, fp, {"1": a, "2": b}, **kw)


def conn(ref, value, nets, fp):
    return Part(ref, f"Connector_Generic:Conn_01x{len(nets):02d}", value, fp,
                {str(i + 1): n for i, n in enumerate(nets)})


def flag(ref, net):
    return Part(ref, "power:PWR_FLAG", "PWR_FLAG", "", {"1": net})


# --- Project library ----------------------------------------------------------

def mcu_symbol():
    io, pw = "bidirectional", "power_in"
    left = [("6", "VDD", pw), None, ("1", "PD7/NRST", io), ("2", "PA1/A1/T1C2", io),
            ("3", "PA2/A0/T1C2N", io), ("5", "PD0/T1C1N/SDA_1", io), None, ("15", "PD1/SWIO", io),
            ("16", "PD2/A3/T1C1/SCK_2", io), ("17", "PD3/A4/T2C2/MOSI_2", io),
            ("18", "PD4/A7/SCK_4", io), ("19", "PD5/A5/TX/MISO_4", io), ("20", "PD6/A6/RX/MOSI_4", io)]
    right = [("7", "PC0/T2C3/TX_3", io), ("8", "PC1/SDA/RX_3", io), ("9", "PC2/SCL", io),
             ("10", "PC3/T1C3", io), ("11", "PC4/A2/T1C4", io), ("12", "PC5/SCK/TX_6/SCL_2", io),
             ("13", "PC6/MOSI/RX_6/SDA_2", io), ("14", "PC7/MISO", io)]
    bottom = [("4", "VSS", pw), ("21", "EP", pw)]
    return ic_symbol(
        "CH32V006F8U6", "U", MCU_FP, left, right, bottom=bottom, width=50.8,
        descr="WCH CH32V006F8U6 RISC-V MCU, 62K flash, 8K RAM, QFN-20 3x3 mm, 0.4 mm pitch. "
              "Exposed pad is VSS. PD7 is also the reset pin and is bonded to PA4 inside the chip.",
        datasheet="https://www.wch-ic.com/products/CH32V006.html")


def tps2553_symbol():
    return ic_symbol(
        "TPS2553DBV", "U", "Package_TO_SOT_SMD:SOT-23-6",
        [("1", "IN", "power_in"), ("3", "EN", "input"), ("4", "~{FAULT}", "open_collector")],
        [("6", "OUT", "power_out"), ("5", "ILIM", "passive"), ("2", "GND", "power_in")],
        width=12.7,
        descr="TI TPS2553 current-limited power switch, 2.5-6.5 V, EN active high, auto-retry, "
              "limit set by R from ILIM to GND (15k-232k), SOT-23-6. Datasheet SLVS841G.",
        datasheet="https://www.ti.com/lit/ds/symlink/tps2553.pdf")


def write_library():
    write_symbol_lib([mcu_symbol(), tps2553_symbol()])
    contact_pad_footprint("ContactPad_3x4mm", 3.0, 4.0)
    # Mill-Max 0906: tail 0.43 dia (0.51 min hole), flange 1.83.
    pogo_footprint("MillMax_0906_TH", 0.6, 1.2, 1.83)
    pad_grid_footprint("SparePads_2x3_P1.5mm", cols=3, rows=2, pitch=1.5, pad=1.1)


# --- Cartridge PCB ------------------------------------------------------------

def cartridge_groups():
    pads = [Part(f"TP{i + 1}", "Connector:TestPoint", name, PAD_FP, {"1": net},
                 note="Bottom side, gold contact pad")
            for i, (name, net) in enumerate([
                ("5V", "+5V"), ("GND", "GND"), ("BOX_TX", "PAD_TX"), ("BOX_RX", "PAD_RX"),
                ("SWIO", "PAD_SWIO"), ("3V3", "+3V3")])]
    contacts = pads + [
        R("R1", "100", "PAD_TX", "CART_RX", note="Box TX -> cartridge RX (PC6)"),
        R("R2", "100", "PAD_RX", "CART_TX", note="Cartridge TX (PC5) -> box RX"),
        R("R3", "100", "PAD_SWIO", "SWIO"),
        R("R4", "4.7k", "PAD_RX", "GND",
          note="Presence: pulls the box RX line low with power off. Strong enough to beat the Pi's "
               "~50k internal pull-up on its RXD pin (0.4 V with the slot's 100k)"),
        Part("U2", "Power_Protection:SRV05-4", "SRV05-4", "Package_TO_SOT_SMD:SOT-23-6",
             {"1": "PAD_TX", "3": "PAD_RX", "4": "PAD_SWIO", "6": None, "5": "+5V", "2": "GND"},
             note="Pin 6 unconnected: on +3V3 its diode to VCC (+5V) would feed the 5 V rail "
                  "while 3.3 V comes up first. The 3V3 pad's 4.7 uF absorbs ESD"),
        flag("#FLG1", "+5V"), flag("#FLG2", "+3V3"), flag("#FLG3", "GND"),
    ]
    mcu = [
        Part("U1", "lasertrack:CH32V006F8U6", "CH32V006F8U6", MCU_FP, {
            "6": "+3V3", "4": "GND", "21": "GND",
            "1": "SPARE_PD7", "2": "DISP_BUSY", "3": "SPARE_PA2", "5": "DISP_RST",
            "15": "SWIO", "16": "LEDA_IO", "17": "LEDB_IO", "18": "SPI_SCK", "19": "SPI_MISO",
            "20": "SPI_MOSI", "7": "DISP_CS", "8": "QW_SDA", "9": "QW_SCL", "10": "DBG_LED",
            "11": "DISP_DC", "12": "CART_TX", "13": "CART_RX", "14": "FLASH_CS"},
            fields={"LCSC": "C42431288"}),
        C("C1", "100n", "+3V3"),
        C("C2", "4.7u", "+3V3", fp=C0603),
        C("C3", "10u", "+5V", fp=C0603),
        R("R5", "1k", "DBG_LED", "DBG_A"),
        Part("D1", "Device:LED", "Debug", "LED_SMD:LED_0603_1608Metric", {"2": "DBG_A", "1": "GND"}),
    ]

    def led_chain(n, conn_ref, buf_ref, cap_ref, jp_ref, r_ref):
        io, buf, sel, out = f"LED{n}_IO", f"LED{n}_BUF", f"LED{n}_SEL", f"LED{n}_OUT"
        return [
            Part(buf_ref, "74xGxx:74AHCT1G125", "74AHCT1G125GW", "Package_TO_SOT_SMD:SOT-353_SC-70-5",
                 {"1": "GND", "2": io, "4": buf, "3": "GND", "5": "+5V"},
                 note="3.3 V -> 5 V level shift for addressable LEDs"),
            C(cap_ref, "100n", "+5V"),
            Part(jp_ref, "Jumper:SolderJumper_3_Bridged12", f"LED {n}: buffered / direct", JUMP3,
                 {"1": buf, "2": sel, "3": io},
                 note="Default 1-2: 5 V buffered. Cut 1-2 and bridge 2-3 for a plain 3.3 V GPIO"),
            R(r_ref, "330", sel, out),
            conn(conn_ref, f"LED {n}", ["+5V", out, "GND"], JST.format(n=3)),
        ]

    leds = led_chain("A", "J1", "U3", "C4", "JP2", "R6") + led_chain("B", "J2", "U4", "C5", "JP3", "R7")
    qwiic = [
        conn("J3", "Qwiic", ["GND", "+3V3", "QW_SDA", "QW_SCL"], JST.format(n=4)),
        R("R8", "4.7k", "QW_SDA", "QW_PU"),
        R("R9", "4.7k", "QW_SCL", "QW_PU"),
        Part("JP1", "Jumper:SolderJumper_2_Bridged", "I2C pull-ups", JUMP2, {"1": "QW_PU", "2": "+3V3"},
             note="Cut to disconnect the pull-ups"),
    ]
    display = [
        conn("J4", "Display (e-ink)",
             ["GND", "+3V3", "SPI_SCK", "SPI_MOSI", "DISP_CS", "DISP_DC", "DISP_RST", "DISP_BUSY"],
             JST.format(n=8)),
    ]
    flash = [
        Part("U5", "Memory_Flash:W25Q32JVSS", "W25Q32JVSS", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
             {"1": "FLASH_CS", "2": "SPI_MISO", "3": "+3V3", "4": "GND", "5": "SPI_MOSI", "6": "SPI_SCK",
              "7": "+3V3", "8": "+3V3"}, dnp=True, note="Image storage, 4 MB. WP and HOLD tied high"),
        C("C6", "100n", "+3V3", dnp=True),
    ]
    spare = [conn("J5", "Spare pads", ["SPI_MISO", "SPARE_PD7", "SPARE_PA2", "+3V3", "+5V", "GND"],
                  "lasertrack:SparePads_2x3_P1.5mm")]
    return [("Contact pads (bottom), protection, presence", contacts),
            ("Microcontroller, decoupling, debug LED", mcu),
            ("LED chains", leds),
            ("Qwiic (I2C)", qwiic),
            ("Display connector (e-ink)", display),
            ("Image flash (not fitted)", flash),
            ("Spare pads", spare)]


# --- Slot PCB -----------------------------------------------------------------

def slot_groups():
    pins = [Part(f"P{i + 1}", "Connector_Generic:Conn_01x01", f"Pogo {name}", POGO_FP, {"1": net},
                 note="Mill-Max 0906-2-15-20-75-14-11-0, hand-soldered")
            for i, (name, net) in enumerate([
                ("5V", "5V_CART"), ("GND", "GND"), ("TX", "POGO_TX"), ("RX", "POGO_RX"),
                ("SWIO", "POGO_SWIO"), ("3V3", "3V3_CART")])]
    headers = [
        conn("J1", "To Pi", ["+5V_PI", "GND", "PI_TXD", "PI_RXD", "PWR_EN", "SENSE", "+3V3_PI"],
             "Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical"),
        conn("J2", "WCH-LinkE", ["GND", "LINK_SWIO"], "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"),
        flag("#FLG1", "+5V_PI"), flag("#FLG2", "GND"), flag("#FLG3", "+3V3_PI"), flag("#FLG4", "+5V_F"),
    ]
    power = [
        Part("F1", "Device:Polyfuse", "0.5A hold", "Fuse:Fuse_1206_3216Metric", {"1": "+5V_PI", "2": "+5V_F"}),
        C("C1", "10u", "+5V_F", fp=C0603),
        Part("U1", "lasertrack:TPS2553DBV", "TPS2553", "Package_TO_SOT_SMD:SOT-23-6",
             {"1": "+5V_F", "2": "GND", "3": "PWR_EN", "4": None, "5": "ILIM", "6": "5V_CART"},
             note="Current-limited switch for both cartridge rails: soft start (about 1 ms), "
                  "limits a short on the pins to about 0.6 A instead of loading the Pi's 5 V"),
        R("R7", "43.2k", "ILIM", "GND", note="Current limit: 544 / 605 / 673 mA min / typ / max (1%, SLVS841G table 9-2)"),
        R("R8", "10k", "5V_CART", "GND", note="Bleeds the 5 V pin to 0 V when switched off (the TPS2553 has no output discharge)"),
        C("C3", "1u", "5V_CART"),
        Part("U2", "Regulator_Linear:AP2112K-3.3", "AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5",
             {"1": "5V_CART", "2": "GND", "3": "PWR_EN", "4": None, "5": "3V3_CART"},
             note="Cartridge 3.3 V, fed from the switched 5 V so 3.3 V never leads 5 V"),
        C("C4", "1u", "5V_CART"),
        C("C5", "1u", "3V3_CART"),
        R("R1", "100k", "PWR_EN", "GND", note="Power off while the Pi boots"),
    ]
    signals = [
        R("R2", "1k", "PI_TXD", "POGO_TX", note="Limits current if a pad is shorted"),
        R("R3", "1k", "PI_RXD", "POGO_RX"),
        R("R4", "100k", "POGO_RX", "+3V3_PI", note="Pull-up: high = empty slot"),
        R("R5", "10k", "POGO_RX", "SENSE", note="Pi reads presence here (low = cartridge in, power off)"),
        R("R6", "1k", "LINK_SWIO", "POGO_SWIO",
          note="Limits current into an unpowered cartridge from the always-on WCH-LinkE"),
    ]
    return [("Pogo pins (6x Mill-Max 0906-2)", pins), ("Connectors to the Pi and programmer", headers),
            ("Power: fuse, 5 V switch, 3.3 V regulator", power), ("Signals and presence", signals)]


if __name__ == "__main__":
    write_library()
    for name, title, groups, notes in (
        ("cartridge_pcb", "LaserTrack cartridge PCB", cartridge_groups(), (
            "Logic 3.3 V from the 3V3 pad; 5 V pad feeds LED chains and add-ons. Pin map: electronics/cartridge_pcb.md",
            "UART to the box on PC5 (TX) / PC6 (RX) = USART1 remap 6; the same pins are I2C remap 2 (SCL/SDA).",
            "SPI remap 4: SCK PD4, MOSI PD6, MISO PD5. Not-fitted parts are marked DNP.")),
        ("slot_pcb", "LaserTrack slot PCB", slot_groups(), (
            "Pogo pins are through-hole, hand-soldered; everything else is SMD on the bottom side.",
            "Pi: 5V pin 2, GND pin 6, TXD GPIO14 pin 8, RXD GPIO15 pin 10, PWR_EN GPIO23 pin 16, SENSE GPIO24 pin 18, 3V3 pin 17.",
            "Keep the Pi's UART TX off (input) until PWR_EN is on, so it never powers an unpowered cartridge through its pin.")),
    ):
        out = ROOT / name
        out.mkdir(exist_ok=True)
        placed = write_schematic(out / f"{name}.kicad_sch", name, title, "v1", groups, notes=notes)
        print(f"{name}: {len(placed)} symbols")
