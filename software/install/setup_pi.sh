#!/usr/bin/env bash
# LaserTrack Pi setup. Run ON THE PI from ~/lasertrack (deploy.sh copies it).
# Every step is safe to run again.
#
#   bash install/setup_pi.sh all              base + fs42 + app (+ nas-mount if credentials exist)
#   bash install/setup_pi.sh base             apt packages, SPI on, no screen blanking, desktop autologin
#   bash install/setup_pi.sh nas-credentials  YOU run this: asks for the SMB user/password (hidden)
#   bash install/setup_pi.sh nas-mount        read-only mount of the media folder at /mnt/media
#   bash install/setup_pi.sh fs42             clone and install FieldStation42
#   bash install/setup_pi.sh app              LaserTrack venv, config, mpv.conf, services
#   bash install/setup_pi.sh output composite|hdmi   choose the TV output (reboot after)
set -euo pipefail

NAS_HOST="${NAS_HOST:-192.168.1.157}"
NAS_SHARE="${NAS_SHARE:-storage}"
NAS_SUBDIR="${NAS_SUBDIR:-media}"
MOUNT_POINT="/mnt/media"
CRED_FILE="/etc/lasertrack/smb-credentials"
FS42_DIR="$HOME/FieldStation42"
FS42_REPO="https://github.com/shane-mason/FieldStation42"
FS42_REF="${FS42_REF:-main}"
APP_DIR="$HOME/lasertrack"
CFG_DIR="$HOME/.config/lasertrack"
BOOT=/boot/firmware

say() { printf '\n\033[1;33m== %s\033[0m\n' "$*"; }

step_base() {
  say "apt packages"
  sudo apt-get update
  sudo apt-get install -y mpv ffmpeg cifs-utils git rsync \
    python3-venv python3-pip python3-spidev python3-gpiozero python3-lgpio
  say "SPI on (RC522), screen blanking off, boot to desktop with autologin"
  sudo raspi-config nonint do_spi 0
  sudo raspi-config nonint do_blanking 1
  sudo raspi-config nonint do_boot_behaviour B4
}

step_nas_credentials() {
  say "SMB credentials for //$NAS_HOST/$NAS_SHARE (stored root-only in $CRED_FILE)"
  echo "Use an OMV user that has READ-ONLY access to the share if you can."
  read -rp "SMB username: " smb_user
  read -rsp "SMB password (hidden): " smb_pass; echo
  sudo install -d -m 700 /etc/lasertrack
  printf 'username=%s\npassword=%s\n' "$smb_user" "$smb_pass" | sudo tee "$CRED_FILE" >/dev/null
  sudo chmod 600 "$CRED_FILE"; sudo chown root:root "$CRED_FILE"
  unset smb_pass
  echo "Saved. Next: bash install/setup_pi.sh nas-mount"
}

step_nas_mount() {
  [ -f "$CRED_FILE" ] || sudo test -f "$CRED_FILE" || {
    echo "No $CRED_FILE yet: run 'bash install/setup_pi.sh nas-credentials' first."; return 1; }
  say "Read-only CIFS mount //$NAS_HOST/$NAS_SHARE/$NAS_SUBDIR -> $MOUNT_POINT"
  # ro                       the kernel refuses every write, delete or rename
  # file_mode/dir_mode       files also look read-only to every program
  # x-systemd.automount      mounts on first access, so boot never waits on the NAS
  # nofail                   a missing NAS can't stop the Pi booting
  local opts="ro,credentials=$CRED_FILE,uid=$(id -u),gid=$(id -g),file_mode=0444,dir_mode=0555"
  opts+=",vers=3.1.1,iocharset=utf8,nofail,_netdev,x-systemd.automount,x-systemd.mount-timeout=30"
  local line="//$NAS_HOST/$NAS_SHARE/$NAS_SUBDIR $MOUNT_POINT cifs $opts 0 0"
  sudo mkdir -p "$MOUNT_POINT"
  sudo cp -n /etc/fstab /etc/fstab.lasertrack.bak
  sudo sed -i "\# $MOUNT_POINT cifs #d" /etc/fstab
  echo "$line" | sudo tee -a /etc/fstab >/dev/null
  sudo systemctl daemon-reload
  sudo systemctl restart "$(systemd-escape -p --suffix=automount "$MOUNT_POINT")"
  ls "$MOUNT_POINT" >/dev/null  # triggers the mount
  findmnt -no FSTYPE,OPTIONS "$MOUNT_POINT"
  say "Verifying the mount is read-only"
  findmnt -no OPTIONS "$MOUNT_POINT" | tr ',' '\n' | grep -qx ro || {
    echo "ERROR: $MOUNT_POINT is not mounted ro. Stopping."; exit 1; }
  if sudo touch "$MOUNT_POINT/.lasertrack-write-test" 2>/dev/null; then
    sudo rm -f "$MOUNT_POINT/.lasertrack-write-test"
    echo "ERROR: a write succeeded on $MOUNT_POINT. Unmounting."; sudo umount "$MOUNT_POINT"; exit 1
  fi
  echo "OK: writes are refused (even as root). Top level:"; ls "$MOUNT_POINT"
}

