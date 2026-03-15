#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

RUNTIME="$(pe_container_runtime)"
IMAGE="localhost/pf-pe-windows-server:latest"
WORKDIR="${PWD}"

pe_require_image "${RUNTIME}" "${IMAGE}" "pf pe build-windows-server"

WINDOWS_IMAGE_DIR="$(pe_ensure_dir "${WORKDIR}/windows-images")"

exec "${RUNTIME}" run --rm --pull=never \
  --privileged \
  -v "${WINDOWS_IMAGE_DIR}:/opt/windows-images" \
  "${IMAGE}" \
  pf-prepare-windows
