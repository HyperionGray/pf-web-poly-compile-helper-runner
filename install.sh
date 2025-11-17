#!/usr/bin/env bash
# install.sh - Single installer script for pf-web-poly-compile-helper-runner
# 
# Usage:
#   ./install.sh           # Interactive mode - prompts for installation type
#   ./install.sh base      # Install base pf runner and dependencies
#   ./install.sh web       # Install web/WASM development tools
#   ./install.sh all       # Install everything
#   ./install.sh --help    # Show this help message

set -euo pipefail

# Color output helpers
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Show help message
show_help() {
    cat << EOF
pf-web-poly-compile-helper-runner Installer
===========================================

A comprehensive installer for the pf task runner and polyglot WebAssembly development environment.

USAGE:
    ./install.sh [OPTION]

OPTIONS:
    base        Install base pf runner, Python dependencies, and core build tools
    web         Install web/WASM development tools (Node.js, Playwright, Rust, Emscripten, etc.)
    all         Install everything (base + web)
    --help      Show this help message

INTERACTIVE MODE:
    Running without options will enter interactive mode where you can choose what to install.

EXAMPLES:
    ./install.sh           # Interactive installation
    ./install.sh base      # Install just the base pf runner
    ./install.sh web       # Install just web development tools
    ./install.sh all       # Install everything

WHAT GETS INSTALLED:

Base Installation:
  - Python 3 and pip
  - Fabric library (Python task runner)
  - pf runner (CLI tool)
  - Core build tools (gcc, make, git)
  - Shell completions

Web Installation:
  - Node.js and npm
  - Playwright (browser testing)
  - Rust toolchain with wasm-pack
  - Emscripten (C/C++ to WASM)
  - WABT (WebAssembly Binary Toolkit)
  - LFortran (optional, Fortran to WASM)

REQUIREMENTS:
  - Linux (Ubuntu/Debian) or macOS
  - sudo access for system package installation
  - Internet connection

AFTER INSTALLATION:
  - Verify: pf --version
  - List tasks: pf list
  - Get started: See README.md for usage examples

EOF
}

