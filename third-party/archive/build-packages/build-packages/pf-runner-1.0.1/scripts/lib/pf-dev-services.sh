#!/usr/bin/env bash
#
# Operational helpers for pf development containers.
# Intended to be sourced (not executed).
#

if [[ -n "${__PF_DEV_SERVICES_SOURCED:-}" ]]; then
  return 0
fi
__PF_DEV_SERVICES_SOURCED=1

_pf_dev_services_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=pf-bash-lib.sh
source "${_pf_dev_services_dir}/pf-bash-lib.sh"

pf_dev_requirements_check() {
  local cfg_ref="$1"
  local -n cfg="$cfg_ref"

  log_info "Checking system requirements..."

  if ! command_exists podman; then
    log_error "Podman is not installed. Please install Podman first."
    printf '%s\n' "Ubuntu/Debian: sudo apt-get install podman"
    printf '%s\n' "Fedora: sudo dnf install podman"
    printf '%s\n' "Arch: sudo pacman -S podman"
    return 1
  fi

  if ! command_exists podman-compose; then
    log_warning "podman-compose not found; attempting to install via pip..."
    if command_exists pip3; then
      pip3 install --user podman-compose
    elif command_exists python3; then
      python3 -m pip install --user podman-compose
    else
      log_error "pip3/python3 not found; cannot install podman-compose automatically"
      return 1
    fi
  fi

  if [[ "${cfg[use_quadlet]:-false}" == "true" ]]; then
    mkdir -p "$(pf_containers_systemd_dir)"
  fi

  if [[ "${cfg[gpu_support]:-false}" == "true" ]]; then
    if ! command_exists nvidia-smi; then
      log_warning "nvidia-smi not found. GPU support may not work."
    fi
    if ! command_exists nvidia-ctk; then
      log_warning "nvidia-ctk not found. Install NVIDIA Container Toolkit if you need GPU containers."
    fi
  fi

  log_success "Requirements check completed"
  return 0
}

pf_dev_images_build() {
  local cfg_ref="$1"
  local project_root="$2"

  log_info "Building container images..."
  cd "$project_root" || return 1

  log_info "Building base image..."
  podman build -t localhost/pf-base:latest -f containers/base/Dockerfile .

  log_info "Building web services image..."
  podman build -t localhost/pf-web-services:latest -f containers/web-services/Dockerfile .

  log_info "Building build environment image..."
  podman build -t localhost/pf-build-environment:latest -f containers/build-environment/Dockerfile .

  log_info "Building security tools image..."
  podman build -t localhost/pf-security-tools:latest -f containers/security-tools/Dockerfile .

  log_info "Building development environment image..."
  podman build -t localhost/pf-development:latest -f containers/development/Dockerfile .

  log_success "All images built successfully"
  return 0
}

