#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/common.sh"

PE_PATH="${1:-}"
RUNTIME="$(pe_container_runtime)"
IMAGE="localhost/pf-pe-vmkit:latest"

pe_require_file "${PE_PATH}" "Usage: vmkit-analyze.sh /path/to/file.exe" "PE file"
pe_require_image "${RUNTIME}" "${IMAGE}" "pf pe build-vmkit"

PE_DIR="$(pe_input_dir "${PE_PATH}")"
PE_FILE="$(pe_input_file "${PE_PATH}")"

exec "${RUNTIME}" run --rm --pull=never \
  -v "${PE_DIR}:/vmkit/pe-input" \
  "${IMAGE}" \
  pf-analyze-pe.sh "/vmkit/pe-input/${PE_FILE}"
