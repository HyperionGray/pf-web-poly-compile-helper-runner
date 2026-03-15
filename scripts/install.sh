#!/usr/bin/env bash
# install.sh - Cohesive installer for pf-runner (package-first with container and native fallback)
# Usage: ./install.sh [--prefix PATH] [--skip-deps] [--verify-only] [--help]

set -euo pipefail

# Configuration
DEFAULT_PREFIX_NATIVE="/usr/local"
DEFAULT_PREFIX_USER="${HOME:-/usr/local}/.local"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PF_RUNNER_DIR="${SCRIPT_DIR}/pf-runner"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
PREFIX=""
PREFIX_SET=false
SKIP_DEPS=false
SHOW_HELP=false
VERIFY_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --prefix)
            PREFIX="$2"
            PREFIX_SET=true
            shift 2
            ;;
        --prefix=*)
            PREFIX="${1#*=}"
            PREFIX_SET=true
            shift
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}" >&2
            SHOW_HELP=true
            shift
            ;;
    esac
done

# Help function
show_help() {
    cat << EOF
pf-runner Installation Script (Native-only)

USAGE:
    ./install.sh [OPTIONS]

OPTIONS:
    --prefix PATH     Install prefix (default: ${DEFAULT_PREFIX_NATIVE} when run as root, ${DEFAULT_PREFIX_USER} otherwise)
    --skip-deps       Skip installing system dependencies (assumes they are already present)
    --verify-only     Verify an existing installation without installing/updating files
    --help, -h        Show this help message

EXAMPLES:
    # User install (no sudo)
    ./install.sh --prefix ~/.local

    # System install (requires sudo)
    sudo ./install.sh

    # Skip dependency installation (when dependencies already satisfied)
    ./install.sh --skip-deps

    # Verify an existing installation without reinstalling
    ./install.sh --verify-only

    # Verify a specific prefix
    ./install.sh --prefix ~/.local --verify-only

WHAT THIS SCRIPT DOES:
    1. Checks prerequisites (Python 3.10+, Git, pip)
    2. Installs system dependencies (unless --skip-deps)
    3. Creates a Python virtual environment for user installs
    4. Installs Python dependencies (fabric, lark, typer)
    5. Installs pf-runner and wrapper script
    6. Sets up shell completions and validates the install

EOF
}

if [[ "$SHOW_HELP" == true ]]; then
    show_help
    exit 0
fi

# Utility functions
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

normalize_settings() {
    if [[ "$PREFIX_SET" == false ]]; then
        if [[ $EUID -eq 0 ]]; then
            PREFIX="$DEFAULT_PREFIX_NATIVE"
        else
            PREFIX="$DEFAULT_PREFIX_USER"
        fi
    fi
}

resolve_verify_prefix() {
    # If caller provided an explicit prefix, keep it.
    if [[ "$PREFIX_SET" == true ]]; then
        return 0
    fi

    # Prefer whichever existing installation is actually present.
    local candidates=()
    if [[ -n "${HOME:-}" ]]; then
        candidates+=("${HOME}/.local")
    fi
    candidates+=("/usr/local" "/usr")

    local candidate
    for candidate in "${candidates[@]}"; do
        if [[ -x "${candidate}/bin/pf" ]]; then
            PREFIX="$candidate"
            return 0
        fi
    done
}

# Check if running as root when needed
check_permissions() {
    if [[ "$PREFIX" == "/usr/local" ]] || [[ "$PREFIX" == "/usr"* ]]; then
        if [[ $EUID -ne 0 ]]; then
            log_error "Installation to ${PREFIX} requires root privileges."
            log_info "Try: sudo ./install.sh --prefix ${PREFIX}"
            log_info "Or use a user installation: ./install.sh --prefix ~/.local"
            exit 1
        fi
    fi
}

# Detect operating system
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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python 3
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python 3 is required but not installed."
        log_info "Please install Python 3 and try again."
        exit 1
    fi
    
    # Check Python version
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
        log_error "Python 3.10 or higher is required. Found: $python_version"
        exit 1
    fi
    
    # Check Git
    if ! command -v git >/dev/null 2>&1; then
        log_error "Git is required but not installed."
        log_info "Please install Git and try again."
        exit 1
    fi
    
    # Check pip
    if ! python3 -m pip --version >/dev/null 2>&1; then
        log_error "pip is required but not available."
        log_info "Please install python3-pip and try again."
        exit 1
    fi
    
    log_success "Prerequisites check passed (Python $python_version, Git, pip)"
}

