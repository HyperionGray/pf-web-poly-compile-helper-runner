#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

PE_PATH="${1:-}"
RUNTIME="$(pe_container_runtime)"
IMAGE="localhost/pf-pe-windows-server:latest"
WORKDIR="${PWD}"

pe_require_file "${PE_PATH}" "Usage: windows-server-run.sh /path/to/file.exe" "PE file"
pe_require_image "${RUNTIME}" "${IMAGE}" "pf pe build-windows-server"

WINDOWS_IMAGE_DIR="$(pe_ensure_dir "${WORKDIR}/windows-images")"
PE_OUTPUT_DIR="$(pe_ensure_dir "${WORKDIR}/pe-output")"
PE_DIR="$(pe_input_dir "${PE_PATH}")"
PE_FILE="$(pe_input_file "${PE_PATH}")"

exec "${RUNTIME}" run --rm --pull=never \
  --privileged \
  --device /dev/kvm \
  -v "${WINDOWS_IMAGE_DIR}:/opt/windows-images" \
  -v "${PE_DIR}:/workspace/pe-input" \
  -v "${PE_OUTPUT_DIR}:/artifacts/pe-results" \
  "${IMAGE}" \
  pf-execute-pe "/workspace/pe-input/${PE_FILE}"