# Check system prerequisites
check_prerequisites() {
    log_info "Checking system prerequisites..."
    
    # Check for bash version
    if [ "${BASH_VERSINFO:-0}" -lt 4 ]; then
        log_warn "Bash 4.0+ recommended, but will attempt to continue"
    fi
    
    # Check for required commands
    local missing_commands=()
    
    if ! command_exists python3; then
        missing_commands+=("python3")
    fi
    
    if ! command_exists git; then
        missing_commands+=("git")
    fi
    
    if [ ${#missing_commands[@]} -gt 0 ]; then
        log_error "Missing required commands: ${missing_commands[*]}"
        log_info "Installing base system packages..."
        install_base_system_packages
    fi
    
    log_success "Prerequisites check passed"
}

# Install base system packages (git, python3, build-essential)
install_base_system_packages() {
    log_info "Installing base system packages..."
    
    if command_exists apt-get; then
        sudo apt-get update -qq
        sudo apt-get install -y -qq git python3 python3-pip python3-dev build-essential curl wget
    elif command_exists brew; then
        brew install git python3
    else
        log_error "Unsupported package manager. Please install git and python3 manually."
        exit 1
    fi
    
    log_success "Base system packages installed"
}

# Install Python Fabric dependency
install_fabric() {
    log_info "Installing Python Fabric library..."
    
    if ! python3 -m pip --version >/dev/null 2>&1; then
        log_error "pip is not available. Please install python3-pip"
        exit 1
    fi
    
    # Install fabric for the current user
    python3 -m pip install --user "fabric>=3.2,<4" --upgrade
    
    log_success "Fabric installed successfully"
}

# Install pf runner
install_pf_runner() {
    log_info "Installing pf runner..."
    
    cd pf-runner
    
    # Update shebang to use system python3
    if [ -f "pf_parser.py" ]; then
        # Create a wrapper that uses system python3
        sed -i '1s|.*|#!/usr/bin/env python3|' pf_parser.py
        chmod +x pf_parser.py
    fi
    
    # Create local symlink
    ln -sf pf_parser.py pf
    
    # Install to ~/.local/bin
    mkdir -p "$HOME/.local/bin"
    ln -sf "$(pwd)/pf_parser.py" "$HOME/.local/bin/pf"
    
    # Ensure ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        log_warn "Adding ~/.local/bin to PATH in your shell configuration"
        
        # Detect shell and add to appropriate rc file
        if [ -n "${BASH_VERSION:-}" ]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
            log_info "Added to ~/.bashrc - restart your shell or run: source ~/.bashrc"
        elif [ -n "${ZSH_VERSION:-}" ]; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
            log_info "Added to ~/.zshrc - restart your shell or run: source ~/.zshrc"
        fi
        
        # Add to current session
        export PATH="$HOME/.local/bin:$PATH"
    fi
    
    cd ..
    
    log_success "pf runner installed to ~/.local/bin/pf"
}

# Install shell completions
install_completions() {
    log_info "Installing shell completions..."
    
    cd pf-runner
    
    # Install bash completion
    if [ -d "$HOME/.local/share/bash-completion/completions" ] || mkdir -p "$HOME/.local/share/bash-completion/completions" 2>/dev/null; then
        if [ -f "completions/pf-completion.bash" ]; then
            cp completions/pf-completion.bash "$HOME/.local/share/bash-completion/completions/pf"
            log_success "Bash completion installed"
        fi
    fi
    
    # Install zsh completion
    if [ -n "${ZSH_VERSION:-}" ]; then
        if [ -d "$HOME/.zsh/completions" ] || mkdir -p "$HOME/.zsh/completions" 2>/dev/null; then
            if [ -f "completions/_pf" ]; then
                cp completions/_pf "$HOME/.zsh/completions/_pf"
                log_success "Zsh completion installed"
                log_info "Add 'fpath=(~/.zsh/completions \$fpath)' to ~/.zshrc if not present"
            fi
        fi
    fi
    
    cd ..
}

# Install base components
install_base() {
    log_info "=== Installing Base Components ==="
    
    check_prerequisites
    install_fabric
    install_pf_runner
    install_completions
    
    # Verify installation
    if command_exists pf || [ -x "$HOME/.local/bin/pf" ]; then
        log_success "Base installation complete!"
        log_info "Run 'pf list' to see available tasks"
        log_info "Run 'pf --version' to verify installation"
    else
        log_warn "pf command not immediately available - restart your shell or run: source ~/.bashrc"
    fi
}

# Install web/WASM development tools
install_web() {
    log_info "=== Installing Web/WASM Development Tools ==="
    
    # Node.js
    if ! command_exists node; then
        log_info "Installing Node.js..."
        if command_exists apt-get; then
            curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
            sudo apt-get install -y nodejs
        elif command_exists brew; then
            brew install node
        else
            log_warn "Please install Node.js 18+ manually from https://nodejs.org"
        fi
        log_success "Node.js installed"
    else
        log_info "Node.js already installed ($(node --version))"
    fi
    
    # Install Playwright
    if command_exists npm; then
        log_info "Installing Playwright..."
        npm install --no-save @playwright/test
        npx playwright install --with-deps chromium
        log_success "Playwright installed"
    fi
    
    # Rust and wasm-pack
    if ! command_exists rustc; then
        log_info "Installing Rust toolchain..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
        source "$HOME/.cargo/env" 2>/dev/null || true
        log_success "Rust installed"
    else
        log_info "Rust already installed ($(rustc --version))"
    fi
    
    if ! command_exists wasm-pack; then
        log_info "Installing wasm-pack..."
        if command_exists cargo; then
            cargo install wasm-pack
            log_success "wasm-pack installed"
        else
            log_warn "Cargo not available - please install wasm-pack manually"
        fi
    else
        log_info "wasm-pack already installed"
    fi
    
    # WABT (WebAssembly Binary Toolkit)
    if ! command_exists wat2wasm; then
        log_info "Installing WABT..."
        if command_exists apt-get; then
            sudo apt-get install -y wabt
            log_success "WABT installed"
        elif command_exists brew; then
            brew install wabt
            log_success "WABT installed"
        else
            log_warn "Please install WABT manually"
        fi
    else
        log_info "WABT already installed"
    fi
    
    # Emscripten (optional - complex installation)
    if ! command_exists emcc; then
        log_warn "Emscripten not found - this is optional but needed for C/C++ to WASM"
        log_info "To install Emscripten:"
        log_info "  git clone https://github.com/emscripten-core/emsdk.git"
        log_info "  cd emsdk && ./emsdk install latest && ./emsdk activate latest"
        log_info "  source ./emsdk_env.sh"
    else
        log_info "Emscripten already installed"
    fi
    
    log_success "Web/WASM development tools installation complete!"
}

# Install everything
install_all() {
    log_info "=== Full Installation ==="
    install_base
    echo ""
    install_web
    echo ""
    log_success "Complete installation finished!"
}

# Interactive installation
interactive_install() {
    cat << EOF

${BLUE}╔════════════════════════════════════════════════════════╗
║     pf-web-poly-compile-helper-runner Installer       ║
╚════════════════════════════════════════════════════════╝${NC}

This installer will help you set up the pf task runner and 
optionally install web development tools.

What would you like to install?

  ${GREEN}1)${NC} Base only    - pf runner and core dependencies
  ${GREEN}2)${NC} Web only     - Web/WASM development tools
  ${GREEN}3)${NC} Everything   - Base + Web (recommended)
  ${GREEN}4)${NC} Exit

