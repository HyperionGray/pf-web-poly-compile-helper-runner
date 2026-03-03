#!/usr/bin/env bash
set -euo pipefail

# Wrapper to make the pf install-retdec task idempotent and bash-friendly.

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
SCRIPT="$ROOT/tools/lifting/install-retdec.sh"

FORCE="${force_build:-${FORCE_BUILD:-false}}"
SKIP="${skip_build:-${SKIP_BUILD:-false}}"

if [ ! -x "$SCRIPT" ]; then
  echo "[ERR] RetDec installer not found at $SCRIPT" >&2
  exit 127
fi

if command -v retdec-decompiler >/dev/null 2>&1 && [ "$FORCE" != "true" ]; then
  echo "[OK] RetDec already installed (retdec-decompiler found in PATH); skipping rebuild. Use force_build=true to rebuild."
  exit 0
fi

if [ "$SKIP" = "true" ]; then
  echo "[INFO] RetDec installer located at $SCRIPT (skip_build=true, exiting early)"
  exit 0
fi

bash "$SCRIPT"
