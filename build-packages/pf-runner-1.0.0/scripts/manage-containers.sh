#!/usr/bin/env bash
set -euo pipefail

# pf Development Environment Container Management Script
#
# Configuration comes from `pf.config.json5` (and CLI flags), not environment variables.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_PATH_DEFAULT="${PROJECT_ROOT}/pf.config.json5"

# shellcheck disable=SC1091
source "${SCRIPT_DIR}/lib/pf-dev-containers-lib.sh"

show_help() {
  cat <<'EOF'
pf Development Environment Container Management

Usage: scripts/manage-containers.sh [OPTIONS] [COMMAND] [ARGS...]

Options:
  --config PATH         Use a specific pf.config.json5
  --help, -h            Show this help message

Commands:
  status                Show deployment status
  start                 Start all services
  stop                  Stop all services
  restart               Restart all services
  logs [SERVICE]        Show logs (all, web, build, security, dev)
  exec CONTAINER [CMD]  Execute command in container (web, build, security, dev)
  pf [ARGS...]          Run pf command in development container
  build [LANGUAGE]      Build WASM modules (all, rust, c, wat, fortran)
  cleanup               Stop and remove containers/images/volumes
EOF
}

main() {
  local config_path="$CONFIG_PATH_DEFAULT"

  while [[ $# -gt 0 ]]; do
    case "${1:-}" in
      --config)
        shift || true
        [[ $# -gt 0 ]] || die "--config requires a path"
        config_path="$1"
        shift || true
        ;;
      --config=*)
        config_path="${1#*=}"
        shift || true
        ;;
      --help|-h)
        show_help
        return 0
        ;;
      --)
        shift || true
        break
        ;;
      -*)
        die "Unknown option: $1"
        ;;
      *)
        break
        ;;
    esac
  done

  local command="${1:-status}"
  shift || true

  pf_dev_load_config "$config_path"
  if [[ ! -f "$config_path" ]]; then
    pf_dev_detect_deployment_type 2>/dev/null || true
  fi

  case "$command" in
    status)
      pf_dev_show_status "$PROJECT_ROOT"
      ;;
    start)
      pf_dev_start_services "$PROJECT_ROOT"
      ;;
    stop)
      pf_dev_detect_deployment_type 2>/dev/null || true
      pf_dev_stop_services "$PROJECT_ROOT"
      ;;
    restart)
      pf_dev_detect_deployment_type 2>/dev/null || true
      pf_dev_restart_services "$PROJECT_ROOT"
      ;;
    logs)
      pf_dev_detect_deployment_type 2>/dev/null || true
      pf_dev_show_logs "$PROJECT_ROOT" "${1:-all}"
      ;;
    exec)
      [[ $# -ge 1 ]] || die "exec requires a container name (web/build/security/dev)"
      local container="$1"
      shift || true
      pf_dev_exec_container "$container" "$@"
      ;;
    pf)
      pf_dev_run_pf_command "$@"
      ;;
    build)
      pf_dev_build_wasm "${1:-all}"
      ;;
    cleanup)
      pf_dev_cleanup "$PROJECT_ROOT"
      ;;
    help|--help|-h)
      show_help
      ;;
    *)
      die "Unknown command: $command"
      ;;
  esac
}

main "$@"

