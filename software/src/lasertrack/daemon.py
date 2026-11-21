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
        if self.item:
            self.report("stopped")
        self.player.quit()
        self.cart, self.items, self.item = None, [], None
        self.status.mode, self.status.cartridge, self.status.now_playing = "CHANNELS", None, None
        fs42.start(self.cfg.fs42.service)
        self.note("Channels")

    def leave_channels(self) -> None:
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
        self.leave_channels()
        if cart is None:
            self.cart = None
            self.status.mode = "UNASSIGNED"
            self.player.card("UNASSIGNED CARTRIDGE")
            self.note(f"Unassigned cartridge {uid}")
            return
        self.cart = cart
        self.status.mode, self.status.cartridge = "CARTRIDGE", cart.__dict__
        self.player.card("LOADING…")
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
        self.to_channels()
        while True:
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
