"""NFC readers: the RC522 over SPI, and a simulated one fed by the web page.

Both produce the same events on a queue: ("tag_inserted", uid) and
("tag_removed", None). Only transitions are sent, never every poll.

Why a hand-written RC522 driver: the usual Python libraries (mfrc522,
pi-rc522) stop after the first cascade level and return 4 bytes. NTAG215 tags
have 7-byte UIDs, so those libraries return 0x88 plus 3 bytes of the real UID.
That would mostly work as a key, but it is not the tag's real UID (the one a
phone shows), and two tags could collide. This driver does the full ISO
14443A select, which is ~100 lines.
"""

from __future__ import annotations

import logging
import queue
import threading
import time

log = logging.getLogger(__name__)

# --- RC522 registers and commands (datasheet section 9) ---------------------
CommandReg = 0x01
ComIrqReg = 0x04
DivIrqReg = 0x05
ErrorReg = 0x06
FIFODataReg = 0x09
FIFOLevelReg = 0x0A
ControlReg = 0x0C
BitFramingReg = 0x0D
CollReg = 0x0E
ModeReg = 0x11
TxControlReg = 0x14
TxASKReg = 0x15
RFCfgReg = 0x26
TModeReg = 0x2A
TPrescalerReg = 0x2B
TReloadRegH = 0x2C
TReloadRegL = 0x2D
VersionReg = 0x37

CMD_IDLE = 0x00
CMD_TRANSCEIVE = 0x0C
CMD_SOFTRESET = 0x0F

# --- ISO 14443A card commands ------------------------------------------------
PICC_WUPA = 0x52  # wake-up: answered by idle AND halted cards
PICC_HLTA = 0x50
SEL_CL = (0x93, 0x95, 0x97)  # select, cascade levels 1-3
CASCADE_TAG = 0x88


def crc_a(data: bytes) -> bytes:
    """ISO 14443A CRC (CRC-16/ISO-IEC-14443-3-A), low byte first."""
    crc = 0x6363
    for b in data:
        b ^= crc & 0xFF
        b = (b ^ (b << 4)) & 0xFF
        crc = (crc >> 8) ^ (b << 8) ^ (b << 3) ^ (b >> 4)
    return bytes((crc & 0xFF, (crc >> 8) & 0xFF))


def uid_from_cascade(levels: list[bytes]) -> bytes:
    """Join the 4-byte answers of each cascade level into the real UID.

    Every level but the last starts with the cascade tag 0x88, which is not
    part of the UID.
    """
    uid = b""
    for i, part in enumerate(levels):
        last = i == len(levels) - 1
        if not last:
            if part[0] != CASCADE_TAG:
                raise ValueError(f"cascade level {i + 1} lacks 0x88: {part.hex()}")
            uid += part[1:]
        else:
            uid += part
    return uid


