#!/usr/bin/env bash
set -euo pipefail

RUNTIME="${CONTAINER_RT:-podman}"
IMAGE="localhost/pf-pe-vmkit:latest"
WORKDIR="${PWD}"

if ! "${RUNTIME}" image exists "${IMAGE}" >/dev/null 2>&1; then
  echo "[error] VMKit PE image not found."
  echo "Build it first: pf pe build-vmkit"
  exit 1
fi

mkdir -p "${WORKDIR}/vmkit-images"

exec "${RUNTIME}" run --rm \
  -v "${WORKDIR}/vmkit-images:/vmkit/images" \
  "${IMAGE}" \
  vmkit-create.sh --all-the-passthru
