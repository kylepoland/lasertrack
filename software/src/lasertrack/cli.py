"""Command line: `lasertrack <command>`. Run `lasertrack -h` for the list."""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

from . import config


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="lasertrack")
    ap.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("run", help="run the daemon (normally started by systemd)")
    sub.add_parser("plex-login", help="link this box to Plex with a plex.tv/link code")
    sub.add_parser("plex-check", help="connect to Plex and list libraries")

    p = sub.add_parser("probe", help="classify media files by how well the Pi can play them")
    p.add_argument("roots", nargs="*", help="folders to scan (default: media_root)")
    p.add_argument("-o", "--out", default="~/lasertrack-probe.csv")
    p.add_argument("-j", "--workers", type=int, default=4)
    p.add_argument("--limit", type=int)

    b = sub.add_parser("bench", help="play sample files and count dropped frames")
    b.add_argument("files", nargs="*")
    b.add_argument("--from", dest="probe_csv", help="pick samples from a probe CSV")
    b.add_argument("--per-group", type=int, default=2)
    b.add_argument("--seconds", type=float, default=60)
    b.add_argument("--hwdec", default="auto-safe,v4l2m2m-copy,drm,no", help="comma list of mpv hwdec values to try")
    b.add_argument("--mpv", default="", help='extra mpv options for every run, e.g. "profile=fast,vo=dmabuf-wayland"')
    b.add_argument("--group", action="append", help="only bench this probe group (repeatable)")
    b.add_argument("-o", "--out", default="~/lasertrack-bench.csv")

    f = sub.add_parser("fs42-setup", help="symlink test channels into FieldStation42 and build schedules")
    f.add_argument("--no-build", action="store_true", help="only write links and confs")

    n = sub.add_parser("nfc-test", help="print tag UIDs as they are read (stop the daemon first)")
    n.add_argument("--seconds", type=float, default=0, help="0 = until Ctrl-C")

    args = ap.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    cfg = config.load()

    if args.cmd == "run":
        from .daemon import Daemon

        Daemon(cfg).run()

    elif args.cmd == "plex-login":
        from .plex import login_with_pin

        login_with_pin()

    elif args.cmd == "plex-check":
        from .plex import connect

        server = connect(cfg.plex)
        print(f"Server: {server.friendlyName} ({server.version}) at {server._baseurl}")
        for s in server.library.sections():
            print(f"  {s.type:<8} {s.title}  ({s.totalSize} items)")

    elif args.cmd == "probe":
        from .probe import run

        roots = [Path(r) for r in args.roots] or [Path(cfg.media_root)]
        run(roots, Path(args.out).expanduser(), args.workers, args.limit)

    elif args.cmd == "bench":
        from .bench import run

        run(
            args.files,
            Path(args.probe_csv).expanduser() if args.probe_csv else None,
            args.per_group,
            args.seconds,
            args.hwdec.split(","),
            cfg.fs42.service,
            Path(args.out).expanduser(),
            args.mpv,
            args.group,
        )

    elif args.cmd == "fs42-setup":
        from .fs42 import setup_channels

        if not cfg.channels:
            sys.exit("No [[channels]] in config.toml.")
        for p in setup_channels(cfg):
            print(f"wrote {p}")
        if not args.no_build:
            py = str(cfg.fs42.path / "env" / "bin" / "python3")
            # Catalog: measures each file's duration (headers only, read-only).
            subprocess.run([py, "station_42.py", "--rebuild_catalog"], cwd=cfg.fs42.path, check=True)
            subprocess.run([py, "station_42.py", "--add_week"], cwd=cfg.fs42.path, check=True)

    elif args.cmd == "nfc-test":
        import time

        from .nfc import PresenceTracker, Rc522, format_uid

        r = Rc522(cfg.nfc.spi_bus, cfg.nfc.spi_device, cfg.nfc.reset_gpio, cfg.nfc.rx_gain)
        tracker = PresenceTracker(cfg.nfc.remove_after_misses)
        print("Hold a tag to the reader (Ctrl-C to stop).")
        end = time.monotonic() + args.seconds if args.seconds else None
        reads = misses = 0
        try:
            while end is None or time.monotonic() < end:
                raw = r.read_uid()
                reads += raw is not None
                misses += raw is None
                ev = tracker.update(format_uid(raw) if raw else None)
                if ev:
                    print(ev[0], ev[1] or "", f"(reads {reads}, misses {misses})")
                time.sleep(cfg.nfc.poll_interval_s)
        except KeyboardInterrupt:
            pass
        finally:
            r.close()


if __name__ == "__main__":
    main()
