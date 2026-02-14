#!/bin/bash
set -e

# pf Development Environment Container Management Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
USE_QUADLET="${USE_QUADLET:-true}"
GPU_SUPPORT="${GPU_SUPPORT:-false}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
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
    cat << EOF
pf Development Environment Container Management

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    status              Show deployment status
    start               Start all services
    stop                Stop all services
    restart             Restart all services
    logs [SERVICE]      Show logs (all, web, build, security, dev)
    exec CONTAINER [CMD] Execute command in container
    pf [ARGS]           Run pf command in development container
    build [LANGUAGE]    Build WASM modules (all, rust, c, wat, fortran)
    cleanup             Stop and remove containers/images/volumes
    help                Show this help message

Container Access:
    web                 Web service container
    build               Build environment container
    security            Security tools container
    dev                 Development environment container

Examples:
    # Show status
    $0 status
    
    # Start services
    $0 start
    
    # View web service logs
    $0 logs web
    
    # Access development container
    $0 exec dev
    
    # Run pf command
    $0 pf web-build-all
    
    # Build Rust WASM
    $0 build rust
    
    # Access security tools
    $0 exec security

Environment Variables:
    USE_QUADLET         Use Quadlet instead of podman-compose (true/false)
    GPU_SUPPORT         Enable GPU support (true/false)
EOF
}

main() {
    local command="${1:-status}"
    
    case "$command" in
        "status")
            show_status
            ;;
        "start")
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "logs")
            shift
            show_logs "$@"
            ;;
        "exec")
            shift
            exec_container "$@"
            ;;
        "pf")
            shift
            run_pf_command "$@"
            ;;
        "build")
            shift
            build_wasm "$@"
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Auto-detect deployment type if not set
if [ -z "$USE_QUADLET" ] || [ -z "$GPU_SUPPORT" ]; then
    detect_deployment_type 2>/dev/null || true
fi

# Handle command line arguments
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi