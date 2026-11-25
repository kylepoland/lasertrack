"""The LaserTrack daemon: one event loop that owns the screen.

Modes:
  CHANNELS   FieldStation42 is playing; our mpv is closed.
  CARTRIDGE  a known cartridge is in; our mpv plays it from Plex.
  UNASSIGNED an unknown cartridge is in; our mpv shows UNASSIGNED CARTRIDGE
             until it is assigned from the web page.

Everything that happens (tag in/out, playback ended, web buttons) arrives as
an event on one queue and is handled on this thread, so there are no races
between the NFC thread, the web server and mpv's IPC thread.
"""

from __future__ import annotations

import logging
import queue
import subprocess
import threading
import time
from dataclasses import dataclass, field

from . import fs42
from .cartridges import Cartridge, CartridgeStore
from .config import Config
from .nfc import Rc522Poller
from .player import Player
from .plex import PlayItem, PlexPlayback

log = logging.getLogger(__name__)

# The Pi has no battery-backed clock: it boots on the last saved time and
# jumps to the real time when NTP syncs. FieldStation42 schedules by the clock,
# so channels must not start before that.
CLOCK_WAIT_S = 120


def clock_synced() -> bool:
    try:
        r = subprocess.run(
            ["timedatectl", "show", "-p", "NTPSynchronized", "--value"],
            capture_output=True, text=True, timeout=5,
        )
        return r.stdout.strip() == "yes"
    except Exception:
        return True  # can't tell: don't block channels forever


def wait_for_clock_sync(timeout_s: float) -> bool:
    end = time.monotonic() + timeout_s
    while time.monotonic() < end:
        if clock_synced():
            return True
        time.sleep(2)
    return clock_synced()


@dataclass
class Status:
    """What the web page shows. Written by the daemon thread only."""

    mode: str = "CHANNELS"
    uid: str | None = None  # cartridge currently in the slot
    last_uid: str | None = None  # last cartridge seen, kept after removal
    cartridge: dict | None = None
    now_playing: str | None = None
    position_s: float = 0.0
    error: str | None = None
    log: list[str] = field(default_factory=list)


