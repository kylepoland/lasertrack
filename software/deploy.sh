#!/usr/bin/env bash
# Copy software/ from this Mac to the Pi (~/lasertrack), then optionally
# reinstall and restart the daemon.
#
#   ./deploy.sh            copy only
#   ./deploy.sh --restart  copy, pip install, restart lasertrack.service
#
# Uses the SSH host alias "lasertrack" (see README: ~/.ssh/config).
set -euo pipefail
PI="${PI:-lasertrack}"
cd "$(dirname "$0")"
rsync -az --delete \
  --exclude .venv --exclude __pycache__ --exclude '*.egg-info' --exclude .pytest_cache \
  ./ "$PI:lasertrack/"
echo "Copied to $PI:~/lasertrack"
if [[ "${1:-}" == "--restart" ]]; then
  ssh "$PI" 'cd ~/lasertrack && .venv/bin/pip install --quiet -e . && systemctl --user restart lasertrack.service && systemctl --user --no-pager status lasertrack.service | head -5'
fi
