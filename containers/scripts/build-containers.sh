#!/usr/bin/env bash
# build-containers.sh - Build all container images for pf-web-poly-compile-helper-runner
#
# Usage:
#   ./containers/scripts/build-containers.sh           # Build all containers
#   ./containers/scripts/build-containers.sh base      # Build only base image
#   ./containers/scripts/build-containers.sh api       # Build API services
#   ./containers/scripts/build-containers.sh build     # Build builder images
#   ./containers/scripts/build-containers.sh debug     # Build debugger images
#   ./containers/scripts/build-containers.sh --help    # Show help

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
DOCKERFILE_DIR="${PROJECT_ROOT}/containers/dockerfiles"

# Container runtime (podman preferred, docker as fallback)
CONTAINER_RT="${CONTAINER_RT:-podman}"
if ! command -v "${CONTAINER_RT}" &> /dev/null; then
    if command -v docker &> /dev/null; then
        CONTAINER_RT="docker"
        log_warn "podman not found, using docker instead"
    else
        log_error "Neither podman nor docker found. Please install one of them."
        exit 1
    fi
fi

show_help() {
    cat <<EOF
Build Container Images for pf-web-poly-compile-helper-runner
============================================================

USAGE:
    ./containers/scripts/build-containers.sh [OPTIONS] [TARGET]

TARGETS:
    all       Build all container images (default)
    base      Build only the base Ubuntu 24.04 image
    api       Build API server and pf-runner images
    build     Build compilation images (Rust, C, Fortran)
    debug     Build debugger images (standard and GPU)

OPTIONS:
    --no-cache    Build without using cache
    --push        Push images to registry after building
    --help        Show this help message

EXAMPLES:
    # Build all images
    ./containers/scripts/build-containers.sh

    # Build only base and API images
    ./containers/scripts/build-containers.sh base api

    # Build without cache
    ./containers/scripts/build-containers.sh --no-cache all

ENVIRONMENT:
    CONTAINER_RT    Container runtime to use (default: podman, fallback: docker)
    REGISTRY        Registry to push to (default: localhost)

EOF
}

build_image() {
    local name="$1"
    local dockerfile="$2"
    local tag="${3:-latest}"
    local extra_args="${4:-}"
    
    local full_tag="localhost/pf-${name}:${tag}"
    
    log_info "Building ${full_tag}..."
    
    if ${CONTAINER_RT} build ${CACHE_ARG:-} ${extra_args} \
        -t "${full_tag}" \
        -f "${DOCKERFILE_DIR}/${dockerfile}" \
        "${PROJECT_ROOT}"; then
        log_success "Built ${full_tag}"
        return 0
    else
        log_error "Failed to build ${full_tag}"
        return 1
    fi
}

build_base() {
    log_info "=== Building Base Image ==="
    build_image "base" "Dockerfile.base"
}

build_api() {
    log_info "=== Building API Images ==="
    build_image "runner" "Dockerfile.pf-runner"
    build_image "api-server" "Dockerfile.api-server"
}

build_builders() {
    log_info "=== Building Compilation Images ==="
    build_image "build-rust" "Dockerfile.build-rust"
    build_image "build-c" "Dockerfile.build-c"
    build_image "build-fortran" "Dockerfile.build-fortran"
}

build_debugger() {
    log_info "=== Building Debugger Images ==="
    build_image "debugger" "Dockerfile.debugger"
    build_image "debugger-gpu" "Dockerfile.debugger-gpu"
}

build_all() {
    build_base
    build_api
    build_builders
    build_debugger
}

# Main script
main() {
    cd "${PROJECT_ROOT}"
    
    # Parse arguments
    CACHE_ARG=""
    PUSH_IMAGES=false
    TARGETS=()
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --no-cache)
                CACHE_ARG="--no-cache"
                shift
                ;;
            --push)
                PUSH_IMAGES=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            all|base|api|build|debug)
                TARGETS+=("$1")
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Default to all if no targets specified
    if [[ ${#TARGETS[@]} -eq 0 ]]; then
        TARGETS=("all")
    fi
    
    log_info "Using container runtime: ${CONTAINER_RT}"
    log_info "Project root: ${PROJECT_ROOT}"
    
    # Build requested targets
    for target in "${TARGETS[@]}"; do
        case "$target" in
            all)
                build_all
                ;;
            base)
                build_base
                ;;
            api)
                build_base
                build_api
                ;;
            build)
                build_base
                build_builders
                ;;
            debug)
                build_base
                build_debugger
                ;;
        esac
    done
    
    log_success "All requested images built successfully!"
    
    # List built images
    log_info "Built images:"
    ${CONTAINER_RT} images | grep "pf-" | head -20
}

main "$@"