class Rc522:
    """Minimal RC522 driver: enough to read a tag's UID repeatedly."""

    def __init__(self, bus: int = 0, device: int = 0, reset_gpio: int | None = 25, rx_gain: int = 7):
        import spidev  # apt: python3-spidev; only on the Pi

        self._reset = None
        if reset_gpio is not None:
            try:
                from gpiozero import DigitalOutputDevice  # apt: python3-gpiozero

                self._reset = DigitalOutputDevice(reset_gpio, initial_value=False)
                time.sleep(0.05)
                self._reset.on()  # RST high = running; a low pulse is a hard reset
                time.sleep(0.05)
            except Exception as e:  # keep going: RST may be tied high instead
                log.warning("Could not drive RC522 reset on GPIO%s: %s", reset_gpio, e)

        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.max_speed_hz = 1_000_000
        self.spi.mode = 0
        self.init(rx_gain)

    # SPI framing: address byte is (reg << 1), bit 7 set for a read.
    def write(self, reg: int, val: int) -> None:
        self.spi.xfer2([(reg << 1) & 0x7E, val & 0xFF])

    def read(self, reg: int) -> int:
        return self.spi.xfer2([((reg << 1) & 0x7E) | 0x80, 0])[1]

    def set_bits(self, reg: int, mask: int) -> None:
        self.write(reg, self.read(reg) | mask)

    def clear_bits(self, reg: int, mask: int) -> None:
        self.write(reg, self.read(reg) & ~mask)

    def init(self, rx_gain: int) -> None:
        self.write(CommandReg, CMD_SOFTRESET)
        time.sleep(0.05)
        version = self.read(VersionReg)
        if version in (0x00, 0xFF):
            raise RuntimeError(
                f"RC522 not answering on SPI (VersionReg=0x{version:02X}). "
                "Check wiring, 3.3 V power, and that SPI is enabled."
            )
        log.info("RC522 found, version 0x%02X", version)
        # Timer: 40 kHz tick, reload 1000 -> 25 ms timeout per command.
        self.write(TModeReg, 0x80)
        self.write(TPrescalerReg, 0xA9)
        self.write(TReloadRegH, 0x03)
        self.write(TReloadRegL, 0xE8)
        self.write(TxASKReg, 0x40)  # 100% ASK modulation
        self.write(ModeReg, 0x3D)  # CRC preset 0x6363
        self.write(RFCfgReg, (max(0, min(7, rx_gain)) & 0x07) << 4)
        self.set_bits(TxControlReg, 0x03)  # antenna on

    def transceive(self, data: bytes, last_bits: int = 0) -> tuple[bytes, int] | None:
        """Send bytes, return (reply, valid bits in last byte) or None on timeout/error."""
        self.write(CommandReg, CMD_IDLE)
        self.write(ComIrqReg, 0x7F)  # clear interrupt flags
        self.write(FIFOLevelReg, 0x80)  # flush FIFO
        for b in data:
            self.write(FIFODataReg, b)
        self.write(BitFramingReg, last_bits & 0x07)
        self.write(CommandReg, CMD_TRANSCEIVE)
        self.set_bits(BitFramingReg, 0x80)  # StartSend
        deadline = time.monotonic() + 0.04
        while True:
            irq = self.read(ComIrqReg)
            if irq & 0x30:  # RxIRq or IdleIRq: done
                break
            if irq & 0x01 or time.monotonic() > deadline:  # TimerIRq: no card
                self.clear_bits(BitFramingReg, 0x80)
                return None
        self.clear_bits(BitFramingReg, 0x80)
        if self.read(ErrorReg) & 0x1B:  # buffer overflow, collision, parity, protocol
            return None
        n = self.read(FIFOLevelReg)
        valid_bits = self.read(ControlReg) & 0x07
        return bytes(self.read(FIFODataReg) for _ in range(n)), valid_bits

    def read_uid(self) -> bytes | None:
        """Wake a tag, run anticollision/select through all cascade levels, halt it.

        Halting at the end matters: the next poll's WUPA wakes it again, so a
        tag sitting in the slot answers every poll (REQA would skip a halted tag
        and the cartridge would look removed).
        """
        r = self.transceive(bytes([PICC_WUPA]), last_bits=7)
        if not r or len(r[0]) != 2:
            return None
        levels: list[bytes] = []
        for sel in SEL_CL:
            self.clear_bits(CollReg, 0x80)
            r = self.transceive(bytes([sel, 0x20]))
            if not r or len(r[0]) != 5:
                return None
            part, bcc = r[0][:4], r[0][4]
            if part[0] ^ part[1] ^ part[2] ^ part[3] != bcc:
                return None
            frame = bytes([sel, 0x70]) + r[0]
            r = self.transceive(frame + crc_a(frame))
            if not r or len(r[0]) != 3:
                return None
            sak = r[0][0]
            levels.append(part)
            if not sak & 0x04:  # UID complete
                break
        else:
            return None
        halt = bytes([PICC_HLTA, 0x00])
        self.transceive(halt + crc_a(halt))  # no reply expected
        try:
            return uid_from_cascade(levels)
        except ValueError:
            return None

    def antenna_cycle(self) -> None:
        """Switch the RF field off and on. A tag loses power and restarts in its
        idle state, which clears any half-finished exchange from a missed read."""
        self.clear_bits(TxControlReg, 0x03)
        time.sleep(0.005)
        self.set_bits(TxControlReg, 0x03)
        time.sleep(0.005)  # tag needs a few ms of field before it answers

    def read_uid_retry(self) -> bytes | None:
        uid = self.read_uid()
        if uid is None:
            self.antenna_cycle()
            uid = self.read_uid()
        return uid

    def close(self) -> None:
        self.clear_bits(TxControlReg, 0x03)
        self.spi.close()
        if self._reset:
            self._reset.close()


class PresenceTracker:
    """Turns a stream of poll results into inserted/removed transitions.

    Removal is decided by time, not by a count of misses: the tag counts as
    gone only when there has been no good read for `remove_after_s`. A seated
    tag misses the odd read (seen 2026-11-21: three misses in a row every
    second or two), and a count-based rule turned that into eject/insert
    flapping.
    """

    def __init__(self, remove_after_s: float, clock=time.monotonic):
        self.remove_after_s = remove_after_s
        self.clock = clock
        self.current: str | None = None
        self.last_seen = 0.0
        self.reads = 0
        self.misses = 0

    def update(self, uid: str | None) -> tuple[str, str | None] | None:
        now = self.clock()
        if uid is not None:
            self.reads += 1
            self.last_seen = now
            if uid != self.current:
                # A different tag without a gap counts as remove + insert.
                self.current = uid
                return ("tag_inserted", uid)
            return None
        self.misses += 1
        if self.current is not None and now - self.last_seen >= self.remove_after_s:
            self.current = None
            return ("tag_removed", None)
        return None


def format_uid(uid: bytes) -> str:
    return uid.hex(":").upper()


class Rc522Poller(threading.Thread):
    def __init__(self, cfg, events: queue.Queue):
        super().__init__(name="rc522", daemon=True)
        self.cfg = cfg
        self.events = events
        self.stop_flag = threading.Event()

    def run(self) -> None:
        reader = None
        tracker = PresenceTracker(self.cfg.remove_after_s)
        while not self.stop_flag.is_set():
            try:
                if reader is None:
                    reader = Rc522(self.cfg.spi_bus, self.cfg.spi_device, self.cfg.reset_gpio, self.cfg.rx_gain)
                raw = reader.read_uid_retry()
                ev = tracker.update(format_uid(raw) if raw else None)
                if ev:
                    log.info("NFC %s %s (reads %d, misses %d)", *ev, tracker.reads, tracker.misses)
                    self.events.put(ev)
            except Exception as e:
                log.error("RC522 error: %s; retrying in 5 s", e)
                if reader:
                    try:
                        reader.close()
                    except Exception:
                        pass
                reader = None
                time.sleep(5)
            time.sleep(self.cfg.poll_interval_s)