# Install system dependencies
install_system_deps() {
    if [[ "$SKIP_DEPS" == true ]]; then
        log_info "Skipping system dependency installation (--skip-deps)"
        return 0
    fi
    
    local os_type
    os_type=$(detect_os)
    
    log_info "Installing system dependencies for $os_type..."
    
    case "$os_type" in
        debian)
            apt-get update
            apt-get install -y python3-dev python3-pip python3-venv build-essential curl git
            ;;
        rhel)
            if command -v dnf >/dev/null 2>&1; then
                dnf install -y python3-devel python3-pip gcc gcc-c++ make curl git
            else
                yum install -y python3-devel python3-pip gcc gcc-c++ make curl git
            fi
            ;;
        arch)
            pacman -Sy --noconfirm python python-pip base-devel curl git
            ;;
        macos)
            if command -v brew >/dev/null 2>&1; then
                brew install python3 git
            else
                log_warning "Homebrew not found. Please install dependencies manually."
            fi
            ;;
        *)
            log_warning "Unknown OS. Please install Python 3, pip, and build tools manually."
            ;;
    esac
    
    log_success "System dependencies installed"
}

# Setup Python environment and dependencies
setup_python_env() {
    log_info "Setting up Python environment..."
    
    # Create virtual environment if needed for user installation
    if [[ "$PREFIX" != "/usr/local" ]] && [[ "$PREFIX" != "/usr"* ]]; then
        local venv_dir="${PREFIX}/lib/pf-runner-venv"
        if [[ ! -d "$venv_dir" ]]; then
            log_info "Creating virtual environment at $venv_dir"
            mkdir -p "$(dirname "$venv_dir")"
            python3 -m venv "$venv_dir"
        fi
        
        # Use virtual environment python
        export PATH="${venv_dir}/bin:$PATH"
        PYTHON_CMD="${venv_dir}/bin/python"
        PIP_CMD="${venv_dir}/bin/pip"
    else
        # System installation - use system python
        PYTHON_CMD="python3"
        PIP_CMD="python3 -m pip"
    fi
    
    # Upgrade pip
    log_info "Upgrading pip..."
    $PIP_CMD install --upgrade pip
    
    # Install Python dependencies
    log_info "Installing Python dependencies..."
    $PIP_CMD install "lark>=1.1.0" "fabric>=3.2,<4" "typer>=0.12"
    
    log_success "Python environment setup complete"
}

