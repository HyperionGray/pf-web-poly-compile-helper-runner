#!/usr/bin/env bash
#
# Configuration helpers for pf development containers.
# Keeps configuration in an associative array passed by name
# instead of using environment variables.
#

if [[ -n "${__PF_DEV_CONFIG_SOURCED:-}" ]]; then
  return 0
fi
__PF_DEV_CONFIG_SOURCED=1

_pf_dev_config_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=pf-bash-lib.sh
source "${_pf_dev_config_dir}/pf-bash-lib.sh"
# shellcheck source=pf-json5-lib.sh
source "${_pf_dev_config_dir}/pf-json5-lib.sh"

pf_dev_systemctl_user_available() {
  command_exists systemctl || return 1
  systemctl --user show-environment >/dev/null 2>&1
}

pf_dev_config_validate() {
  local target_ref="$1"
  local -n cfg="$target_ref"

  if [[ "${cfg[use_quadlet]:-false}" == "true" ]] && ! pf_dev_systemctl_user_available; then
    log_warning "Quadlet requested, but systemd user services are not available; falling back to podman-compose."
    cfg["use_quadlet"]="false"
  fi
}

pf_dev_config_init() {
  local config_path="${1:-}"
  local target_ref="${2:-}"

  [[ -n "$target_ref" ]] || die "pf_dev_config_init requires target associative array name"

  # shellcheck disable=SC2034
  declare -gA "$target_ref"
  local -n cfg="$target_ref"
  cfg=(["use_quadlet"]="false" ["gpu_support"]="false")

  if pf_dev_systemctl_user_available; then
    cfg["use_quadlet"]="true"
  fi

  if [[ -n "$config_path" && -f "$config_path" ]]; then
    cfg["use_quadlet"]="$(pf_json5_get "$config_path" "devEnvironment.useQuadlet" "${cfg[use_quadlet]}")"
    cfg["gpu_support"]="$(pf_json5_get "$config_path" "devEnvironment.gpuSupport" "${cfg[gpu_support]}")"
  fi

  pf_dev_config_validate "$target_ref"
}

pf_dev_config_set() {
  local target_ref="$1"
  local key="$2"
  local value="$3"
  local -n cfg="$target_ref"
  cfg["$key"]="$value"
}

pf_dev_config_get() {
  local target_ref="$1"
  local key="$2"
  local -n cfg="$target_ref"
  printf '%s\n' "${cfg[$key]}"
}

pf_dev_config_detect_runtime() {
  local target_ref="$1"
  local -n cfg="$target_ref"

  if command_exists systemctl; then
    if systemctl --user is-active pf-main-pod.service &>/dev/null || \
      systemctl --user is-active pf-main-pod-gpu.service &>/dev/null; then
      cfg["use_quadlet"]="true"
      cfg["gpu_support"]="false"
      if systemctl --user is-active pf-main-pod-gpu.service &>/dev/null; then
        cfg["gpu_support"]="true"
      fi
      return 0
    fi
  fi

  if command_exists podman; then
    if podman pod exists pf-main-pod &>/dev/null || \
      podman pod exists pf-main-pod-gpu &>/dev/null; then
      cfg["use_quadlet"]="false"
      cfg["gpu_support"]="false"
      if podman pod exists pf-main-pod-gpu &>/dev/null; then
        cfg["gpu_support"]="true"
      fi
      return 0
    fi
  fi

  log_warning "No active deployment detected"
  return 1
}

pf_dev_config_summary() {
  local target_ref="$1"
  local -n cfg="$target_ref"
  printf '%s\n' "- GPU Support: ${cfg[gpu_support]}"
  printf '%s\n' "- Use Quadlet: ${cfg[use_quadlet]}"
}

