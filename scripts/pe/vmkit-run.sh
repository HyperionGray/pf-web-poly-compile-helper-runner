#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

PE_PATH="${1:-}"
RUNTIME="$(pe_container_runtime)"
IMAGE="localhost/pf-pe-vmkit:latest"
WORKDIR="${PWD}"

pe_require_file "${PE_PATH}" "Usage: vmkit-run.sh /path/to/file.exe" "PE file"
pe_require_image "${RUNTIME}" "${IMAGE}" "pf pe build-vmkit"

VMKIT_IMAGE_DIR="$(pe_ensure_dir "${WORKDIR}/vmkit-images")"
PE_OUTPUT_DIR="$(pe_ensure_dir "${WORKDIR}/pe-output")"
PE_DIR="$(pe_input_dir "${PE_PATH}")"
PE_FILE="$(pe_input_file "${PE_PATH}")"

exec "${RUNTIME}" run --rm --pull=never \
  --device /dev/kvm \
  -v "${VMKIT_IMAGE_DIR}:/vmkit/images" \
  -v "${PE_DIR}:/vmkit/pe-input" \
  -v "${PE_OUTPUT_DIR}:/vmkit/pe-output" \
  "${IMAGE}" \
  vmkit-run.sh "/vmkit/pe-input/${PE_FILE}"
