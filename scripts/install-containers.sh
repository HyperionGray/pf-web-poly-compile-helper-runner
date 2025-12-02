#!/bin/bash
set -e

# pf Development Environment Container Installation Script
# This script sets up the containerized pf development environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_MODE="${1:-interactive}"
GPU_SUPPORT="${GPU_SUPPORT:-false}"
USE_QUADLET="${USE_QUADLET:-true}"

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

check_requirements() {
    log_info "Checking system requirements..."
    
    # Check for Podman
    if ! command -v podman &> /dev/null; then
        log_error "Podman is not installed. Please install Podman first."
        echo "Ubuntu/Debian: sudo apt-get install podman"
        echo "Fedora: sudo dnf install podman"
        echo "Arch: sudo pacman -S podman"
        exit 1
    fi
    
    # Check for podman-compose
    if ! command -v podman-compose &> /dev/null; then
        log_warning "podman-compose not found. Installing via pip..."
        pip3 install --user podman-compose
    fi
    
    # Check systemd user directory for Quadlet
    if [ "$USE_QUADLET" = "true" ]; then
        mkdir -p ~/.config/containers/systemd
    fi
    
    # Check for GPU support
    if [ "$GPU_SUPPORT" = "true" ]; then
        if ! command -v nvidia-smi &> /dev/null; then
            log_warning "nvidia-smi not found. GPU support may not work."
        fi
        
        if ! command -v nvidia-container-toolkit &> /dev/null; then
            log_warning "NVIDIA Container Toolkit not found. Installing..."
            install_nvidia_container_toolkit
        fi
    fi
    
    log_success "Requirements check completed"
}

install_nvidia_container_toolkit() {
    log_info "Installing NVIDIA Container Toolkit..."
    
    # Add NVIDIA repository
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    
    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    
    # Configure Podman for GPU support
    sudo nvidia-ctk cdi generate --output=/etc/cdi/nvidia.yaml
    
    log_success "NVIDIA Container Toolkit installed"
}

build_images() {
    log_info "Building container images..."
    
    cd "$PROJECT_ROOT"
    
    # Build base image first
    log_info "Building base image..."
    podman build -t localhost/pf-base:latest -f containers/base/Dockerfile .
    
    # Build service images
    log_info "Building web services image..."
    podman build -t localhost/pf-web-services:latest -f containers/web-services/Dockerfile .
    
    log_info "Building build environment image..."
    podman build -t localhost/pf-build-environment:latest -f containers/build-environment/Dockerfile .
    
    log_info "Building security tools image..."
    podman build -t localhost/pf-security-tools:latest -f containers/security-tools/Dockerfile .
    
    log_info "Building development environment image..."
    podman build -t localhost/pf-development:latest -f containers/development/Dockerfile .
    
    log_success "All images built successfully"
}

