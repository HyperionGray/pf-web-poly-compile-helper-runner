#!/usr/bin/env bash
# Run pf install tasks inside a disposable container so host packages stay untouched.
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./scripts/pf-install-in-container.sh <task> [task-args...]

Runs a pf task inside a container built from containers/development/Dockerfile.
Good for install-* tasks that would otherwise apt/dnf/yum the host.

Env vars:
  PF_INSTALL_IMAGE   Image tag to use/build (default: pf-dev:installer)
  PF_INSTALL_FILE    Pfyfile path inside repo (default: pf-files/Pfyfile.pf)
  CONTAINER_ENGINE   Override container engine (podman|docker)
  PF_DOCKERFILE      Override Dockerfile (default: containers/development/Dockerfile)
  NO_BUILD           If set, skip auto-build and fail if image missing
USAGE
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage; exit 0
fi

if [[ $# -lt 1 ]]; then
  usage; exit 1
fi

TASK="$1"; shift
TASK_ARGS=("$@")

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PFY_FILE_DEFAULT="pf-files/Pfyfile.pf"
PFY_FILE="${PF_INSTALL_FILE:-$PFY_FILE_DEFAULT}"
IMAGE="${PF_INSTALL_IMAGE:-pf-dev:installer}"
DOCKERFILE="${PF_DOCKERFILE:-containers/development/Dockerfile}"
ENGINE="${CONTAINER_ENGINE:-}"
if [[ -z "$ENGINE" ]]; then
  if command -v podman >/dev/null 2>&1; then
    ENGINE=podman
  elif command -v docker >/dev/null 2>&1; then
    ENGINE=docker
  else
    echo "No container engine found (podman|docker)." >&2
    exit 1
  fi
fi

# Build image if missing
if ! $ENGINE image inspect "$IMAGE" >/dev/null 2>&1; then
  if [[ -n "${NO_BUILD:-}" ]]; then
    echo "Image $IMAGE missing and NO_BUILD set; aborting." >&2
    exit 1
  fi
  echo "[pf-install] Building $IMAGE from $DOCKERFILE..."
  $ENGINE build -t "$IMAGE" -f "$ROOT_DIR/$DOCKERFILE" "$ROOT_DIR"
fi

# Prepare volume mount
WORK_MNT="$ROOT_DIR:/workspace"

# Run task inside container; we override entrypoint to use bash so we control env.
set -x
$ENGINE run --rm \
  -v "$WORK_MNT" \
  -w /workspace \
  --entrypoint bash \
  "$IMAGE" \
  -lc 'set -euo pipefail
       export DEBIAN_FRONTEND=noninteractive
       export PATH="/usr/local/bin:/root/.local/bin:/home/pf/.local/bin:$PATH"
       export PYTHONPATH="/workspace/pf-runner-full:$PYTHONPATH"
       python3 -m pip install --break-system-packages -U pip setuptools wheel >/dev/null
       python3 -m pip install --break-system-packages -e /workspace/pf-runner-full >/dev/null
       PFY_FILE="${PFY_FILE:-/workspace/'"$PFY_FILE"'}"
       python3 -m pf_main -f "$PFY_FILE" run "$@"' bash "$TASK" "${TASK_ARGS[@]}"
