#!/usr/bin/env bash

pe_container_runtime() {
  printf '%s\n' "${CONTAINER_RT:-podman}"
}

pe_require_runtime() {
  local runtime="${1:-}"
  if [[ -z "${runtime}" ]]; then
    echo "[error] container runtime is empty" >&2
    exit 1
  fi
  if ! command -v "${runtime}" >/dev/null 2>&1; then
    echo "[error] container runtime not found: ${runtime}" >&2
    exit 1
  fi
}

pe_require_image() {
  local runtime="${1:-}"
  local image="${2:-}"
  local build_hint="${3:-}"

  pe_require_runtime "${runtime}"
  if ! "${runtime}" image exists "${image}" >/dev/null 2>&1; then
    echo "[error] container image not found: ${image}" >&2
    if [[ -n "${build_hint}" ]]; then
      echo "Build it first: ${build_hint}" >&2
    fi
    exit 1
  fi
}

pe_require_file() {
  local input_path="${1:-}"
  local usage="${2:-Usage error}"
  local label="${3:-file}"

  if [[ -z "${input_path}" ]]; then
    echo "${usage}" >&2
    exit 1
  fi
  if [[ ! -f "${input_path}" ]]; then
    echo "[error] ${label} not found: ${input_path}" >&2
    exit 1
  fi
}

pe_ensure_dir() {
  local target_dir="${1:-}"
  mkdir -p "${target_dir}"
  printf '%s\n' "${target_dir}"
}

pe_input_dir() {
  local input_path="${1:-}"
  (cd "$(dirname "${input_path}")" && pwd)
}

pe_input_file() {
  local input_path="${1:-}"
  basename "${input_path}"
}