setup_quadlet() {
    if [ "$USE_QUADLET" != "true" ]; then
        return
    fi
    
    log_info "Setting up Quadlet configuration..."
    
    # Copy Quadlet files
    cp "$PROJECT_ROOT"/quadlet/*.{pod,container,network,volume} ~/.config/containers/systemd/ 2>/dev/null || true
    
    # Reload systemd
    systemctl --user daemon-reload
    
    log_success "Quadlet configuration installed"
}

start_services() {
    log_info "Starting services..."
    
    if [ "$USE_QUADLET" = "true" ]; then
        # Start with Quadlet
        if [ "$GPU_SUPPORT" = "true" ]; then
            systemctl --user start pf-main-pod-gpu.service
        else
            systemctl --user start pf-main-pod.service
        fi
        
        # Enable for auto-start
        if [ "$GPU_SUPPORT" = "true" ]; then
            systemctl --user enable pf-main-pod-gpu.service
        else
            systemctl --user enable pf-main-pod.service
        fi
    else
        # Start with podman-compose
        cd "$PROJECT_ROOT"
        if [ "$GPU_SUPPORT" = "true" ]; then
            podman-compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
        else
            podman-compose up -d
        fi
    fi
    
    log_success "Services started"
}

test_deployment() {
    log_info "Testing deployment..."
    
    # Wait for services to start
    sleep 10
    
    # Test web service
    if curl -f http://localhost:8080/api/health &> /dev/null; then
        log_success "Web service is responding"
    else
        log_error "Web service is not responding"
        return 1
    fi
    
    # Test build service
    if podman exec pf-build-service rustc --version &> /dev/null; then
        log_success "Build service is working"
    else
        log_error "Build service is not working"
        return 1
    fi
    
    # Test development service
    if podman exec pf-dev-service pf --version &> /dev/null; then
        log_success "Development service is working"
    else
        log_error "Development service is not working"
        return 1
    fi
    
    log_success "All services are working correctly"
}

show_usage() {
    cat << EOF
pf Development Environment Container Installation

Usage: $0 [MODE] [OPTIONS]

Modes:
    interactive     Interactive installation (default)
    auto           Automatic installation with defaults
    build-only     Only build images, don't start services
    test           Test existing deployment

Options:
    --gpu          Enable GPU support
    --no-quadlet   Use podman-compose instead of Quadlet
    --help         Show this help message

Environment Variables:
    GPU_SUPPORT    Enable GPU support (true/false)
    USE_QUADLET    Use Quadlet for service management (true/false)

Examples:
    # Interactive installation
    $0 interactive
    
    # Auto install with GPU support
    GPU_SUPPORT=true $0 auto
    
    # Build images only
    $0 build-only
    
    # Install with podman-compose
    USE_QUADLET=false $0 auto
EOF
}

interactive_install() {
    echo "pf Development Environment Container Setup"
    echo "=========================================="
    echo ""
    
    # Ask about GPU support
    read -p "Enable GPU support? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        GPU_SUPPORT=true
    fi
    
    # Ask about Quadlet vs podman-compose
    read -p "Use Quadlet for service management? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        USE_QUADLET=false
    fi
    
    echo ""
    echo "Configuration:"
    echo "- GPU Support: $GPU_SUPPORT"
    echo "- Use Quadlet: $USE_QUADLET"
    echo ""
    
    read -p "Continue with installation? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        exit 0
    fi
}

main() {
    case "$INSTALL_MODE" in
        "interactive")
            interactive_install
            ;;
        "auto")
            log_info "Starting automatic installation..."
            ;;
        "build-only")
            check_requirements
            build_images
            log_success "Images built successfully. Use 'podman images' to see them."
            exit 0
            ;;
        "test")
            test_deployment
            exit 0
            ;;
        "help"|"--help"|"-h")
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown mode: $INSTALL_MODE"
            show_usage
            exit 1
            ;;
    esac
    
    # Parse additional options
    while [[ $# -gt 1 ]]; do
        case $2 in
            --gpu)
                GPU_SUPPORT=true
                shift
                ;;
            --no-quadlet)
                USE_QUADLET=false
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $2"
                show_usage
                exit 1
                ;;
        esac
        shift
    done
    
    # Run installation steps
    check_requirements
    build_images
    setup_quadlet
    start_services
    test_deployment
    
    echo ""
    log_success "pf Development Environment is now running!"
    echo ""
    echo "Access the web interface at: http://localhost:8080"
    echo ""
    echo "Container management:"
    if [ "$USE_QUADLET" = "true" ]; then
        echo "- View status: systemctl --user status pf-main-pod.service"
        echo "- Stop services: systemctl --user stop pf-main-pod.service"
        echo "- Start services: systemctl --user start pf-main-pod.service"
        echo "- View logs: journalctl --user -u pf-main-pod.service -f"
    else
        echo "- View status: podman-compose ps"
        echo "- Stop services: podman-compose down"
        echo "- Start services: podman-compose up -d"
        echo "- View logs: podman-compose logs -f"
    fi
    echo ""
    echo "Container access:"
    echo "- Development: podman exec -it pf-dev-service bash"
    echo "- Build tools: podman exec -it pf-build-service bash"
    echo "- Security tools: podman exec -it pf-security-service bash"
    echo "- Web service: podman exec -it pf-web-service bash"
}

# Handle command line arguments
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi