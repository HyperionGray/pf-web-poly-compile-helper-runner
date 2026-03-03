#!/usr/bin/env bash
set -euo pipefail

# pf Development Environment Container Management Script
#
# Configuration comes from `pf.config.json5` (and CLI flags), not environment variables.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_PATH_DEFAULT="${PROJECT_ROOT}/pf.config.json5"


# Configuration
USE_QUADLET="${USE_QUADLET:-true}"
GPU_SUPPORT="${GPU_SUPPORT:-false}"

# Functions
log_info() {
    echo "INFO $*"
}

log_success() {
    echo "OK $*"
}

log_warning() {
    echo "WARN $*"
}

log_error() {
    echo "ERROR $*"
}

detect_deployment_type() {
    if systemctl --user is-active pf-main-pod.service &> /dev/null || \
       systemctl --user is-active pf-main-pod-gpu.service &> /dev/null; then
        USE_QUADLET=true
        if systemctl --user is-active pf-main-pod-gpu.service &> /dev/null; then
            GPU_SUPPORT=true
        fi
    elif podman pod exists pf-main-pod &> /dev/null || \
         podman pod exists pf-main-pod-gpu &> /dev/null; then
        USE_QUADLET=false
        if podman pod exists pf-main-pod-gpu &> /dev/null; then
            GPU_SUPPORT=true
        fi
    else
        log_warning "No active deployment detected"
        return 1
    fi
}

show_status() {
    log_info "Checking pf Development Environment status..."
    
    if ! detect_deployment_type; then
        log_error "No deployment found"
        return 1
    fi
    
    echo ""
    echo "Deployment Type: $([ "$USE_QUADLET" = "true" ] && echo "Quadlet" || echo "Podman Compose")"
    echo "GPU Support: $([ "$GPU_SUPPORT" = "true" ] && echo "Enabled" || echo "Disabled")"
    echo ""
    
    if [ "$USE_QUADLET" = "true" ]; then
        local pod_service="pf-main-pod.service"
        if [ "$GPU_SUPPORT" = "true" ]; then
            pod_service="pf-main-pod-gpu.service"
        fi
        
        echo "Pod Status:"
        systemctl --user status "$pod_service" --no-pager -l
        echo ""
        
        echo "Container Services:"
        systemctl --user list-units 'pf-*-service.service' --no-pager
    else
        cd "$PROJECT_ROOT"
        echo "Podman Compose Status:"
        podman-compose ps
    fi
    
    echo ""
    echo "Container Status:"
    podman ps --filter label=app=pf-development --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    echo "Network Status:"
    podman network ls --filter name=pf-network
    
    echo ""
    echo "Volume Status:"
    podman volume ls --filter label=app=pf-development
}

start_services() {
    log_info "Starting pf Development Environment..."
    
    if [ "$USE_QUADLET" = "true" ]; then
        local pod_service="pf-main-pod.service"
        if [ "$GPU_SUPPORT" = "true" ]; then
            pod_service="pf-main-pod-gpu.service"
        fi
        
        systemctl --user start "$pod_service"
        log_success "Services started via Quadlet"
    else
        cd "$PROJECT_ROOT"
        if [ "$GPU_SUPPORT" = "true" ]; then
            podman-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
        else
            podman-compose up -d
        fi
        log_success "Services started via Podman Compose"
    fi
}

stop_services() {
    log_info "Stopping pf Development Environment..."
    
    if [ "$USE_QUADLET" = "true" ]; then
        local pod_service="pf-main-pod.service"
        if [ "$GPU_SUPPORT" = "true" ]; then
            pod_service="pf-main-pod-gpu.service"
        fi
        
        systemctl --user stop "$pod_service"
        log_success "Services stopped via Quadlet"
    else
        cd "$PROJECT_ROOT"
        podman-compose down
        log_success "Services stopped via Podman Compose"
    fi
}

restart_services() {
    log_info "Restarting pf Development Environment..."
    stop_services
    sleep 2
    start_services
}

show_logs() {
    local service="${1:-all}"
    
    if [ "$USE_QUADLET" = "true" ]; then
        case "$service" in
            "all")
                local pod_service="pf-main-pod.service"
                if [ "$GPU_SUPPORT" = "true" ]; then
                    pod_service="pf-main-pod-gpu.service"
                fi
                journalctl --user -u "$pod_service" -f
                ;;
            "web")
                journalctl --user -u pf-web-service.service -f
                ;;
            "build")
                journalctl --user -u pf-build-service.service -f
                ;;
            "security")
                journalctl --user -u pf-security-service.service -f
                ;;
            "dev")
                journalctl --user -u pf-dev-service.service -f
                ;;
            *)
                log_error "Unknown service: $service"
                return 1
                ;;
        esac
    else
        cd "$PROJECT_ROOT"
        if [ "$service" = "all" ]; then
            podman-compose logs -f
        else
            podman-compose logs -f "$service-service"
        fi
    fi
}

exec_container() {
    local container="$1"
    local command="${2:-bash}"
    
    case "$container" in
        "web")
            podman exec -it pf-web-service "$command"
            ;;
        "build")
            podman exec -it pf-build-service "$command"
            ;;
        "security")
            podman exec -it pf-security-service "$command"
            ;;
        "dev")
            podman exec -it pf-dev-service "$command"
            ;;
        *)
            log_error "Unknown container: $container"
            echo "Available containers: web, build, security, dev"
            return 1
            ;;
    esac
}

run_pf_command() {
    local pf_args="$*"
    log_info "Running pf command: $pf_args"
    podman exec -it pf-dev-service pf $pf_args
}

build_wasm() {
    local language="${1:-all}"
    
    case "$language" in
        "all")
            log_info "Building all WASM modules..."
            podman exec pf-build-service ./entrypoint.sh build-all
            ;;
        "rust")
            log_info "Building Rust WASM..."
            podman exec pf-build-service ./entrypoint.sh build-rust
            ;;
        "c")
            log_info "Building C WASM..."
            podman exec pf-build-service ./entrypoint.sh build-c
            ;;
        "wat")
            log_info "Building WAT WASM..."
            podman exec pf-build-service ./entrypoint.sh build-wat
            ;;
        "fortran")
            log_info "Building Fortran WASM..."
            podman exec pf-build-service ./entrypoint.sh build-fortran
            ;;
        *)
            log_error "Unknown language: $language"
            echo "Available languages: all, rust, c, wat, fortran"
            return 1
            ;;
    esac
    
    log_success "Build completed"
}

cleanup() {
    log_info "Cleaning up pf Development Environment..."
    
    # Stop services
    stop_services 2>/dev/null || true
    
    # Remove containers
    podman rm -f pf-web-service pf-build-service pf-security-service pf-dev-service 2>/dev/null || true
    
    # Remove pod
    podman pod rm -f pf-main-pod pf-main-pod-gpu 2>/dev/null || true
    
    # Remove images (optional)
    read -p "Remove container images? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        podman rmi -f localhost/pf-web-services:latest \
                     localhost/pf-build-environment:latest \
                     localhost/pf-security-tools:latest \
                     localhost/pf-development:latest \
                     localhost/pf-base:latest 2>/dev/null || true
    fi
    
    # Remove volumes (optional)
    read -p "Remove persistent volumes? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        podman volume rm -f pf-workspace pf-builds pf-cache 2>/dev/null || true
    fi
    
    log_success "Cleanup completed"
}

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

