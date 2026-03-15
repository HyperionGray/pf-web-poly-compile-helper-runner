#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/pf-bash-lib.sh
source "${SCRIPT_DIR}/../lib/pf-bash-lib.sh"

DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: install-git-filter-repo.sh [--dry-run] [--help]

Install git-filter-repo via pip/pip3.

Options:
  --dry-run   Print actions without installing anything
  -h, --help  Show this help message and exit
EOF
}

run_cmd() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[DRY-RUN]'
    printf ' %q' "$@"
    printf '\n'
    return 0
  fi
  "$@"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      log_error "Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
  shift
done

if command_exists git-filter-repo && [[ "$DRY_RUN" -eq 0 ]]; then
  echo "[OK] git-filter-repo already installed at $(command -v git-filter-repo)"
  exit 0
fi

echo "Installing git-filter-repo..."
[[ "$DRY_RUN" -eq 1 ]] && echo "[DRY-RUN] No changes will be made."

if command_exists pip3; then
  run_cmd pip3 install --user --break-system-packages git-filter-repo
elif command_exists pip; then
  run_cmd pip install --user --break-system-packages git-filter-repo
else
  die "pip/pip3 not found; install Python/pip and rerun"
fi

echo ""
echo "[OK] git-filter-repo installation flow completed!"
if [[ "$DRY_RUN" -eq 0 ]]; then
  if command_exists git-filter-repo; then
    echo "[OK] $(git-filter-repo --version)"
  else
    echo "[WARN] git-filter-repo not found in PATH yet."
  fi
fi
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
