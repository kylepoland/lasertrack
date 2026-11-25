"""Settings, read from ~/.config/lasertrack/config.toml.

Every key has a default here, so the file only needs what differs. Secrets
(the Plex token, the SMB password) are never in this file: the token lives in
its own 0600 file next to it, the SMB password in /etc/lasertrack.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("LASERTRACK_CONFIG_DIR", "~/.config/lasertrack")).expanduser()
DATA_DIR = Path(os.environ.get("LASERTRACK_DATA_DIR", "~/.local/share/lasertrack")).expanduser()
CONFIG_FILE = CONFIG_DIR / "config.toml"
PLEX_TOKEN_FILE = CONFIG_DIR / "plex_token"


@dataclass
class PlexConfig:
    server_name: str = "Blockbuster"
    # Optional direct URL (e.g. "http://192.168.1.x:32400"). Empty = find the
    # server through the plex.tv account, which also works if its IP changes.
    url: str = ""
    # Composite (CRT): ask Plex to transcode down. The NAS has hardware
    # transcoding, and the Pi then never decodes a Blu-ray stream itself.
    composite_resolution: str = "720x480"
    composite_bitrate_kbps: int = 2000
    # HDMI: "direct" plays the original file; "transcode" uses the values below
    # (useful on Wi-Fi, where 40 Mbps peaks may stutter).
    hdmi_mode: str = "direct"
    hdmi_resolution: str = "1920x1080"
    hdmi_bitrate_kbps: int = 12000
    progress_interval_s: float = 10.0


@dataclass
class NfcConfig:
    reader: str = "rc522"  # "rc522" or "sim" (web page only, no hardware)
    spi_bus: int = 0
    spi_device: int = 0  # CE0; the LCD will take CE1 later
    reset_gpio: int = 25
    poll_interval_s: float = 0.15
    # Seconds without a good read before the cartridge counts as removed. A
    # seated tag misses the odd read; 1 s rides through that and still feels
    # immediate when the cartridge is pulled.
    remove_after_s: float = 1.0
    # Receiver gain 0-7 (7 = 48 dB, the maximum). Raise if reads through the
    # cartridge shell are flaky.
    rx_gain: int = 7


@dataclass
class WebConfig:
    host: str = "0.0.0.0"
    port: int = 8080


@dataclass
class Fs42Config:
    dir: str = "~/FieldStation42"
    service: str = "fs42.service"

    @property
    def path(self) -> Path:
        return Path(self.dir).expanduser()


@dataclass
class ChannelConfig:
    """One FieldStation42 test channel built by `lasertrack fs42-setup`."""

    name: str
    number: int
    # Folders under media_root, each becomes one tag (a subfolder of the
    # channel's catalog folder, symlinked to the share).
    folders: list[str]


@dataclass
class Config:
    output: str = "composite"  # "composite" or "hdmi"; must match the boot config
    media_root: str = "/mnt/media"  # read-only CIFS mount of //NAS/storage/media
    plex: PlexConfig = field(default_factory=PlexConfig)
    nfc: NfcConfig = field(default_factory=NfcConfig)
    web: WebConfig = field(default_factory=WebConfig)
    fs42: Fs42Config = field(default_factory=Fs42Config)
    channels: list[ChannelConfig] = field(default_factory=list)


def _fill(cls, data: dict):
    known = {f for f in cls.__dataclass_fields__}
    unknown = set(data) - known
    if unknown:
        raise ValueError(f"Unknown keys in [{cls.__name__}]: {sorted(unknown)}")
    return cls(**data)


def load(path: Path = CONFIG_FILE) -> Config:
    raw: dict = {}
    if path.exists():
        with path.open("rb") as f:
            raw = tomllib.load(f)
    cfg = Config(
        output=raw.get("output", "composite"),
        media_root=raw.get("media_root", "/mnt/media"),
        plex=_fill(PlexConfig, raw.get("plex", {})),
        nfc=_fill(NfcConfig, raw.get("nfc", {})),
        web=_fill(WebConfig, raw.get("web", {})),
        fs42=_fill(Fs42Config, raw.get("fs42", {})),
        channels=[_fill(ChannelConfig, c) for c in raw.get("channels", [])],
    )
    if cfg.output not in ("composite", "hdmi"):
        raise ValueError(f"output must be 'composite' or 'hdmi', not {cfg.output!r}")
    if cfg.nfc.reader not in ("rc522", "sim"):
        raise ValueError(f"nfc.reader must be 'rc522' or 'sim', not {cfg.nfc.reader!r}")
    return cfg
