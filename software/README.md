# LaserTrack software (Raspberry Pi)

v1: FieldStation42 plays scheduled channels from the NAS; inserting an NFC
cartridge stops it and plays that cartridge's media from Plex; pulling the
cartridge reports the position to Plex and puts the channels back.

```
                ┌────────────── Raspberry Pi 4 ──────────────┐
 RC522 ──SPI──▶ │ lasertrack daemon ── web page :8080 (phone)│
                │   │  stops/starts          │ plays          │
                │   ▼                        ▼                │
                │ fs42.service (mpv)     own mpv ◀── Plex HLS │ ◀── Plex "Blockbuster"
                │   ▲ reads files                             │     (transcodes on NAS)
                └───┼─────────────────────────────────────────┘
                    └── /mnt/media  READ-ONLY mount of //192.168.1.157/storage/media
```

| Path | What |
|---|---|
| `src/lasertrack/daemon.py` | Mode switching (channels / cartridge), the event loop |
| `src/lasertrack/nfc.py` | RC522 driver (full 7-byte NTAG UIDs) and insert/remove detection |
| `src/lasertrack/plex.py` | Plex sign-in by code, what to play, stream URLs, progress reports |
| `src/lasertrack/web.py` | Phone page: assign cartridges, simulate tags, play/pause/next/stop |
| `src/lasertrack/probe.py`, `bench.py` | Can the Pi play the library? Predict, then measure |
| `src/lasertrack/fs42.py` | Start/stop FieldStation42, build test channels |
| `config/` | `config.example.toml`, `mpv.conf` (shared by both mpvs) |
| `install/setup_pi.sh` | Everything on the Pi, in re-runnable steps |
| `deploy.sh` | Copy this folder from the Mac to the Pi |

Wiring for the reader: [`electronics/rc522.md`](../electronics/rc522.md).

---

## 1. Flash the microSD (on the Mac)

1. Install Raspberry Pi Imager: `brew install --cask raspberry-pi-imager`
   (or download it from raspberrypi.com/software).
2. Put the 32 GB card in the Mac and open Imager.
3. **Device:** Raspberry Pi 4. **OS:** *Raspberry Pi OS (64-bit)*, the
   desktop version (FieldStation42's player needs a desktop session for its
   window). It is based on Debian 13 "Trixie", which FS42's docs recommend.
   **Storage:** the SD card. Double-check it's the card, not a backup disk.
4. Imager then offers OS customisation (older versions: **Next → Edit
   settings**; newer ones walk through it step by step). Set:
   - Hostname: `lasertrack`
   - Time zone: yours (FS42 schedules follow the clock); keyboard `us`.
   - Username `admin` and a password you choose (sudo asks for it).
   - Wi-Fi: your network name and password, country `US`. Fill it in even
     if you'll use Ethernet, so you can try both.
   - SSH: **on**, **public-key authentication only**, with your Mac's key.
     Imager usually fills it in from `~/.ssh/id_ed25519.pub`; if not, run
     `pbcopy < ~/.ssh/id_ed25519.pub` and paste it.
   - Raspberry Pi Connect: off (not needed).
5. Apply the settings and confirm erasing the card. Writing and verifying
   takes about 5–10 minutes.
6. **Turn on composite before first boot** (CRT only, no HDMI). Out of the
   box a Pi 4 sends no picture to the 3.5 mm jack, so without this the CRT
   stays blank until step 3. Setup works over SSH either way, but seeing the
   boot on the CRT makes problems easier to spot.
   Take the card out and put it back in the Mac; a drive called `bootfs`
   appears. Then edit two files on it (or ask Claude to):
   - `config.txt`: change the line `dtoverlay=vc4-kms-v3d` to
     `dtoverlay=vc4-kms-v3d,composite`, and add `enable_tvout=1` as the last
     line.
   - `cmdline.txt`: it is **one line**; add a space and
     `video=Composite-1:720x480@60ie vc4.tv_norm=NTSC` to the end of that
     line. Don't add a new line.
   Eject `bootfs` in Finder.
7. Put the card in the Pi, plug the composite cable into the 3.5 mm jack
   (it carries video and audio), plug in the network cable if you're using
   one, then power. First boot sets itself up and reboots once; give it 2–3
   minutes.

## 2. Connect from the Mac

