"""Tests for the parts that don't need a Pi, a NAS or Plex."""

import json
import sys
import types
from pathlib import Path

from lasertrack.cartridges import Cartridge, CartridgeStore
from lasertrack.config import load
from lasertrack.fs42 import DAYS, channel_conf, setup_channels
from lasertrack.nfc import PresenceTracker, crc_a, format_uid, uid_from_cascade
from lasertrack.probe import BAD, OK, RISKY, Probe, classify


def test_crc_a_known_vectors():
    # HLTA (50 00) -> 57 CD, the standard ISO 14443A example.
    assert crc_a(bytes([0x50, 0x00])) == bytes([0x57, 0xCD])
    # READ page 0 (30 00) -> 02 A8.
    assert crc_a(bytes([0x30, 0x00])) == bytes([0x02, 0xA8])


def test_seven_byte_uid_from_two_cascade_levels():
    cl1 = bytes([0x88, 0x04, 0xA1, 0xB2])
    cl2 = bytes([0xC3, 0xD4, 0xE5, 0xF6])
    uid = uid_from_cascade([cl1, cl2])
    assert format_uid(uid) == "04:A1:B2:C3:D4:E5:F6"
    assert format_uid(uid_from_cascade([bytes([1, 2, 3, 4])])) == "01:02:03:04"


def test_presence_tracker_debounces_removal():
    t = PresenceTracker(remove_after_misses=3)
    assert t.update("A") == ("tag_inserted", "A")
    assert t.update("A") is None
    assert t.update(None) is None  # one missed read while seated: still in
    assert t.update("A") is None
    assert [t.update(None) for _ in range(3)] == [None, None, ("tag_removed", None)]
    assert t.update("B") == ("tag_inserted", "B")
    assert t.update("C") == ("tag_inserted", "C")  # swapped without a gap


def test_classify():
    ok = classify(Probe(path="a", vcodec="h264", level=41, pix_fmt="yuv420p", height=1080))
    assert ok.verdict == OK and ok.group == "h264 1080"
    assert classify(Probe(path="b", vcodec="vc1", height=1080)).verdict == BAD
    assert classify(Probe(path="c", vcodec="mpeg2video", height=1080)).verdict == RISKY
    assert classify(Probe(path="d", vcodec="mpeg2video", height=480)).verdict == OK
    assert classify(Probe(path="e", vcodec="h264", level=41, pix_fmt="yuv420p10le", height=1080)).verdict == BAD
    hd = classify(Probe(path="f", vcodec="hevc", height=2160, acodec="truehd", mbps=55))
    assert hd.verdict == OK and "CPU audio" in hd.reasons and "Ethernet" in hd.reasons


def test_channel_conf_has_every_day_and_hour():
    c = channel_conf("LT Movies", 3, "catalog/lt_movies", ["movies", "classics"])["station_conf"]
    assert c["channel_number"] == 3 and c["commercial_free"] is True
    assert c["bump_dir"] == "bump" and c["break_strategy"] == "end"
    for d in DAYS:
        assert sorted(c[d], key=int) == [str(h) for h in range(24)]
    assert c["monday"]["0"] == {"tags": "movies"} and c["monday"]["1"] == {"tags": "classics"}


def test_setup_channels_links_into_media(tmp_path, monkeypatch):
    monkeypatch.setattr("lasertrack.fs42.make_bumps", lambda *a: None)
    media = tmp_path / "media"
    (media / "Movies").mkdir(parents=True)
    (media / "Movies" / "film.mkv").write_text("x")
    cfg_file = tmp_path / "config.toml"
    cfg_file.write_text(
        f'media_root = "{media}"\n[fs42]\ndir = "{tmp_path / "fs42"}"\n'
        '[[channels]]\nname = "LT Movies"\nnumber = 3\nfolders = ["Movies"]\n'
    )
    cfg = load(cfg_file)
    [conf] = setup_channels(cfg)
    link = tmp_path / "fs42" / "catalog" / "lt_movies" / "movies"
    assert link.is_symlink() and (link / "film.mkv").exists()
    assert json.loads(conf.read_text())["station_conf"]["content_dir"] == "catalog/lt_movies"
    # Re-running replaces the link and never touches the target.
    setup_channels(cfg)
    assert (media / "Movies" / "film.mkv").read_text() == "x"


def test_example_config_loads():
    cfg = load(Path(__file__).parent.parent / "config" / "config.example.toml")
    assert cfg.output == "composite" and [c.number for c in cfg.channels] == [3, 4]


def test_store_roundtrip(tmp_path):
    s = CartridgeStore(tmp_path)
    s.assign(Cartridge(uid="04:AA", kind="playlist", rating_key=12, title="Mix", shuffle=True))
    s.set_state("04:AA", {"index": 3})
    assert s.get("04:AA").title == "Mix" and s.get_state("04:AA") == {"index": 3}
    s.assign(Cartridge(uid="04:AA", kind="movie", rating_key=13, title="Film"))
    assert s.get_state("04:AA") == {}  # reassigning resets the playlist position
    s.unassign("04:AA")
    assert s.get("04:AA") is None
