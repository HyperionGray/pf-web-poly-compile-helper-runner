#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
cd "${SCRIPT_DIR}/../pf-runner-full"
chmod +x scripts/system-setup.sh
scripts/system-setup.sh update
scripts/system-setup.sh upgrade
scripts/system-setup.sh setup-venv
scripts/system-setup.sh install-base
scripts/system-setup.sh install-build-tools
make build
sudo make install