# Install pf-runner
install_pf_runner() {
    log_info "Installing pf-runner..."
    
    # Create directories
    local lib_dir="${PREFIX}/lib/pf-runner"
    local bin_dir="${PREFIX}/bin"
    
    mkdir -p "$lib_dir" "$bin_dir"
    
    # Copy pf-runner files
    log_info "Copying pf-runner files to $lib_dir"
    cp -r "${PF_RUNNER_DIR}"/* "$lib_dir/"
    
    # Update shebang in main script
    if [[ "$PREFIX" != "/usr/local" ]] && [[ "$PREFIX" != "/usr"* ]]; then
        # User installation - use virtual environment python
        local venv_python="${PREFIX}/lib/pf-runner-venv/bin/python"
        sed -i "1s|^.*$|#!${venv_python}|" "${lib_dir}/pf_main.py"
    else
        # System installation - use system python
        sed -i "1s|^.*$|#!/usr/bin/env python3|" "${lib_dir}/pf_main.py"
    fi
    
    # Make executable
    chmod +x "${lib_dir}/pf_main.py"
    
    # Create pf executable
    cat > "${bin_dir}/pf" << EOF
#!/usr/bin/env bash
# pf - Wrapper script for pf-runner
exec "${lib_dir}/pf_main.py" "\$@"
EOF
    chmod +x "${bin_dir}/pf"
    
    # Create symlink for local development
    if [[ -d "$lib_dir" ]]; then
        ln -sfn pf_main.py "${lib_dir}/pf"
    fi
    
    log_success "pf-runner installed to $lib_dir"
    log_success "pf executable created at ${bin_dir}/pf"
}

# Install shell completions
install_completions() {
    log_info "Installing shell completions..."
    
    local completions_dir="${PF_RUNNER_DIR}/completions"
    if [[ ! -d "$completions_dir" ]]; then
        log_warning "Completions directory not found, skipping"
        return 0
    fi
    
    # Install bash completion
    local bash_completion_installed=false
    if [[ -d "/etc/bash_completion.d" ]] && [[ "$PREFIX" == "/usr/local" || "$PREFIX" == "/usr"* ]]; then
        cp "${completions_dir}/pf-completion.bash" "/etc/bash_completion.d/pf"
        log_success "Installed bash completion to /etc/bash_completion.d/pf"
        bash_completion_installed=true
    elif [[ -d "${HOME}/.local/share/bash-completion/completions" ]]; then
        mkdir -p "${HOME}/.local/share/bash-completion/completions"
        cp "${completions_dir}/pf-completion.bash" "${HOME}/.local/share/bash-completion/completions/pf"
        log_success "Installed bash completion to ~/.local/share/bash-completion/completions/pf"
        bash_completion_installed=true
    fi
    
    # Install zsh completion
    local zsh_completion_installed=false
    if [[ -d "/usr/local/share/zsh/site-functions" ]] && [[ "$PREFIX" == "/usr/local" || "$PREFIX" == "/usr"* ]]; then
        cp "${completions_dir}/_pf" "/usr/local/share/zsh/site-functions/_pf"
        log_success "Installed zsh completion to /usr/local/share/zsh/site-functions/_pf"
        zsh_completion_installed=true
    elif [[ -d "${HOME}/.zsh/completions" ]] || mkdir -p "${HOME}/.zsh/completions" 2>/dev/null; then
        cp "${completions_dir}/_pf" "${HOME}/.zsh/completions/_pf"
        log_success "Installed zsh completion to ~/.zsh/completions/_pf"
        log_info "Add 'fpath=(~/.zsh/completions \$fpath)' to your ~/.zshrc if not already present"
        zsh_completion_installed=true
    fi
    
    if [[ "$bash_completion_installed" == false ]] && [[ "$zsh_completion_installed" == false ]]; then
        log_warning "Could not install shell completions (no suitable directories found)"
    fi
}

# Validate native installation
validate_native_installation() {
    log_info "Validating native installation..."
    
    local pf_cmd="${PREFIX}/bin/pf"
    
    # Check if pf command exists and is executable
    if [[ ! -x "$pf_cmd" ]]; then
        log_error "pf command not found or not executable at $pf_cmd"
        return 1
    fi
    
    # Test basic pf functionality (run from /tmp to avoid parsing issues with local Pfyfiles)
    log_info "Testing pf list..."
    local list_output
    list_output=$("$pf_cmd" list 2>&1)
    if [[ ! "$list_output" =~ "Available tasks" ]]; then
        log_error "pf list failed: $list_output"
        return 1
    fi
    
    log_success "Basic pf functionality validated"
    log_success "Native installation validation passed"
    return 0
}

# Update PATH information
update_path_info() {
    local bin_dir="${PREFIX}/bin"
    
    # Check if bin directory is in PATH
    if [[ ":$PATH:" != *":${bin_dir}:"* ]]; then
        log_warning "The installation directory ${bin_dir} is not in your PATH"
        log_info "Add the following to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
        echo ""
        echo "    export PATH=\"${bin_dir}:\$PATH\""
        echo ""
        log_info "Or run: echo 'export PATH=\"${bin_dir}:\$PATH\"' >> ~/.bashrc"
        log_info "Then restart your shell or run: source ~/.bashrc"
    else
        log_success "Installation directory is already in PATH"
    fi
}

run_verify_only() {
    log_info "Running verification-only mode (no files will be modified)..."
    resolve_verify_prefix
    log_info "Verifying installation at prefix: ${PREFIX}"

    if validate_native_installation; then
        echo ""
        log_success "✅ Installation verification passed"
        update_path_info
        echo ""
        log_info "Next steps:"
        echo "  1. Try: ${PREFIX}/bin/pf --version"
        echo "  2. Try: ${PREFIX}/bin/pf list"
        return 0
    fi

    log_error "Installation verification failed for prefix: ${PREFIX}"
    log_info "If pf is installed elsewhere, rerun with: ./install.sh --prefix <path> --verify-only"
    return 1
}

# Main installation function
main() {
    echo -e "${BLUE}pf-runner Installation Script${NC}"
    echo "=============================="
    echo ""
    
    # Check if we're in the right directory
    if [[ ! -d "$PF_RUNNER_DIR" ]]; then
        log_error "pf-runner directory not found at $PF_RUNNER_DIR"
        log_info "Please run this script from the repository root directory"
        exit 1
    fi
    
    normalize_settings

    if [[ "$VERIFY_ONLY" == true ]]; then
        if run_verify_only; then
            exit 0
        else
            exit 1
        fi
    fi

    # Check permissions
    check_permissions

    # Native installation steps
    check_prerequisites

    if [[ "$SKIP_DEPS" == false ]]; then
        install_system_deps
    fi

    setup_python_env
    install_pf_runner
    install_completions

    # Validate installation
    if validate_native_installation; then
        echo ""
        log_success "🎉 pf-runner native installation completed successfully!"
        echo ""
        log_info "Installation summary:"
        echo "  • pf-runner library: ${PREFIX}/lib/pf-runner"
        echo "  • pf executable: ${PREFIX}/bin/pf"
        echo "  • Python dependencies: lark, decorator, invoke, paramiko, deprecated"
        echo ""

        update_path_info

        echo ""
        log_info "Next steps:"
        echo "  1. Restart your shell or run: source ~/.bashrc"
        echo "  2. Try: pf --version"
        echo "  3. Try: pf list"
        echo "  4. Read the documentation: cat docs/README.md"
        echo ""
        log_success "Happy task running! 🚀"
    else
        log_error "Native installation validation failed"
        exit 1
    fi
}

# Run main function
main "$@"
