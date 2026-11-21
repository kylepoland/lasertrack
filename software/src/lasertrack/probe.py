"""`lasertrack probe`: sort the library by how likely the Pi 4 is to play it.

FieldStation42 plays files as they are; nothing transcodes them. So whether a
channel works depends on what the Pi 4 can decode in real time:

  video   H.264 8-bit up to 1080p (High profile, level <= 4.2): hardware decoder.
          HEVC 8/10-bit up to 4K: hardware decoder.
          MPEG-2: software only; 1080i is borderline on the Pi 4's CPU.
          VC-1, AV1, H.264 10-bit (Hi10P): software only; 1080p likely too slow.
  audio   TrueHD / DTS-HD MA are decoded on the CPU (fine, but adds load).
  network peaks above ~40 Mbps may stutter on Wi-Fi; Ethernet is fine.

Only file headers are read (ffprobe), so this is fast and read-only.
Output: a summary on screen and a CSV for `lasertrack bench --from`.
"""

from __future__ import annotations

import csv
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, fields
from pathlib import Path

EXTS = {".mkv", ".mp4", ".m4v", ".avi", ".mov", ".ts", ".mpg", ".mpeg", ".webm", ".wmv"}

OK, RISKY, BAD = "ok", "risky", "bad"


@dataclass
class Probe:
    path: str
    verdict: str = ""
    reasons: str = ""
    vcodec: str = ""
    profile: str = ""
    level: int = 0
    pix_fmt: str = ""
    width: int = 0
    height: int = 0
    fps: float = 0.0
    interlaced: bool = False
    acodec: str = ""
    aprofile: str = ""
    channels: int = 0
    mbps: float = 0.0
    duration_min: float = 0.0
    group: str = ""  # bench sample group, e.g. "h264 1080p", "vc1 1080p"


def ffprobe(path: Path) -> dict:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or "ffprobe failed")
    return json.loads(r.stdout)


def _fps(rate: str) -> float:
    try:
        n, d = rate.split("/")
        return round(int(n) / int(d), 3) if int(d) else 0.0
    except Exception:
        return 0.0


def classify(p: Probe) -> Probe:
    """Fill verdict, reasons and group from the stream facts."""
    reasons: list[str] = []
    verdict = OK
    tenbit = "10" in p.pix_fmt
    big = p.height > 720  # 1080-line content is where software decode fails

    def worse(v: str, why: str):
        nonlocal verdict
        order = {OK: 0, RISKY: 1, BAD: 2}
        if order[v] > order[verdict]:
            verdict = v
        reasons.append(why)

    c = p.vcodec
    if c == "h264":
        if tenbit:
            worse(BAD if big else RISKY, "H.264 10-bit has no hardware decoder")
        elif p.level > 42:
            worse(RISKY, f"H.264 level {p.level / 10:.1f} is above the decoder's 4.2")
        elif p.height > 1088:
            worse(BAD, "H.264 above 1080p")
    elif c == "hevc":
        pass  # hardware (stateless V4L2 via mpv's drm/v4l2request path)
    elif c == "mpeg2video":
        worse(RISKY if big else OK, "MPEG-2 decodes in software" + (" at 1080 lines" if big else ""))
    elif c == "vc1":
        worse(BAD if big else RISKY, "VC-1 decodes in software")
    elif c in ("av1", "vp9"):
        worse(BAD if big else RISKY, f"{c.upper()} decodes in software")
    elif c:
        worse(RISKY, f"uncommon video codec {c}")
    else:
        worse(BAD, "no video stream")

    if p.interlaced:
        reasons.append("interlaced")
    if p.acodec == "truehd" or (p.acodec == "dts" and "HD" in p.aprofile):
        reasons.append(f"CPU audio ({p.acodec} {p.aprofile})".strip())
    if p.mbps > 40:
        reasons.append(f"{p.mbps:.0f} Mbps average: use Ethernet")

    lines = "2160" if p.height > 1088 else "1080" if p.height > 720 else ("720" if p.height > 576 else "SD")
    p.verdict, p.reasons, p.group = verdict, "; ".join(reasons), f"{c or 'none'}{' 10bit' if tenbit else ''} {lines}"
    return p


