#!/usr/bin/env bash
# One-command installer for pf-runner
# Automatically detects the best installation method and uses it
#
# Usage: curl -sSL https://raw.githubusercontent.com/P4X-ng/pf-web-poly-compile-helper-runner/main/quick-install.sh | bash
#        OR: ./quick-install.sh

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
    echo -e "${RED}[ERROR]${NC} $1" >&2
}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd -P)"

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get >/dev/null 2>&1; then
            echo "debian"
        elif command -v yum >/dev/null 2>&1 || command -v dnf >/dev/null 2>&1; then
            echo "rhel"
        elif command -v pacman >/dev/null 2>&1; then
            echo "arch"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

# Check if we're in the repo
in_repo() {
    [[ -f "${REPO_ROOT}/install.sh" ]] && ([[ -d "${REPO_ROOT}/pf-runner-full" ]] || [[ -d "${REPO_ROOT}/pf-runner" ]])
}

find_repo_deb() {
    local candidates=(
        "${REPO_ROOT}/build-packages/deb/pf-runner_${PF_VERSION}.deb"
        "${REPO_ROOT}/build-packages/deb/pf-runner_latest.deb"
        "${REPO_ROOT}/deb/build/pf-runner_${PF_VERSION}.deb"
    )
    local candidate=""
    for candidate in "${candidates[@]}"; do
        if [[ -f "$candidate" ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
    return 1
}

# Main installation logic
main() {
    log_info "🚀 pf-runner One-Command Installer"
    echo ""
    
    local os_type
    os_type=$(detect_os)
    
    # Version to use (can be overridden by environment variable)
    local PF_VERSION="${PF_VERSION:-1.0.0}"
    
    # If we're in the repo, use the local installer
    if in_repo; then
        log_info "Detected repository - using local installer"
        cd "${REPO_ROOT}"
        
        # Check if we have a .deb package
        local deb_package=""
        deb_package="$(find_repo_deb || true)"
        if [[ "$os_type" == "debian" ]] && [[ -n "$deb_package" ]]; then
            log_info "Found .deb package - installing via dpkg"
            if [[ $EUID -eq 0 ]]; then
                dpkg -i "$deb_package" || true
                apt-get install -f -y
                log_success "Installed pf-runner from .deb package"
            else
                log_warning ".deb installation requires sudo; falling back to user/native install"
                ./install.sh --prefix ~/.local
            fi
        else
            # Use the standard native installer
            log_info "Using standard installer"
            if [[ $EUID -eq 0 ]]; then
                ./install.sh
            else
                ./install.sh --prefix ~/.local
            fi
        fi
    else
        # We're not in the repo, need to clone it first
        log_info "Cloning repository..."
        
        if ! command -v git >/dev/null 2>&1; then
            log_error "Git is required but not installed"
            log_info "Install git and try again"
            exit 1
        fi
        
        local temp_dir
        temp_dir=$(mktemp -d)
        cd "$temp_dir"
        
        git clone https://github.com/P4X-ng/pf-web-poly-compile-helper-runner.git
        cd pf-web-poly-compile-helper-runner
        
        log_info "Repository cloned - running installer"
        
        # Run the installer based on available tools
        log_info "Running native installer"
        if [[ $EUID -eq 0 ]]; then
            ./install.sh
        else
            ./install.sh --prefix ~/.local
        fi
        
        log_info "Cleaning up temporary directory"
        cd /
        rm -rf "$temp_dir"
    fi
    
    echo ""
    log_success "🎉 Installation complete!"
    echo ""
    log_info "Next steps:"
    echo "  1. Restart your shell or run: source ~/.bashrc"
    echo "  2. Try: pf --version"
    echo "  3. Try: pf list"
    echo ""
    log_success "Happy task running! 🚀"
}

main "$@"
