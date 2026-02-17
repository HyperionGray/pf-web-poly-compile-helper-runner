#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONTAINERS_DIR="${PROJECT_ROOT}/containers/scripts"
RUN_DEV="${CONTAINERS_DIR}/run-dev.sh"
BUILD_CONTAINERS="${CONTAINERS_DIR}/build-containers.sh"

log() { printf '[containers] %s\n' "$*"; }
die() { log "ERROR: $*" >&2; exit 1; }

[[ -x "$RUN_DEV" ]] || die "run-dev.sh not found (expected ${RUN_DEV})"
[[ -x "$BUILD_CONTAINERS" ]] || die "build-containers.sh not found (expected ${BUILD_CONTAINERS})"

cmd="${1:-start}"
case "$cmd" in
  install|start|up)
    log "Building container images (all)"
    "$BUILD_CONTAINERS" all
    log "Starting development stack"
    "$RUN_DEV" start
    ;;
  rebuild)
    log "Rebuilding container images without cache"
    "$BUILD_CONTAINERS" --no-cache all
    ;;
  stop|down)
    "$RUN_DEV" down
    ;;
  status)
    "$RUN_DEV" status
    ;;
  logs)
    shift || true
    "$RUN_DEV" logs "${1:-}"
    ;;
  help|--help|-h)
    cat <<'EOF_HELP'
install-containers.sh - thin wrapper to provision pf dev containers

Usage: scripts/install-containers.sh [command]

Commands:
  start|install|up   Build images (all) and start the dev stack
  rebuild            Rebuild images without cache
  stop|down          Stop running containers
  status             Show container status
  logs [name]        Tail logs (default: all)
  help               Show this help
EOF_HELP
    ;;
  *)
    die "Unknown command: $cmd"
    ;;

esac
