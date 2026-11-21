"""FieldStation42: start/stop its player, and build the test channels.

FS42 runs unmodified (decided 2026-11-18). Its player is a systemd user
service (`fs42.service`, installed by setup_pi.sh). Stopping it quits its mpv
and frees the screen; starting it again tunes to whatever is scheduled now.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from .config import Config

log = logging.getLogger(__name__)

DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")


def _systemctl(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["systemctl", "--user", *args], capture_output=True, text=True)


def start(service: str) -> None:
    r = _systemctl("start", service)
    if r.returncode:
        log.error("Could not start %s: %s", service, r.stderr.strip())


def stop(service: str) -> None:
    r = _systemctl("stop", service)  # waits until the process has exited
    if r.returncode:
        log.error("Could not stop %s: %s", service, r.stderr.strip())


def is_active(service: str) -> bool:
    return _systemctl("is-active", "--quiet", service).returncode == 0


BUMP_TAG = "bump"
BUMP_SECONDS = (10, 30, 60)


def make_bumps(folder: Path, name: str, number: int) -> None:
    """Placeholder station-ID clips: colour bars with the channel's name.

    Stored on the Pi's SD card, not the NAS. Replace them with real bumps or
    commercials later; FS42 picks up whatever video is in the folder.
    """
    folder.mkdir(parents=True, exist_ok=True)
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    label = f"{name.upper()}   CH {number:02d}".replace(":", "\\:")
    for secs in BUMP_SECONDS:
        out = folder / f"lt_ident_{secs:02d}s.mp4"
        if out.exists():
            continue
        vf = (
            f"drawbox=y=ih*0.38:w=iw:h=ih*0.24:color=black@0.85:t=fill,"
            f"drawtext=fontfile={font}:text='{label}':fontcolor=white:fontsize=40:"
            f"x=(w-text_w)/2:y=(h-text_h)/2"
        )
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y",
             "-f", "lavfi", "-i", "smptebars=size=720x480:rate=30000/1001",
             "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
             "-t", str(secs), "-vf", vf, "-c:v", "libx264", "-preset", "veryfast",
             "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(out)],
            check=True,
        )


def channel_conf(name: str, number: int, content_dir: str, tags: list[str]) -> dict:
    """A 'standard' FS42 channel that plays its tags round the clock.

    Tags rotate hour by hour. Commercial-free: FS42 fills the gap between a
    show's end and the next slot with clips from the `bump` folder (it
    requires one even for commercial-free channels), and with
    break_strategy "end" all of that filler comes after the show, never in
    the middle of it.
    """
    hours = {str(h): {"tags": tags[h % len(tags)]} for h in range(24)}
    conf = {
        "network_name": name,
        "channel_number": number,
        "content_dir": content_dir,
        "commercial_free": True,
        "break_strategy": "end",
        "bump_dir": BUMP_TAG,
        "commercial_dir": "commercial",
    }
    for day in DAYS:
        conf[day] = dict(hours)
    return {"station_conf": conf}


def setup_channels(cfg: Config, dry_run: bool = False) -> list[Path]:
    """Make catalog folders of symlinks into the read-only share, and confs.

    catalog/<slug>/<tag> -> /mnt/media/<folder>. FS42 reads through the link;
    the mount is read-only, so nothing FS42 does can change the media.
    """
    fs42_dir = cfg.fs42.path
    media = Path(cfg.media_root)
    written = []
    for ch in cfg.channels:
        # lt_ prefix marks folders/confs LaserTrack made, so they're easy to find.
        slug = "".join(c if c.isalnum() else "_" for c in ch.name.lower())
        slug = slug if slug.startswith("lt_") else "lt_" + slug
        chan_dir = fs42_dir / "catalog" / slug
        tags = []
        for folder in ch.folders:
            target = media / folder
            tag = "".join(c if c.isalnum() else "_" for c in Path(folder).name.lower())
            link = chan_dir / tag
            tags.append(tag)
            if dry_run:
                continue
            if not target.is_dir():
                raise FileNotFoundError(f"{target} not found (is the share mounted?)")
            chan_dir.mkdir(parents=True, exist_ok=True)
            if link.is_symlink():
                link.unlink()  # unlink removes the link only, never the target
            link.symlink_to(target, target_is_directory=True)
        if not dry_run:
            make_bumps(chan_dir / BUMP_TAG, ch.name, ch.number)
        conf_path = fs42_dir / "confs" / f"{slug}.json"
        conf = channel_conf(ch.name, ch.number, f"catalog/{slug}", tags)
        if not dry_run:
            conf_path.parent.mkdir(parents=True, exist_ok=True)
            conf_path.write_text(json.dumps(conf, indent=2))
        written.append(conf_path)
    return written
