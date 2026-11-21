"""`lasertrack bench`: play real files on the real output and count dropped frames.

`probe` predicts; this measures. For each sample file it plays 60 s from the
middle of the film in fullscreen mpv, once per decoder setting, and reads mpv's
counters:

  hwdec-current          which decoder mpv actually used ("no" = software)
  decoder-frame-drop-count  frames the decoder was too slow to produce
  frame-drop-count       frames dropped at the display
  avsync                 audio/video drift at the end

A run passes if under 1% of frames drop. FieldStation42 is stopped during the
bench and restarted afterwards.

Run it on the Pi with the TV connected (it needs the desktop session), e.g.
  lasertrack bench --from ~/lasertrack-probe.csv --per-group 2
"""

from __future__ import annotations

import csv
import os
import random
import time
from pathlib import Path

from python_mpv_jsonipc import MPV

from . import fs42
from .player import runtime_dir

HWDECS = ("conf", "auto-safe", "v4l2m2m-copy", "drm", "no")


def _ensure_display_env() -> None:
    """Allow running over SSH: point at the desktop session's Wayland display."""
    os.environ.setdefault("XDG_RUNTIME_DIR", str(runtime_dir()))
    if "WAYLAND_DISPLAY" not in os.environ and "DISPLAY" not in os.environ:
        os.environ["WAYLAND_DISPLAY"] = "wayland-0"


def parse_opts(text: str) -> dict:
    """"profile=fast,vo=dmabuf-wayland" -> {"profile": "fast", "vo": "dmabuf-wayland"}."""
    opts = {}
    for item in filter(None, (t.strip() for t in text.split(","))):
        k, _, v = item.partition("=")
        opts[k.replace("-", "_")] = v
    return opts


def bench_one(path: str, hwdec: str, seconds: float, duration_s: float, extra: dict | None = None) -> dict:
    sock = str(runtime_dir() / "lasertrack-bench.sock")
    opts = dict(extra or {})
    if hwdec != "conf":  # "conf" = use whatever mpv.conf says
        opts["hwdec"] = hwdec
    mpv = MPV(start_mpv=True, ipc_socket=sock, fs=True, input_default_bindings=False, osc=False, **opts)
    try:
        start = max(0.0, duration_s * 0.5) if duration_s else 0.0
        mpv.command("set_property", "start", f"{start:.0f}")
        mpv.command("loadfile", path, "replace")
        # Wait for playback to begin (network share + seek can take a moment).
        t0 = time.monotonic()
        while time.monotonic() - t0 < 20:
            if mpv.command("get_property", "time-pos") is not None:
                break
            time.sleep(0.25)
        time.sleep(3)  # let caches fill before counting
        get = lambda p: _safe(mpv, p)
        d0, f0 = get("decoder-frame-drop-count") or 0, get("frame-drop-count") or 0
        time.sleep(seconds)
        fps = get("container-fps") or 24
        frames = fps * seconds
        dec, vo = (get("decoder-frame-drop-count") or 0) - d0, (get("frame-drop-count") or 0) - f0
        return {
            "file": Path(path).name,
            "hwdec": hwdec,
            "opts": ",".join(f"{k}={v}" for k, v in (extra or {}).items()),
            "used": get("hwdec-current") or "no",
            "dec_drops": dec,
            "vo_drops": vo,
            "drop_pct": round(100 * (dec + vo) / frames, 2) if frames else None,
            "avsync": round(get("avsync") or 0, 3),
            "pass": frames and (dec + vo) / frames < 0.01,
        }
    finally:
        mpv.terminate()


def _safe(mpv, prop):
    try:
        return mpv.command("get_property", prop)
    except Exception:
        return None


def pick_samples(probe_csv: Path, per_group: int, seed: int = 1) -> list[dict]:
    rows = list(csv.DictReader(probe_csv.open()))
    by_group: dict[str, list[dict]] = {}
    for r in rows:
        if r["group"] != "unreadable":
            by_group.setdefault(r["group"], []).append(r)
    rnd = random.Random(seed)
    picked = []
    for g, rs in sorted(by_group.items()):
        rs = sorted(rs, key=lambda r: -float(r["mbps"] or 0))
        # The highest-bitrate file is the hardest case; the rest random.
        picked += rs[:1] + rnd.sample(rs[1:], min(per_group - 1, len(rs) - 1))
    return picked


def run(files: list[str], probe_csv: Path | None, per_group: int, seconds: float, hwdecs: list[str], service: str, out_csv: Path, extra: str = "", groups: list[str] | None = None) -> None:
    _ensure_display_env()
    samples: list[dict] = []
    if probe_csv:
        samples = pick_samples(probe_csv, per_group)
        if groups:
            samples = [s for s in samples if s["group"] in groups]
    samples += [{"path": f, "duration_min": "0", "group": "given"} for f in files]
    if not samples:
        raise SystemExit("Nothing to bench: pass files or --from a probe CSV.")
    was_running = fs42.is_active(service)
    if was_running:
        fs42.stop(service)
    results = []
    try:
        for s in samples:
            dur = float(s.get("duration_min") or 0) * 60
            for hw in hwdecs:
                print(f"[{s['group']}] {Path(s['path']).name}  hwdec={hw} ...", flush=True)
                try:
                    r = bench_one(s["path"], hw, seconds, dur, parse_opts(extra))
                except Exception as e:
                    r = {"file": Path(s["path"]).name, "hwdec": hw, "error": str(e), "pass": False}
                r["group"] = s["group"]
                results.append(r)
                print("   ", {k: v for k, v in r.items() if k not in ("file", "group")}, flush=True)
    finally:
        if was_running:
            fs42.start(service)
    keys = ["group", "file", "hwdec", "opts", "used", "dec_drops", "vo_drops", "drop_pct", "avsync", "pass", "error"]
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    print(f"\nResults: {out_csv}")
    print("\nBest decoder per group (lowest drops):")
    best: dict[str, dict] = {}
    for r in results:
        if r.get("drop_pct") is None:
            continue
        b = best.get(r["group"])
        if b is None or r["drop_pct"] < b["drop_pct"]:
            best[r["group"]] = r
    for g, r in sorted(best.items()):
        print(f"  {g:<24} hwdec={r['hwdec']:<13} used={r['used']:<14} drops {r['drop_pct']}%  {'PASS' if r['pass'] else 'FAIL'}")
