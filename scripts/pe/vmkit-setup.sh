#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

RUNTIME="$(pe_container_runtime)"
IMAGE="localhost/pf-pe-vmkit:latest"
WORKDIR="${PWD}"
pe_require_image "${RUNTIME}" "${IMAGE}" "pf pe build-vmkit"

VMKIT_IMAGE_DIR="$(pe_ensure_dir "${WORKDIR}/vmkit-images")"

exec "${RUNTIME}" run --rm --pull=never \
  -v "${VMKIT_IMAGE_DIR}:/vmkit/images" \
  "${IMAGE}" \
  vmkit-create.sh --all-the-passthru
