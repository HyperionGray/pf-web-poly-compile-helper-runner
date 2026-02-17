#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}"
PF_RUNNER_DIR="${REPO_ROOT}/pf-runner"

if [[ ! -d "${PF_RUNNER_DIR}" ]]; then
  echo "[error] pf-runner directory not found at ${PF_RUNNER_DIR}" >&2
  exit 1
fi

cd "${PF_RUNNER_DIR}"
chmod +x scripts/system-setup.sh
scripts/system-setup.sh update
scripts/system-setup.sh upgrade
scripts/system-setup.sh setup-venv
scripts/system-setup.sh install-base
scripts/system-setup.sh install-build-tools
make build
sudo make install