EOF

    read -p "Enter your choice [1-4]: " choice
    
    case $choice in
        1)
            echo ""
            install_base
            ;;
        2)
            echo ""
            log_warn "Installing web tools only - you may need base installation too"
            install_web
            ;;
        3)
            echo ""
            install_all
            ;;
        4)
            log_info "Installation cancelled"
            exit 0
            ;;
        *)
            log_error "Invalid choice. Please run the installer again."
            exit 1
            ;;
    esac
}

# Post-installation instructions
show_next_steps() {
    cat << EOF

${GREEN}╔════════════════════════════════════════════════════════╗
║              Installation Complete! 🎉                 ║
╚════════════════════════════════════════════════════════╝${NC}

${BLUE}Next Steps:${NC}

1. Restart your shell or run:
   ${YELLOW}source ~/.bashrc${NC}  (or ~/.zshrc for zsh)

2. Verify installation:
   ${YELLOW}pf --version${NC}

3. List available tasks:
   ${YELLOW}pf list${NC}

4. Build the demo WebAssembly modules:
   ${YELLOW}pf web-build-all${NC}

5. Start the development server:
   ${YELLOW}pf web-dev${NC}

6. Run tests:
   ${YELLOW}pf web-test${NC}

${BLUE}Documentation:${NC}
  - Main README: README.md
  - pf runner docs: pf-runner/README.md
  - Build helpers: pf-runner/BUILD-HELPERS.md

${BLUE}Need Help?${NC}
  - Run: ${YELLOW}pf --help${NC}
  - File issues on GitHub
  - Check documentation in pf-runner/ directory

Happy coding! 🚀

EOF
}

# Main installation logic
main() {
    # Change to repository root
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR"
    
    log_info "Starting pf-web-poly-compile-helper-runner installer"
    log_info "Installation directory: $SCRIPT_DIR"
    
    # Parse command line arguments
    case "${1:-interactive}" in
        --help|-h|help)
            show_help
            exit 0
            ;;
        base)
            install_base
            show_next_steps
            ;;
        web)
            install_web
            show_next_steps
            ;;
        all)
            install_all
            show_next_steps
            ;;
        interactive)
            interactive_install
            show_next_steps
            ;;
        *)
            log_error "Unknown option: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
