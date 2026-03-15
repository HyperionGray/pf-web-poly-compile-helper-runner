#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

RUNTIME="$(pe_container_runtime)"
IMAGE="localhost/pf-pe-reactos:latest"
WORKDIR="${PWD}"

pe_require_image "${RUNTIME}" "${IMAGE}" "pf pe build-reactos"

REACTOS_IMAGE_DIR="$(pe_ensure_dir "${WORKDIR}/reactos-images")"

exec "${RUNTIME}" run --rm --pull=never \
  -v "${REACTOS_IMAGE_DIR}:/reactos/images" \
  "${IMAGE}" \
  setup-reactos.sh
