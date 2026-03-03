#!/usr/bin/env bash
set -euo pipefail

if command -v git-filter-repo >/dev/null 2>&1; then
  echo "OK git-filter-repo already installed"
  exit 0
fi

if command -v pip3 >/dev/null 2>&1; then
  pip3 install --user --break-system-packages git-filter-repo
elif command -v pip >/dev/null 2>&1; then
  pip install --user --break-system-packages git-filter-repo
else
  echo "ERROR: pip/pip3 not found; install Python/pip and rerun"
  exit 1
fi

echo "OK git-filter-repo installed (ensure ~/.local/bin is in PATH)"