class Daemon:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.events: queue.Queue = queue.Queue()
        self.store = CartridgeStore()
        self.plex = PlexPlayback(cfg.plex, cfg.output, self.store)
        self.player = Player(self.events)
        self.status = Status()
        # Cartridge-mode state
        self.cart: Cartridge | None = None
        self.items: list = []
        self.index = 0
        self.item: PlayItem | None = None
        self.last_report = 0.0

    # --- helpers -----------------------------------------------------------------
    def note(self, msg: str) -> None:
        log.info(msg)
        self.status.log = (self.status.log + [time.strftime("%H:%M:%S ") + msg])[-30:]

    def position(self) -> float:
        """Position in the video, in seconds from its true start.

        A direct-played file reports its real time. A Plex transcode that
        starts at an offset may report time from 0 or from the offset,
        depending on the server; anything well below the offset is taken as
        relative.
        """
        t = self.player.get("time-pos")
        if t is None or self.item is None:
            return self.status.position_s
        if self.item.transcoded and self.item.start_s and t < self.item.start_s - 5:
            return self.item.start_s + t
        return float(t)

    def report(self, state: str) -> None:
        if self.item is None:
            return
        pos = self.position()
        self.status.position_s = pos
        self.plex.report(self.item.video, pos, state)
        self.last_report = time.monotonic()

    # --- mode changes --------------------------------------------------------------
    def to_channels(self) -> None:
        """Back to FieldStation42 without the desktop showing in between.

        Our window goes black and stays on top while FS42 starts; it closes
        only once FS42's own window is up and playing.
        """
        if self.item:
            self.report("stopped")
        self.cart, self.items, self.item = None, [], None
        self.status.mode, self.status.cartridge, self.status.now_playing = "CHANNELS", None, None
        if self.player.running:
            self.player.card()  # plain black while the channel tunes in
        if not fs42.is_active(self.cfg.fs42.service):
            fs42.start(self.cfg.fs42.service)
            fs42.wait_on_screen(self.cfg.fs42.path)
        self.player.quit()
        self.note("Channels")

    def leave_channels(self, card_text: str = "") -> None:
        """Put our window on screen first, then stop FS42 underneath it."""
        self.player.card(card_text)
        if fs42.is_active(self.cfg.fs42.service):
            fs42.stop(self.cfg.fs42.service)

    def play_index(self, idx: int, from_start: bool = False) -> None:
        if not 0 <= idx < len(self.items):
            self.item = None
            self.status.now_playing = None
            self.player.card("■ END — remove cartridge")
            self.note("End of cartridge")
            return
        self.index = idx
        self.plex.remember_index(self.cart, idx)
        self.item = self.plex.make_item(self.items[idx], from_start=from_start)
        self.status.now_playing = self.item.title
        self.status.position_s = self.item.start_s
        self.player.play(self.item.url, 0 if self.item.transcoded else self.item.start_s, self.item.title)
        self.report("playing")
        self.note(
            f"Playing {self.item.title} from {self.item.start_s:.0f}s "
            f"({'transcode' if self.item.transcoded else 'direct'})"
        )

    def insert(self, uid: str) -> None:
        self.status.uid = self.status.last_uid = uid
        self.status.error = None
        cart = self.store.get(uid)
        if cart is None:
            self.leave_channels("UNASSIGNED CARTRIDGE")
            self.cart = None
            self.status.mode = "UNASSIGNED"
            self.note(f"Unassigned cartridge {uid}")
            return
        self.leave_channels("LOADING…")
        self.cart = cart
        self.status.mode, self.status.cartridge = "CARTRIDGE", cart.__dict__
        self.note(f"Cartridge {uid}: {cart.title}")
        try:
            self.items = self.plex._queue(cart)
            self.play_index(self.plex.first_index(cart, self.items))
        except Exception as e:
            log.exception("Could not start cartridge")
            self.status.error = str(e)
            self.player.card("PLAYBACK ERROR — see web page")

    def remove(self) -> None:
        self.note("Cartridge removed")
        self.status.uid = None
        self.to_channels()

    # --- event loop --------------------------------------------------------------------
    def handle(self, kind: str, arg) -> None:
        if kind == "tag_inserted":
            if self.status.uid and self.status.uid != arg:
                self.remove()
            self.insert(arg)
        elif kind == "tag_removed":
            if self.status.uid:
                self.remove()
        elif kind == "playback_ended":
            if self.item is None:
                return
            self.report("stopped")
            if arg == "error":
                self.status.error = f"mpv could not play {self.item.title}"
                self.note(self.status.error)
            self.play_index(self.index + 1, from_start=True)
        elif kind == "assigned":
            # The page assigned the cartridge that is in the slot: play it now.
            if self.status.uid == arg and self.status.mode == "UNASSIGNED":
                self.insert(arg)
        elif kind == "control":
            self.control(arg)

    def control(self, action: str) -> None:
        if self.status.mode == "STOPPED" and action == "pause" and self.status.uid:
            self.insert(self.status.uid)  # Play after Stop resumes from Plex's position
            return
        if self.status.mode != "CARTRIDGE" or self.item is None:
            return
        if action == "pause":
            paused = self.player.toggle_pause()
            self.report("paused" if paused else "playing")
        elif action == "next":
            self.report("stopped")
            if self.cart.kind == "movie":
                self.player.seek(60)
            else:
                self.play_index(self.index + 1, from_start=True)
        elif action == "prev":
            self.report("stopped")
            if self.cart.kind == "movie":
                self.player.seek(-60)
            else:
                self.play_index(max(0, self.index - 1), from_start=True)
        elif action == "stop":
            # Stop/Eject: save the position and go back to channels; the
            # cartridge is still in, so re-inserting isn't needed to resume.
            uid = self.status.uid
            self.to_channels()
            self.status.uid, self.status.mode = uid, "STOPPED"

    def run(self) -> None:
        from .web import serve

        threading.Thread(target=serve, args=(self,), name="web", daemon=True).start()
        if self.cfg.nfc.reader == "rc522":
            Rc522Poller(self.cfg.nfc, self.events).start()
        else:
            self.note("NFC reader: simulated (web page only)")
        clock_ok = wait_for_clock_sync(CLOCK_WAIT_S)
        self.note("Clock synced" if clock_ok else f"Clock not synced after {CLOCK_WAIT_S}s; starting anyway")
        self.to_channels()
        while True:
            if not clock_ok and clock_synced():
                # FS42 tuned on a wrong clock and would stay in a stale slot
                # (seen 2026-11-21): restart it now the time is right.
                clock_ok = True
                self.note("Clock synced late; restarting channels")
                if self.status.mode == "CHANNELS":
                    fs42.stop(self.cfg.fs42.service)
                    fs42.start(self.cfg.fs42.service)
            try:
                kind, arg = self.events.get(timeout=1.0)
                self.handle(kind, arg)
            except queue.Empty:
                pass
            except Exception as e:
                log.exception("Error handling event")
                self.status.error = str(e)
            if self.item and time.monotonic() - self.last_report >= self.cfg.plex.progress_interval_s:
                self.report("paused" if self.player.get("pause") else "playing")