step_fs42() {
  say "FieldStation42 ($FS42_REF)"
  if [ ! -d "$FS42_DIR/.git" ]; then
    git clone "$FS42_REPO" "$FS42_DIR"
  fi
  git -C "$FS42_DIR" fetch --quiet origin
  git -C "$FS42_DIR" checkout --quiet "$FS42_REF"
  [ "$FS42_REF" = main ] && git -C "$FS42_DIR" pull --quiet --ff-only origin main
  (cd "$FS42_DIR" && bash install.sh)
  mkdir -p "$CFG_DIR"
  git -C "$FS42_DIR" rev-parse HEAD | tee "$CFG_DIR/fs42-commit"
}

step_app() {
  say "LaserTrack venv"
  # System site packages give the venv apt's spidev/gpiozero/lgpio (Pi-only).
  [ -x "$APP_DIR/.venv/bin/python" ] || python3 -m venv --system-site-packages "$APP_DIR/.venv"
  "$APP_DIR/.venv/bin/pip" install --quiet --upgrade pip
  "$APP_DIR/.venv/bin/pip" install --quiet -e "$APP_DIR"
  say "Config"
  mkdir -p "$CFG_DIR"
  [ -f "$CFG_DIR/config.toml" ] || cp "$APP_DIR/config/config.example.toml" "$CFG_DIR/config.toml"
  mkdir -p "$HOME/.config/mpv"
  if [ -f "$HOME/.config/mpv/mpv.conf" ] && ! cmp -s "$APP_DIR/config/mpv.conf" "$HOME/.config/mpv/mpv.conf"; then
    cp "$HOME/.config/mpv/mpv.conf" "$HOME/.config/mpv/mpv.conf.bak.$(date +%s)"
  fi
  cp "$APP_DIR/config/mpv.conf" "$HOME/.config/mpv/mpv.conf"
  say "Services"
  mkdir -p "$HOME/.config/systemd/user" "$HOME/.config/autostart"
  cp "$APP_DIR"/install/systemd/*.service "$HOME/.config/systemd/user/"
  cp "$APP_DIR/install/lasertrack.desktop" "$HOME/.config/autostart/"
  systemctl --user daemon-reload
  echo "Installed. They start with the desktop session after a reboot."
}

step_output() {
  local mode="${1:-}"
  [[ "$mode" == composite || "$mode" == hdmi ]] || { echo "usage: output composite|hdmi"; exit 1; }
  local cfg="$BOOT/config.txt" cmd="$BOOT/cmdline.txt"
  say "Video output: $mode"
  sudo cp -n "$cfg" "$cfg.lasertrack.bak"; sudo cp -n "$cmd" "$cmd.lasertrack.bak"
  # Remove anything a previous run added.
  sudo sed -i '/^# >>> lasertrack output/,/^# <<< lasertrack output/d' "$cfg"
  sudo sed -i '/^enable_tvout=1$/d' "$cfg"  # also a hand-added one (README step 1.6)
  sudo sed -i -E 's/ video=Composite-1:[^ ]*//g; s/ vc4\.tv_norm=[^ ]*//g' "$cmd"
  sudo sed -i -E 's/^dtoverlay=vc4-kms-v3d,composite$/dtoverlay=vc4-kms-v3d/' "$cfg"
  if [ "$mode" = composite ]; then
    # Pi 4 composite: enable the TV encoder and tell the KMS driver about it.
    # NTSC 480i (North American CRT). For PAL use 720x576@50ie and PAL.
    sudo sed -i -E 's/^dtoverlay=vc4-kms-v3d$/dtoverlay=vc4-kms-v3d,composite/' "$cfg"
    printf '# >>> lasertrack output\n[all]\nenable_tvout=1\n# <<< lasertrack output\n' | sudo tee -a "$cfg" >/dev/null
    sudo sed -i -E '1 s/$/ video=Composite-1:720x480@60ie vc4.tv_norm=NTSC/' "$cmd"
  fi
  [ -f "$CFG_DIR/config.toml" ] && sed -i -E "s/^output = .*/output = \"$mode\"/" "$CFG_DIR/config.toml"
  grep -n 'vc4-kms\|enable_tvout' "$cfg"; cat "$cmd"
  echo "Reboot to apply: sudo reboot"
}

case "${1:-}" in
  all)
    step_base
    if sudo test -f "$CRED_FILE"; then step_nas_mount; else echo "(skipping nas-mount: run nas-credentials first)"; fi
    step_fs42; step_app ;;
  base) step_base ;;
  nas-credentials) step_nas_credentials ;;
  nas-mount) step_nas_mount ;;
  fs42) step_fs42 ;;
  app) step_app ;;
  output) step_output "${2:-}" ;;
  *) sed -n '2,13p' "$0"; exit 1 ;;
esac
