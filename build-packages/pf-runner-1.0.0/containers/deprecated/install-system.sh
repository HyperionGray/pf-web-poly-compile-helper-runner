#!/usr/bin/env bash
# Install pf to /usr/local/bin/pf from ~/.local/bin/pf
# If running inside a container, print instructions to run on host.
set -euo pipefail

SRC="$HOME/.local/bin/pf"
DEST="/usr/local/bin/pf"

if [[ ! -f "$SRC" ]]; then
  echo "[install-system] Source binary not found: $SRC" >&2
  echo "Build it first: pf install-native (or pf install-full mode=native)" >&2
  exit 1
fi

IN_CONTAINER=false
{ [[ -f /.dockerenv ]] || [[ -f /run/.containerenv ]] ; } && IN_CONTAINER=true || true

if $IN_CONTAINER; then
  echo "[install-system] Detected container environment; cannot elevate on host from inside container."
  echo "Run on host: sudo install -m 0755 $SRC $DEST"
  exit 0
fi

if [[ $(id -u) -ne 0 ]]; then
  echo "[install-system] Using sudo to write $DEST"
  exec sudo install -m 0755 "$SRC" "$DEST"
else
  install -m 0755 "$SRC" "$DEST"
fi

echo "[install-system] Installed $DEST"
