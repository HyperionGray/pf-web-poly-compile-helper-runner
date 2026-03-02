#!/usr/bin/env bash
# Build native pf binary inside the pf container and drop it onto the host via HOME mount
# Result: $HOME/.local/bin/pf
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)"
cd "${ROOT_DIR}/pf-runner"

# Ensure PyInstaller is available (inside container)
python3 -m pip install --break-system-packages -q pyinstaller || python3 -m pip install -q pyinstaller

# Prefer Makefile target if present
if grep -q '^build:' Makefile 2>/dev/null; then
  make build
else
  pyinstaller -F -n pf_parser pf_parser.py
fi

BIN_SRC="dist/pf_parser"
if [[ ! -f "$BIN_SRC" ]]; then
  echo "[install-native] build output missing: $BIN_SRC" >&2
  exit 1
fi

HOST_BIN_DIR="${HOME}/.local/bin"
mkdir -p "$HOST_BIN_DIR"
install -m 0755 "$BIN_SRC" "${HOST_BIN_DIR}/pf"

echo "[install-native] Installed ${HOST_BIN_DIR}/pf"
command -v pf >/dev/null 2>&1 || echo "Add ${HOST_BIN_DIR} to your PATH"