Add this to `~/.ssh/config` on the Mac, so `ssh lasertrack` works (and so I
can run commands on the Pi for you):

```
Host lasertrack
  HostName lasertrack.local
  User admin
  IdentityFile ~/.ssh/id_ed25519
```

Check it:

```bash
ssh lasertrack 'uname -a && cat /etc/os-release | head -3'
```

If `lasertrack.local` doesn't resolve, find the Pi's IP in your router's
client list and use that as `HostName`.

## 3. Install

From the Mac, copy the software over:

```bash
cd ~/code/lasertrack/software && ./deploy.sh
```

On the Pi (`ssh lasertrack`), **you** type the NAS login, so the password is
never in this repo or in a chat:

```bash
cd ~/lasertrack && bash install/setup_pi.sh nas-credentials
```

`sudo` on the Pi asks for your password, so **you** run the steps that use it
(`base`, `nas-credentials`, `nas-mount`, `output`) in an `ssh -t lasertrack`
session. Claude runs the rest (`fs42`, `app`, `probe`, `bench`,
`fs42-setup`) over SSH.

Then the rest:

```bash
cd ~/lasertrack && bash install/setup_pi.sh all
```

```bash
cd ~/lasertrack && bash install/setup_pi.sh output composite && sudo reboot
```

```bash
ssh -t lasertrack '~/lasertrack/.venv/bin/lasertrack plex-login'
```

`plex-login` prints a 4-letter code: enter it at https://plex.tv/link. No
password is typed on the Pi.

Until the RC522 is wired, set `reader = "sim"` under `[nfc]` in
`~/.config/lasertrack/config.toml` on the Pi.

## 4. Test plan

**A. Can the Pi play the raw MKVs? (the big unknown)**

```bash
ssh lasertrack '~/lasertrack/.venv/bin/lasertrack probe'
```

Reads only file headers, prints how many files fall into *ok / risky / bad*
and why, and writes `~/lasertrack-probe.csv`. Then measure on the real TV:

```bash
ssh lasertrack '~/lasertrack/.venv/bin/lasertrack bench --from ~/lasertrack-probe.csv --per-group 2'
```

It plays 60 s of each sample once per decoder setting and reports dropped
frames, and which decoder mpv really used. Try it once on Wi-Fi and once on
Ethernet. The results decide what happens to the files that fail (see
`docs/product.md`, Media).

**B. FieldStation42 channels**

```bash
ssh lasertrack '~/lasertrack/.venv/bin/lasertrack fs42-setup'
```

This symlinks `Movies` and `TV` from the read-only share into FS42's catalog as
channels 3 and 4, measures every file's duration (the first time takes a
while), and builds a week of schedules. Then reboot, or
`systemctl --user restart lasertrack`; channels start on their own.

**C. Cartridges through Plex**

Open http://lasertrack.local:8080 on your phone. Simulate a tag (or insert a
real one), search Plex, tap **Assign**: it starts playing. **Remove**
returns to channels; check your phone's Plex app shows the position under
Continue Watching, then insert again to resume.

## Everyday commands (on the Pi)

```bash
systemctl --user status lasertrack fs42      # what's running
journalctl --user -u lasertrack -f           # daemon log
journalctl --user -u fs42 -f                 # FieldStation42 log
systemctl --user restart lasertrack          # after a config change
```

The Pi boots into a kiosk session: black screen, no desktop or taskbar,
just the daemon and FieldStation42 (`~/.config/labwc/autostart`). To get the
normal Pi desktop back, delete that file and reboot.

## Safety of the media files

- **The Pi's connection** to the share is read-only: `ro` in the Pi's own
  `/etc/fstab`, set by `setup_pi.sh nas-mount`. Linux on the Pi rejects
  every write, delete and rename through it, even as root, and the script
  refuses to finish unless a test write fails. This changes nothing on the
  NAS: other computers (the Windows PC) keep whatever access their own login
  gives them.
- Only the `media` folder is mounted, not the whole `storage` share.
- FS42's catalog holds **symlinks** to the share. Deleting a symlink deletes
  the link, not the film.
- Strongest option, on the NAS side: give the Pi its own OMV user with
  read-only permission on the share. Then the NAS itself refuses the Pi's
  writes, even if the Pi is misconfigured. Your Windows login is a different
  user and keeps full access.
