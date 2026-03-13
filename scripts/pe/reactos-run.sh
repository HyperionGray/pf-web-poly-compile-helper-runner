#!/usr/bin/env bash
set -euo pipefail

PE_PATH="${1:-}"
RUNTIME="${CONTAINER_RT:-podman}"
IMAGE="localhost/pf-pe-reactos:latest"
WORKDIR="${PWD}"

if [[ -z "${PE_PATH}" ]]; then
  echo "Usage: reactos-run.sh /path/to/file.exe"
  exit 1
fi

if [[ ! -f "${PE_PATH}" ]]; then
  echo "[error] PE file not found: ${PE_PATH}"
  exit 1
fi

if ! "${RUNTIME}" image exists "${IMAGE}" >/dev/null 2>&1; then
  echo "[error] ReactOS PE image not found."
  echo "Build it first: pf pe build-reactos"
  exit 1
fi

mkdir -p "${WORKDIR}/reactos-images" "${WORKDIR}/pe-output"

PE_DIR="$(cd "$(dirname "${PE_PATH}")" && pwd)"
PE_FILE="$(basename "${PE_PATH}")"

exec "${RUNTIME}" run --rm --device /dev/kvm \
  -v "${WORKDIR}/reactos-images:/reactos/images" \
  -v "${PE_DIR}:/reactos/pe-input" \
  -v "${WORKDIR}/pe-output:/reactos/pe-output" \
  "${IMAGE}" \
  run-pe.sh "/reactos/pe-input/${PE_FILE}"
