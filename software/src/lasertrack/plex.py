"""Plex: sign-in, finding what a cartridge should play, stream URLs, progress.

Cartridges play through Plex (decided 2026-11-18) so they share saved
positions and Continue Watching with Kyle's phone. Channels never touch Plex.
"""

from __future__ import annotations

import logging
import os
import random
import socket
import uuid
from dataclasses import dataclass

import plexapi
from plexapi.myplex import MyPlexAccount, MyPlexPinLogin
from plexapi.server import PlexServer

from .cartridges import Cartridge, CartridgeStore
from .config import CONFIG_DIR, PLEX_TOKEN_FILE, PlexConfig

log = logging.getLogger(__name__)


def _client_id() -> str:
    """A stable client identifier, so Plex shows one 'LaserTrack' device."""
    path = CONFIG_DIR / "client_id"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(uuid.uuid4()))
    return path.read_text().strip()


def _set_identity() -> None:
    hdr = plexapi.BASE_HEADERS
    hdr["X-Plex-Product"] = "LaserTrack"
    hdr["X-Plex-Version"] = "0.1.0"
    hdr["X-Plex-Device"] = "Raspberry Pi"
    hdr["X-Plex-Device-Name"] = socket.gethostname()
    hdr["X-Plex-Platform"] = "Linux"
    hdr["X-Plex-Client-Identifier"] = _client_id()


def login_with_pin() -> None:
    """Link this box to the Plex account with a code entered at plex.tv/link.

    No password is typed on the Pi; the resulting token goes in a 0600 file.
    """
    _set_identity()
    pin = MyPlexPinLogin()
    print(f"\n  Go to https://plex.tv/link and enter:  {pin.pin}\n")
    print("Waiting up to 5 minutes...")
    pin.run(timeout=300)
    if not pin.waitForLogin():
        raise SystemExit("Timed out or refused; run `lasertrack plex-login` again.")
    PLEX_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(PLEX_TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(pin.token)
    print(f"Linked. Token saved to {PLEX_TOKEN_FILE}")


def connect(cfg: PlexConfig) -> PlexServer:
    _set_identity()
    if not PLEX_TOKEN_FILE.exists():
        raise RuntimeError("No Plex token; run `lasertrack plex-login` first.")
    token = PLEX_TOKEN_FILE.read_text().strip()
    if cfg.url:
        return PlexServer(cfg.url, token)
    account = MyPlexAccount(token=token)
    server = account.resource(cfg.server_name).connect()  # tries local addresses first
    log.info("Connected to Plex server %s at %s", server.friendlyName, server._baseurl)
    return server


@dataclass
class PlayItem:
    """One thing to put on screen: a movie or an episode."""

    video: object  # plexapi Movie or Episode
    url: str
    start_s: float  # where to start, from Plex's saved position
    transcoded: bool
    title: str


class PlexPlayback:
    def __init__(self, cfg: PlexConfig, output: str, store: CartridgeStore):
        self.cfg = cfg
        self.output = output
        self.store = store
        self.server: PlexServer | None = None

    def ensure(self) -> PlexServer:
        if self.server is None:
            self.server = connect(self.cfg)
        return self.server

    # --- choosing what to play -------------------------------------------------
    def _queue(self, cart: Cartridge) -> list:
        """The ordered list of playable videos this cartridge stands for."""
        server = self.ensure()
        obj = server.fetchItem(cart.rating_key)
        if cart.kind == "movie":
            return [obj]
        if cart.kind == "show":
            return obj.episodes()
        items = [i for i in obj.items() if i.type in ("movie", "episode")]
        if cart.shuffle:
            state = self.store.get_state(cart.uid)
            seed = state.get("shuffle_seed")
            if seed is None:
                seed = random.randrange(1 << 30)
                self.store.set_state(cart.uid, {**state, "shuffle_seed": seed})
            random.Random(seed).shuffle(items)
        return items

    def first_index(self, cart: Cartridge, items: list) -> int:
        if cart.kind == "movie":
            return 0
        if cart.kind == "show":
            # Plex's On Deck episode: the one in progress, or the next unwatched.
            show = self.ensure().fetchItem(cart.rating_key)
            deck = show.onDeck()
            if deck is not None:
                for i, ep in enumerate(items):
                    if ep.ratingKey == deck.ratingKey:
                        return i
            for i, ep in enumerate(items):
                if not ep.isPlayed:
                    return i
            return 0
        # Playlist/collection: the box remembers the current item.
        idx = self.store.get_state(cart.uid).get("index", 0)
        return idx if 0 <= idx < len(items) else 0

    def remember_index(self, cart: Cartridge, idx: int) -> None:
        if cart.kind in ("playlist", "collection"):
            state = self.store.get_state(cart.uid)
            self.store.set_state(cart.uid, {**state, "index": idx})

    def make_item(self, video, from_start: bool = False) -> PlayItem:
        video.reload()  # fresh viewOffset in case the phone moved it
        start_s = 0.0 if from_start else (video.viewOffset or 0) / 1000
        # Don't resume into the closing credits: past 95% start over.
        if video.duration and start_s * 1000 > 0.95 * video.duration:
            start_s = 0.0
        if self.output == "composite":
            res, kbps, transcode = self.cfg.composite_resolution, self.cfg.composite_bitrate_kbps, True
        else:
            res, kbps = self.cfg.hdmi_resolution, self.cfg.hdmi_bitrate_kbps
            transcode = self.cfg.hdmi_mode == "transcode"
        if transcode:
            # HLS from Plex's universal transcoder, starting at the offset.
            # The NAS does the work (hardware transcoding), the Pi only plays
            # a small 480p stream.
            url = video.getStreamURL(
                videoResolution=res,
                maxVideoBitrate=kbps,
                offset=int(start_s),
                protocol="hls",
            )
        else:
            part = video.media[0].parts[0]
            url = self.ensure().url(part.key, includeToken=True)
        title = video.title
        if video.type == "episode":
            title = f"{video.grandparentTitle} {video.seasonEpisode.upper()} {video.title}"
        return PlayItem(video, url, start_s, transcode, title)

    # --- reporting ---------------------------------------------------------------
    @staticmethod
    def report(video, position_s: float, state: str) -> None:
        """Tell Plex where we are ('playing', 'paused', 'stopped')."""
        try:
            video.updateTimeline(int(position_s * 1000), state=state, duration=video.duration)
            if state == "stopped" and video.duration and position_s * 1000 >= 0.9 * video.duration:
                video.markPlayed()  # Plex's own rule is 90%; don't rely on the timeline alone
        except Exception as e:
            log.warning("Plex progress report failed: %s", e)

    # --- web assignment page -------------------------------------------------------
    def search(self, query: str) -> list[dict]:
        server = self.ensure()
        results = []
        seen = set()
        for item in server.search(query, limit=30):
            if item.type not in ("movie", "show", "playlist", "collection"):
                continue
            if item.ratingKey in seen:
                continue
            seen.add(item.ratingKey)
            year = getattr(item, "year", None)
            results.append(
                {
                    "rating_key": int(item.ratingKey),
                    "kind": item.type,
                    "title": item.title + (f" ({year})" if year else ""),
                }
            )
        q = query.lower()
        for pl in server.playlists(playlistType="video"):
            if q in pl.title.lower() and pl.ratingKey not in seen:
                results.append({"rating_key": int(pl.ratingKey), "kind": "playlist", "title": pl.title})
        return results
