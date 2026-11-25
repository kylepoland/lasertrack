"""The daemon's own mpv, used only in cartridge mode.

FieldStation42 has its own mpv; the two never run at once. The daemon stops
FS42's service before starting this one and quits this one before starting
FS42 again, so only one fullscreen window exists.

Both mpvs read ~/.config/mpv/mpv.conf (decoder and audio settings shared).
"""

from __future__ import annotations

import logging
import os
import queue
import time
from pathlib import Path

from python_mpv_jsonipc import MPV

log = logging.getLogger(__name__)

BLACK = "av://lavfi:color=c=black:s=720x480:r=30"


def runtime_dir() -> Path:
    return Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))


class Player:
    def __init__(self, events: queue.Queue):
        self.events = events
        self.mpv: MPV | None = None

    def _start(self) -> MPV:
        if self.mpv is None:
            sock = str(runtime_dir() / "lasertrack-mpv.sock")
            self.mpv = MPV(
                start_mpv=True,
                ipc_socket=sock,
                fs=True,
                idle=True,
                force_window=True,
                input_default_bindings=False,  # the daemon owns all input
                osc=False,
                osd_font_size=40,
                # CRTs overscan: keep text well inside the visible area
                # (margins are in OSD pixels scaled to a 720-line screen).
                osd_margin_x=72,
                osd_margin_y=54,
                osd_align_x="center",
                osd_align_y="center",
                keep_open=False,
            )
            self.mpv.bind_event("end-file", self._on_end_file)
        return self.mpv

    def _on_end_file(self, data) -> None:
        # Runs on the IPC thread: hand it to the main loop.
        reason = (data or {}).get("reason")
        if reason in ("eof", "error"):
            self.events.put(("playback_ended", reason))

    def play(self, url: str, start_s: float = 0.0, title: str = "") -> None:
        mpv = self._start()
        # Set 'start' as a property rather than a loadfile option: the
        # loadfile argument order changed in mpv 0.38.
        mpv.command("set_property", "start", f"{start_s:.1f}" if start_s else "none")
        mpv.command("loadfile", url, "replace")
        if title:
            self.osd(f"▶ PLAY  {title}", 4)

    def card(self, text: str = "") -> None:
        """Black screen with an optional line of text, shown before returning.

        Waits until mpv's window is actually on screen, so the caller can
        then stop FieldStation42 without the desktop showing in between.
        """
        mpv = self._start()
        mpv.command("set_property", "start", "none")
        mpv.command("loadfile", BLACK, "replace")
        self.wait_visible()
        if text:
            self.osd(text, 86400)

    def wait_visible(self, timeout_s: float = 5.0) -> bool:
        end = time.monotonic() + timeout_s
        while time.monotonic() < end:
            if self.get("vo-configured"):
                time.sleep(0.15)  # one more frame or two for the compositor
                return True
            time.sleep(0.05)
        log.warning("mpv window not confirmed visible after %.1fs", timeout_s)
        return False

    @property
    def running(self) -> bool:
        return self.mpv is not None

    def osd(self, text: str, seconds: float) -> None:
        if self.mpv:
            self.mpv.command("show-text", text, int(seconds * 1000))

    def get(self, prop: str):
        if not self.mpv:
            return None
        try:
            return self.mpv.command("get_property", prop)
        except Exception:
            return None

    def toggle_pause(self) -> bool:
        paused = not bool(self.get("pause"))
        self.mpv.command("set_property", "pause", paused)
        self.osd("❚❚ PAUSE" if paused else "▶ PLAY", 2)
        return paused

    def seek(self, seconds: float) -> None:
        if self.mpv:
            self.mpv.command("seek", seconds, "relative")

    def quit(self) -> None:
        if self.mpv:
            try:
                self.mpv.terminate()
            except Exception as e:
                log.warning("mpv terminate: %s", e)
            self.mpv = None