def probe_file(path: Path) -> Probe:
    p = Probe(path=str(path))
    try:
        info = ffprobe(path)
    except Exception as e:
        p.verdict, p.reasons, p.group = BAD, f"unreadable: {e}", "unreadable"
        return p
    fmt = info.get("format", {})
    p.duration_min = round(float(fmt.get("duration", 0) or 0) / 60, 1)
    p.mbps = round(int(fmt.get("bit_rate", 0) or 0) / 1e6, 1)
    v = next((s for s in info["streams"] if s.get("codec_type") == "video" and not s.get("disposition", {}).get("attached_pic")), None)
    a = next((s for s in info["streams"] if s.get("codec_type") == "audio" and s.get("disposition", {}).get("default")), None)
    a = a or next((s for s in info["streams"] if s.get("codec_type") == "audio"), None)
    if v:
        p.vcodec = v.get("codec_name", "")
        p.profile = v.get("profile", "")
        p.level = int(v.get("level", 0) or 0)
        p.pix_fmt = v.get("pix_fmt", "")
        p.width, p.height = int(v.get("width", 0)), int(v.get("height", 0))
        p.fps = _fps(v.get("avg_frame_rate") or v.get("r_frame_rate") or "0/0")
        p.interlaced = v.get("field_order", "progressive") not in ("progressive", "unknown", "")
    if a:
        p.acodec = a.get("codec_name", "")
        p.aprofile = a.get("profile", "") or ""
        p.channels = int(a.get("channels", 0) or 0)
    return classify(p)


def find_media(roots: list[Path]) -> list[Path]:
    files = []
    for root in roots:
        for f in root.rglob("*"):
            if f.suffix.lower() in EXTS and f.is_file() and not f.name.startswith("."):
                files.append(f)
    return sorted(files)


def run(roots: list[Path], out_csv: Path, workers: int = 4, limit: int | None = None) -> list[Probe]:
    files = find_media(roots)
    if limit:
        files = files[:limit]
    print(f"Probing {len(files)} files under {', '.join(map(str, roots))} ...")
    results: list[Probe] = []
    with ThreadPoolExecutor(workers) as ex:
        for i, p in enumerate(ex.map(probe_file, files), 1):
            results.append(p)
            if i % 25 == 0:
                print(f"  {i}/{len(files)}")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[fl.name for fl in fields(Probe)])
        w.writeheader()
        for p in results:
            w.writerow(asdict(p))
    summarize(results)
    print(f"\nFull list: {out_csv}")
    return results


def summarize(results: list[Probe]) -> None:
    from collections import Counter

    total = len(results) or 1
    print("\nVerdict          files   share")
    for v in (OK, RISKY, BAD):
        n = sum(r.verdict == v for r in results)
        print(f"  {v:<14} {n:>5}   {100 * n / total:4.0f}%")
    print("\nBy group (codec, lines)        files  verdicts")
    groups: dict[str, Counter] = {}
    for r in results:
        groups.setdefault(r.group, Counter())[r.verdict] += 1
    for g, c in sorted(groups.items(), key=lambda kv: -sum(kv[1].values())):
        print(f"  {g:<28} {sum(c.values()):>5}  " + ", ".join(f"{k} {n}" for k, n in c.items()))
    audio = Counter(f"{r.acodec} {r.aprofile}".strip() for r in results if r.acodec)
    print("\nAudio: " + ", ".join(f"{k} {n}" for k, n in audio.most_common(6)))
    bad = [r for r in results if r.verdict == BAD][:15]
    if bad:
        print("\nFirst files judged bad:")
        for r in bad:
            print(f"  {Path(r.path).name}: {r.reasons}")
