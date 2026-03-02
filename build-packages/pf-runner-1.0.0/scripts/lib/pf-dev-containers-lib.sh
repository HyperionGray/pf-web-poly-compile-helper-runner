#!/usr/bin/env bash
#
# Shared helpers for pf development-environment container scripts.
# This file is meant to be sourced, not executed.
#
# Configuration is stored in `PF_DEV_CONFIG` (associative array).
#

if [[ -n "${__PF_DEV_CONTAINERS_LIB_SOURCED:-}" ]]; then
  return 0
fi
__PF_DEV_CONTAINERS_LIB_SOURCED=1

_pf_dev_containers_lib_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=pf-bash-lib.sh
source "${_pf_dev_containers_lib_dir}/pf-bash-lib.sh"
# shellcheck source=pf-dev-config.sh
source "${_pf_dev_containers_lib_dir}/pf-dev-config.sh"
# shellcheck source=pf-dev-services.sh
source "${_pf_dev_containers_lib_dir}/pf-dev-services.sh"

declare -gA PF_DEV_CONFIG=()

pf_dev_load_config() {
  local config_path="${1:-}"
  pf_dev_config_init "$config_path" PF_DEV_CONFIG
}

pf_dev_detect_deployment_type() {
  pf_dev_config_detect_runtime PF_DEV_CONFIG
}

pf_dev_check_requirements() {
  pf_dev_requirements_check PF_DEV_CONFIG
}

pf_dev_build_images() {
  local project_root="${1:?project root required}"
  pf_dev_images_build PF_DEV_CONFIG "$project_root"
}

pf_dev_setup_quadlet() {
  local project_root="${1:?project root required}"
  pf_dev_quadlet_setup PF_DEV_CONFIG "$project_root"
}

pf_dev_start_services() {
  local project_root="${1:?project root required}"
  local enable_units="${2:-false}"
  pf_dev_services_start PF_DEV_CONFIG "$project_root" "$enable_units"
}

pf_dev_stop_services() {
  local project_root="${1:?project root required}"
  pf_dev_services_stop PF_DEV_CONFIG "$project_root"
}

pf_dev_restart_services() {
  local project_root="${1:?project root required}"
  pf_dev_services_restart PF_DEV_CONFIG "$project_root"
}

pf_dev_test_deployment() {
  pf_dev_deployment_test
}

pf_dev_show_status() {
  local project_root="${1:?project root required}"
  pf_dev_status_show PF_DEV_CONFIG "$project_root"
}

pf_dev_show_logs() {
  local project_root="${1:?project root required}"
  local service="${2:-all}"
  pf_dev_logs_show PF_DEV_CONFIG "$project_root" "$service"
}

pf_dev_exec_container() {
  pf_dev_exec_container "$@"
}

pf_dev_run_pf_command() {
  pf_dev_run_pf_command "$@"
}

pf_dev_build_wasm() {
  pf_dev_build_wasm "$@"
}

pf_dev_cleanup() {
  local project_root="${1:?project root required}"
  pf_dev_cleanup_env PF_DEV_CONFIG "$project_root"
}

