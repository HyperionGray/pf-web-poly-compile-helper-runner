#!/usr/bin/env bash
# install-quadlets.sh - Install Podman Quadlet files for systemd integration
#
# Quadlets allow running containers as systemd services without complex
# service files. They are processed by systemd-generator and converted
# to proper unit files automatically.
#
# Usage:
#   ./containers/scripts/install-quadlets.sh           # Install for current user
#   sudo ./containers/scripts/install-quadlets.sh      # Install system-wide
#   ./containers/scripts/install-quadlets.sh --remove  # Remove installed quadlets

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
QUADLET_SRC="${PROJECT_ROOT}/containers/quadlets"

# Determine quadlet destination based on privileges
if [[ $EUID -eq 0 ]]; then
    # System-wide installation
    QUADLET_DEST="/etc/containers/systemd"
    SYSTEMCTL_CMD="systemctl"
else
    # User installation
    QUADLET_DEST="${HOME}/.config/containers/systemd"
    SYSTEMCTL_CMD="systemctl --user"
fi

show_help() {
    cat <<EOF
Install Podman Quadlet Files
============================

Quadlets are a Podman feature that allows running containers as systemd
services without writing complex service files.

USAGE:
    ./containers/scripts/install-quadlets.sh [OPTIONS]

OPTIONS:
    --install     Install quadlet files (default)
    --remove      Remove installed quadlet files
    --list        List installed quadlet files
    --status      Show status of quadlet services
    --help        Show this help message

INSTALLATION:
    - Run as normal user: Installs to ~/.config/containers/systemd/
    - Run as root: Installs to /etc/containers/systemd/

AFTER INSTALLATION:
    # Reload systemd to process new quadlets
    systemctl --user daemon-reload
    
    # Start the API server
    systemctl --user start pf-api-server
    
    # Start all services in a pod
    systemctl --user start pf-web-api-pod

REQUIREMENTS:
    - Podman 4.4+ with quadlet support
    - systemd-based Linux distribution

EOF
}

check_podman_quadlet() {
    if ! command -v podman &> /dev/null; then
        log_error "Podman not found. Please install Podman first."
        exit 1
    fi
    
    # Check Podman version for quadlet support (4.4+)
    local version=$(podman --version | grep -oP '\d+\.\d+' | head -1)
    local major=$(echo "$version" | cut -d. -f1)
    local minor=$(echo "$version" | cut -d. -f2)
    
    if [[ "$major" -lt 4 ]] || [[ "$major" -eq 4 && "$minor" -lt 4 ]]; then
        log_warn "Podman version $version may not have full quadlet support (4.4+ recommended)"
    fi
    
    # Check if quadlet generator exists
    local generators=("/usr/lib/systemd/system-generators/podman-system-generator"
                      "/usr/lib/systemd/user-generators/podman-user-generator"
                      "/usr/libexec/podman/quadlet")
    
    local found=false
    for gen in "${generators[@]}"; do
        if [[ -x "$gen" ]]; then
            found=true
            break
        fi
    done
    
    if ! $found; then
        log_warn "Podman quadlet generator not found in expected locations"
        log_warn "Quadlets may not work. Ensure podman-generate-systemd is available."
    fi
}

install_quadlets() {
    log_info "Installing quadlet files to ${QUADLET_DEST}"
    
    # Create destination directory
    mkdir -p "${QUADLET_DEST}"
    
    # Copy quadlet files
    local count=0
    for file in "${QUADLET_SRC}"/*.{container,pod,network,volume,kube,image} 2>/dev/null; do
        if [[ -f "$file" ]]; then
            local basename=$(basename "$file")
            log_info "Installing ${basename}"
            cp "$file" "${QUADLET_DEST}/"
            ((count++))
        fi
    done
    
    if [[ $count -eq 0 ]]; then
        log_warn "No quadlet files found in ${QUADLET_SRC}"
        return 1
    fi
    
    log_success "Installed ${count} quadlet files"
    
    # Reload systemd
    log_info "Reloading systemd daemon..."
    ${SYSTEMCTL_CMD} daemon-reload
    
    log_success "Quadlets installed successfully!"
    log_info ""
    log_info "To start services:"
    log_info "  ${SYSTEMCTL_CMD} start pf-api-server"
    log_info "  ${SYSTEMCTL_CMD} start pf-web-api-pod"
    log_info ""
    log_info "To enable services at boot:"
    log_info "  ${SYSTEMCTL_CMD} enable pf-api-server"
}

remove_quadlets() {
    log_info "Removing quadlet files from ${QUADLET_DEST}"
    
    # Stop any running services first
    local services=("pf-runner" "pf-api-server" "pf-build-rust" "pf-build-c" 
                    "pf-build-fortran" "pf-debugger" "pf-debugger-gpu"
                    "pf-web-api-pod" "pf-web-build-pod" "pf-debugger-pod")
    
    for service in "${services[@]}"; do
        if ${SYSTEMCTL_CMD} is-active --quiet "${service}" 2>/dev/null; then
            log_info "Stopping ${service}..."
            ${SYSTEMCTL_CMD} stop "${service}" 2>/dev/null || true
        fi
    done
    
    # Remove quadlet files
    local count=0
    for file in "${QUADLET_DEST}"/pf-*.{container,pod,network,volume,kube,image} 2>/dev/null; do
        if [[ -f "$file" ]]; then
            local basename=$(basename "$file")
            log_info "Removing ${basename}"
            rm -f "$file"
            ((count++))
        fi
    done
    
    # Reload systemd
    ${SYSTEMCTL_CMD} daemon-reload
    
    log_success "Removed ${count} quadlet files"
}

list_quadlets() {
    log_info "Installed quadlet files in ${QUADLET_DEST}:"
    
    if [[ -d "${QUADLET_DEST}" ]]; then
        ls -la "${QUADLET_DEST}"/pf-*.{container,pod,network,volume,kube,image} 2>/dev/null || \
            log_warn "No pf-* quadlet files found"
    else
        log_warn "Quadlet directory does not exist"
    fi
}

show_status() {
    log_info "Quadlet service status:"
    
    local services=("pf-runner" "pf-api-server" "pf-build-rust" "pf-build-c" 
                    "pf-build-fortran" "pf-debugger" "pf-debugger-gpu"
                    "pf-web-api-pod" "pf-web-build-pod" "pf-debugger-pod")
    
    printf "%-25s %-15s %-15s\n" "SERVICE" "STATUS" "STATE"
    printf "%s\n" "-------------------------------------------------------"
    
    for service in "${services[@]}"; do
        local status=$(${SYSTEMCTL_CMD} is-active "${service}" 2>/dev/null || echo "inactive")
        local enabled=$(${SYSTEMCTL_CMD} is-enabled "${service}" 2>/dev/null || echo "disabled")
        printf "%-25s %-15s %-15s\n" "${service}" "${status}" "${enabled}"
    done
}

# Main script
main() {
    check_podman_quadlet
    
    case "${1:-install}" in
        --install|install)
            install_quadlets
            ;;
        --remove|remove)
            remove_quadlets
            ;;
        --list|list)
            list_quadlets
            ;;
        --status|status)
            show_status
            ;;
        --help|-h|help)
            show_help
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
