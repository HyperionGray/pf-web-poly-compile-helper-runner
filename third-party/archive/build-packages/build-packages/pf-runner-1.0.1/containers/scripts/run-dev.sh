#!/usr/bin/env bash
# run-dev.sh - Quick development workflow with containers
#
# Usage:
#   ./containers/scripts/run-dev.sh                    # Start API server
#   ./containers/scripts/run-dev.sh build              # Build all WASM
#   ./containers/scripts/run-dev.sh shell [container]  # Open shell in container
#   ./containers/scripts/run-dev.sh debug              # Start debugger container
#   ./containers/scripts/run-dev.sh gpu                # Start GPU debugger
#   ./containers/scripts/run-dev.sh down               # Stop all containers
#   ./containers/scripts/run-dev.sh logs               # View container logs

set -euo pipefail

# Color output helpers
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# Container runtime
CONTAINER_RT="${CONTAINER_RT:-podman}"
COMPOSE_RT="${COMPOSE_RT:-podman-compose}"

# Fallback to docker-compose if podman-compose not available
if ! command -v "${COMPOSE_RT}" &> /dev/null; then
    if command -v docker-compose &> /dev/null; then
        COMPOSE_RT="docker-compose"
        CONTAINER_RT="docker"
        log_warn "podman-compose not found, using docker-compose"
    else
        log_error "Neither podman-compose nor docker-compose found."
        exit 1
    fi
fi

show_help() {
    cat <<EOF
Development Workflow with Containers
====================================

USAGE:
    ./containers/scripts/run-dev.sh [COMMAND] [OPTIONS]

COMMANDS:
    up, start       Start the API server and required services (default)
    down, stop      Stop all running containers
    build           Build all WASM modules
    build-images    Build all container images
    shell [name]    Open interactive shell in container (default: debugger)
    debug           Start debugging container interactively
    gpu             Start GPU-enabled debugger (requires nvidia-container-toolkit)
    logs [name]     View logs (all or specific container)
    status          Show container status
    clean           Remove all containers and volumes
    help            Show this help

EXAMPLES:
    # Start development server
    ./containers/scripts/run-dev.sh

    # Build all WASM modules
    ./containers/scripts/run-dev.sh build

    # Open shell in debugger container
    ./containers/scripts/run-dev.sh shell debugger

    # View API server logs
    ./containers/scripts/run-dev.sh logs api-server

    # Start GPU debugger
    ./containers/scripts/run-dev.sh gpu

EOF
}

compose_cmd() {
    cd "${PROJECT_ROOT}"
    ${COMPOSE_RT} -f podman-compose.yml "$@"
}

start_services() {
    log_info "Starting development services..."
    compose_cmd up -d api-server pf-runner
    log_success "Services started!"
    log_info "API server available at: http://localhost:8080"
    log_info "API health check: http://localhost:8080/api/health"
}

stop_services() {
    log_info "Stopping all services..."
    compose_cmd down
    log_success "All services stopped"
}

build_wasm() {
    log_info "Building all WASM modules..."
    
    # Run each build container
    compose_cmd run --rm build-rust
    compose_cmd run --rm build-c
    compose_cmd run --rm build-fortran
    compose_cmd run --rm build-wat
    
    log_success "All WASM modules built!"
    log_info "Output available in the pf-wasm-output volume"
}

build_images() {
    log_info "Building all container images..."
    compose_cmd build
    log_success "All images built!"
}

open_shell() {
    local container="${1:-debugger}"
    log_info "Opening shell in ${container}..."
    
    # Check if container is running
    if compose_cmd ps --services --filter "status=running" | grep -q "${container}"; then
        compose_cmd exec "${container}" /bin/bash
    else
        log_info "Container not running, starting it..."
        compose_cmd run --rm -it "${container}" /bin/bash
    fi
}

start_debug() {
    log_info "Starting debugging container..."
    compose_cmd run --rm -it debugger
}

start_gpu_debug() {
    log_info "Starting GPU debugger (requires nvidia-container-toolkit)..."
    compose_cmd --profile gpu run --rm -it debugger-gpu
}

show_logs() {
    local container="${1:-}"
    if [[ -n "$container" ]]; then
        compose_cmd logs -f "${container}"
    else
        compose_cmd logs -f
    fi
}

show_status() {
    log_info "Container status:"
    compose_cmd ps -a
    
    log_info ""
    log_info "Volumes:"
    ${CONTAINER_RT} volume ls | grep pf- || log_info "No pf-* volumes found"
    
    log_info ""
    log_info "Networks:"
    ${CONTAINER_RT} network ls | grep pf- || log_info "No pf-* networks found"
}

clean_all() {
    log_warn "This will remove all containers, volumes, and networks!"
    read -p "Are you sure? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        compose_cmd down -v --remove-orphans
        ${CONTAINER_RT} volume rm $(${CONTAINER_RT} volume ls -q | grep pf-) 2>/dev/null || true
        ${CONTAINER_RT} network rm $(${CONTAINER_RT} network ls -q | grep pf-) 2>/dev/null || true
        log_success "Cleanup complete"
    else
        log_info "Cleanup cancelled"
    fi
}

# Main script
main() {
    case "${1:-up}" in
        up|start)
            start_services
            ;;
        down|stop)
            stop_services
            ;;
        build)
            build_wasm
            ;;
        build-images)
            build_images
            ;;
        shell)
            open_shell "${2:-debugger}"
            ;;
        debug)
            start_debug
            ;;
        gpu)
            start_gpu_debug
            ;;
        logs)
            show_logs "${2:-}"
            ;;
        status)
            show_status
            ;;
        clean)
            clean_all
            ;;
        --help|-h|help)
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
