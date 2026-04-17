#!/usr/bin/env bash
set -euo pipefail

if command -v git-filter-repo >/dev/null 2>&1; then
  echo "[OK] git-filter-repo already installed at $(command -v git-filter-repo)"
  exit 0
fi

echo "Installing git-filter-repo..."

if command -v pip3 >/dev/null 2>&1; then
  pip3 install --break-system-packages git-filter-repo
elif command -v pip >/dev/null 2>&1; then
  pip install --break-system-packages git-filter-repo
else
  echo "[ERR] pip/pip3 not found; install Python/pip and rerun"
  exit 1
fi

echo ""
echo "[OK] git-filter-repo installed successfully!"
echo ""
echo "USAGE:"
echo "  pf git-cleanup               # Interactive TUI for removing large files"
echo "  pf git-analyze-large-files   # List largest blobs in history"
echo "  pf git-repo-size             # Show repository size"
echo ""
echo "TEST:"
echo "  git-filter-repo --version"
echo ""
echo "NOTE: Ensure ~/.local/bin is in your PATH"