pf_dev_quadlet_setup() {
  local cfg_ref="$1"
  local project_root="$2"
  local -n cfg="$cfg_ref"

  if [[ "${cfg[use_quadlet]:-false}" != "true" ]]; then
    return 0
  fi

  log_info "Setting up Quadlet configuration..."
  local config_dir=""
  config_dir="$(pf_containers_systemd_dir)"
  mkdir -p "$config_dir"

  shopt -s nullglob
  local quadlet_files=("${project_root}"/quadlet/*.{pod,container,network,volume})
  shopt -u nullglob

  if [[ ${#quadlet_files[@]} -gt 0 ]]; then
    cp "${quadlet_files[@]}" "${config_dir}/"
  fi

  systemctl --user daemon-reload
  log_success "Quadlet configuration installed"
  return 0
}

pf_dev_services_start() {
  local cfg_ref="$1"
  local project_root="$2"
  local enable_units="${3:-false}"
  local -n cfg="$cfg_ref"

  log_info "Starting services..."

  if [[ "${cfg[use_quadlet]:-false}" == "true" ]]; then
    local unit="pf-main-pod.service"
    if [[ "${cfg[gpu_support]:-false}" == "true" ]]; then
      unit="pf-main-pod-gpu.service"
    fi
    systemctl --user start "$unit"
    if [[ "$enable_units" == "true" ]]; then
      systemctl --user enable "$unit" >/dev/null 2>&1 || true
    fi
  else
    cd "$project_root" || return 1
    if [[ "${cfg[gpu_support]:-false}" == "true" ]]; then
      podman-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
    else
      podman-compose up -d
    fi
  fi

  log_success "Services started"
  return 0
}

pf_dev_services_stop() {
  local cfg_ref="$1"
  local project_root="$2"
  local -n cfg="$cfg_ref"

  log_info "Stopping pf Development Environment..."

  if [[ "${cfg[use_quadlet]:-false}" == "true" ]]; then
    local unit="pf-main-pod.service"
    if [[ "${cfg[gpu_support]:-false}" == "true" ]]; then
      unit="pf-main-pod-gpu.service"
    fi
    systemctl --user stop "$unit"
    log_success "Services stopped via Quadlet"
  else
    cd "$project_root" || return 1
    podman-compose down
    log_success "Services stopped via Podman Compose"
  fi
}

pf_dev_services_restart() {
  local cfg_ref="$1"
  local project_root="$2"
  pf_dev_services_stop "$cfg_ref" "$project_root" || return 1
  sleep 2
  pf_dev_services_start "$cfg_ref" "$project_root" || return 1
}

pf_dev_deployment_test() {
  log_info "Testing deployment..."

  sleep 10

  if command_exists curl && curl -f http://localhost:8080/api/health &>/dev/null; then
    log_success "Web service is responding"
  else
    log_error "Web service is not responding"
    return 1
  fi

  if podman exec pf-build-service rustc --version &>/dev/null; then
    log_success "Build service is working"
  else
    log_error "Build service is not working"
    return 1
  fi

  if podman exec pf-dev-service pf --version &>/dev/null; then
    log_success "Development service is working"
  else
    log_error "Development service is not working"
    return 1
  fi

  log_success "All services are working correctly"
  return 0
}

pf_dev_status_show() {
  local cfg_ref="$1"
  local project_root="$2"
  local -n cfg="$cfg_ref"

  log_info "Checking pf Development Environment status..."

  echo ""
  echo "Deployment Type: $([ "${cfg[use_quadlet]:-false}" = "true" ] && echo "Quadlet" || echo "Podman Compose")"
  echo "GPU Support: $([ "${cfg[gpu_support]:-false}" = "true" ] && echo "Enabled" || echo "Disabled")"
  echo ""

  if [[ "${cfg[use_quadlet]:-false}" == "true" ]]; then
    local unit="pf-main-pod.service"
    if [[ "${cfg[gpu_support]:-false}" == "true" ]]; then
      unit="pf-main-pod-gpu.service"
    fi
    echo "Pod Status:"
    systemctl --user status "$unit" --no-pager -l
    echo ""
    echo "Container Services:"
    systemctl --user list-units 'pf-*-service.service' --no-pager
  else
    cd "$project_root" || return 1
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

pf_dev_logs_show() {
  local cfg_ref="$1"
  local project_root="$2"
  local service="${3:-all}"
  local -n cfg="$cfg_ref"

  if [[ "${cfg[use_quadlet]:-false}" == "true" ]]; then
    case "$service" in
      all)
        local unit="pf-main-pod.service"
        if [[ "${cfg[gpu_support]:-false}" == "true" ]]; then
          unit="pf-main-pod-gpu.service"
        fi
        journalctl --user -u "$unit" -f
        ;;
      web) journalctl --user -u pf-web-service.service -f ;;
      build) journalctl --user -u pf-build-service.service -f ;;
      security) journalctl --user -u pf-security-service.service -f ;;
      dev) journalctl --user -u pf-dev-service.service -f ;;
      *) die "Unknown service: $service" ;;
    esac
  else
    cd "$project_root" || return 1
    if [[ "$service" == "all" ]]; then
      podman-compose logs -f
    else
      podman-compose logs -f "$service-service"
    fi
  fi
}

pf_dev_exec_container() {
  local container="${1:-}"
  shift || true
  if [[ -z "$container" ]]; then
    die "exec requires a container name (web|build|security|dev)"
  fi
  if [[ $# -eq 0 ]]; then
    set -- bash
  fi
  case "$container" in
    web) podman exec -it pf-web-service "$@" ;;
    build) podman exec -it pf-build-service "$@" ;;
    security) podman exec -it pf-security-service "$@" ;;
    dev) podman exec -it pf-dev-service "$@" ;;
    *) die "Unknown container: $container" ;;
  esac
}

pf_dev_run_pf_command() {
  log_info "Running pf command: $*"
  podman exec -it pf-dev-service pf "$@"
}

pf_dev_build_wasm() {
  local language="${1:-all}"

  case "$language" in
    all) podman exec pf-build-service ./entrypoint.sh build-all ;;
    rust) podman exec pf-build-service ./entrypoint.sh build-rust ;;
    c) podman exec pf-build-service ./entrypoint.sh build-c ;;
    wat) podman exec pf-build-service ./entrypoint.sh build-wat ;;
    fortran) podman exec pf-build-service ./entrypoint.sh build-fortran ;;
    *) die "Unknown language: $language" ;;
  esac
  log_success "Build completed"
}

pf_dev_cleanup_env() {
  local cfg_ref="$1"
  local project_root="$2"

  log_info "Cleaning up pf Development Environment..."

  pf_dev_services_stop "$cfg_ref" "$project_root" 2>/dev/null || true

  podman rm -f pf-web-service pf-build-service pf-security-service pf-dev-service 2>/dev/null || true
  podman pod rm -f pf-main-pod pf-main-pod-gpu 2>/dev/null || true

  local reply=""
  read -r -p "Remove container images? (y/N): " -n 1 reply || true
  echo
  if [[ "${reply:-}" =~ ^[Yy]$ ]]; then
    podman rmi -f localhost/pf-web-services:latest \
      localhost/pf-build-environment:latest \
      localhost/pf-security-tools:latest \
      localhost/pf-development:latest \
      localhost/pf-base:latest 2>/dev/null || true
  fi

  local reply2=""
  read -r -p "Remove persistent volumes? (y/N): " -n 1 reply2 || true
  echo
  if [[ "${reply2:-}" =~ ^[Yy]$ ]]; then
    podman volume rm -f pf-workspace pf-builds pf-cache 2>/dev/null || true
  fi

  log_success "Cleanup completed"
}

