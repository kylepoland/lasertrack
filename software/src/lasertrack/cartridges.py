"""The tag-UID-to-media table, plus per-cartridge playback state.

A cartridge stores only its tag UID (decided 2026-11-18), so reassigning one is
an edit here, not a rewrite of the tag. Both files are small JSON written
atomically (temp file + rename) so a power cut can't leave half a file.
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import DATA_DIR

KINDS = ("movie", "show", "playlist", "collection")


@dataclass
class Cartridge:
    uid: str
    kind: str  # one of KINDS
    rating_key: int  # Plex's id for the movie/show/playlist/collection
    title: str
    shuffle: bool = False  # playlists and collections only


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True))
    os.replace(tmp, path)


def _read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text())


class CartridgeStore:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.map_file = data_dir / "cartridges.json"
        self.state_file = data_dir / "state.json"
        self._lock = threading.Lock()

    def all(self) -> list[Cartridge]:
        with self._lock:
            return [Cartridge(**c) for c in _read_json(self.map_file, {}).values()]

    def get(self, uid: str) -> Cartridge | None:
        with self._lock:
            c = _read_json(self.map_file, {}).get(uid)
        return Cartridge(**c) if c else None

    def assign(self, cart: Cartridge) -> None:
        if cart.kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}")
        with self._lock:
            data = _read_json(self.map_file, {})
            data[cart.uid] = asdict(cart)
            _write_json(self.map_file, data)
            # A reassigned cartridge starts its playlist from the top.
            state = _read_json(self.state_file, {})
            state.pop(cart.uid, None)
            _write_json(self.state_file, state)

    def unassign(self, uid: str) -> None:
        with self._lock:
            data = _read_json(self.map_file, {})
            data.pop(uid, None)
            _write_json(self.map_file, data)

    # Playlist/collection position. Plex playlists don't remember which item
    # you were on, so the box does (product.md, Media).
    def get_state(self, uid: str) -> dict:
        with self._lock:
            return _read_json(self.state_file, {}).get(uid, {})

    def set_state(self, uid: str, state: dict) -> None:
        with self._lock:
            data = _read_json(self.state_file, {})
            data[uid] = state
            _write_json(self.state_file, data)
