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
    [[ -d "pf-runner" ]] && ([[ -f "install.sh" ]] || [[ -f "scripts/install.sh" ]])
}

resolve_installer_path() {
    if [[ -x "./install.sh" ]]; then
        echo "./install.sh"
        return 0
    fi

    if [[ -x "./scripts/install.sh" ]]; then
        echo "./scripts/install.sh"
        return 0
    fi

    if [[ -f "./install.sh" ]]; then
        echo "./install.sh"
        return 0
    fi

    if [[ -f "./scripts/install.sh" ]]; then
        echo "./scripts/install.sh"
        return 0
    fi

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
        local installer_cmd
        if ! installer_cmd=$(resolve_installer_path); then
            log_error "Could not locate installer entrypoint (install.sh or scripts/install.sh)"
            exit 1
        fi
        
        # Check if we have a .deb package
        if [[ "$os_type" == "debian" ]] && [[ -f "deb/build/pf-runner_${PF_VERSION}.deb" ]]; then
            log_info "Found .deb package - installing via dpkg"
            if [[ $EUID -eq 0 ]]; then
                dpkg -i "deb/build/pf-runner_${PF_VERSION}.deb" || true
                apt-get install -f -y
                log_success "Installed pf-runner from .deb package"
            else
                log_error ".deb installation requires sudo"
                log_info "Run: sudo dpkg -i deb/build/pf-runner_${PF_VERSION}.deb && sudo apt-get install -f"
                exit 1
            fi
        else
            # Use the standard native installer
            log_info "Using standard installer"
            if [[ $EUID -eq 0 ]]; then
                "$installer_cmd"
            else
                "$installer_cmd" --prefix ~/.local
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
        local installer_cmd
        if ! installer_cmd=$(resolve_installer_path); then
            log_error "Could not locate installer entrypoint after clone"
            exit 1
        fi

        if [[ $EUID -eq 0 ]]; then
            "$installer_cmd"
        else
            "$installer_cmd" --prefix ~/.local
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
