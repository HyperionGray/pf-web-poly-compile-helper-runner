#!/usr/bin/env bash
set -euo pipefail

if [ ! -d .git ]; then
  echo "ERROR: no .git directory found in current directory"
  exit 1
fi

echo "Repository size:"
du -sh .git 2>/dev/null || true
echo ""
echo "Top .git directories:"
du -sh .git/* 2>/dev/null | sort -hr | head -n 15 || true
