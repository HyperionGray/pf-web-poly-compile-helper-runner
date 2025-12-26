#!/usr/bin/env bash
# install.sh - Cohesive installer for pf-runner (container-first with native option)
# Usage: ./install.sh [--mode container|native] [--runtime podman|docker] [--image NAME] [--prefix PATH] [--skip-deps] [--skip-build] [--no-wrapper] [--help]

set -euo pipefail

# Configuration
DEFAULT_PREFIX_NATIVE="/usr/local"
DEFAULT_PREFIX_CONTAINER="${HOME:-/usr/local}/.local"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PF_RUNNER_DIR="${SCRIPT_DIR}/pf-runner"
BASE_IMAGE_DEFAULT="localhost/pf-base:latest"
RUNNER_IMAGE_DEFAULT="localhost/pf-runner:latest"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
MODE="container"
PREFIX=""
PREFIX_SET=false
SKIP_DEPS=false
SHOW_HELP=false
CONTAINER_RT="podman"
CONTAINER_RT_SET=false
CONTAINER_IMAGE="${RUNNER_IMAGE_DEFAULT}"
SKIP_BUILD=false
NO_WRAPPER=false
BUILD_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --mode=*)
            MODE="${1#*=}"
            shift
            ;;
        --container)
            MODE="container"
            shift
            ;;
        --native|--host)
            MODE="native"
            shift
            ;;
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
        --runtime)
            CONTAINER_RT="$2"
            CONTAINER_RT_SET=true
            MODE="container"
            shift 2
            ;;
        --runtime=*)
            CONTAINER_RT="${1#*=}"
            CONTAINER_RT_SET=true
            MODE="container"
            shift
            ;;
        --image)
            CONTAINER_IMAGE="$2"
            MODE="container"
            shift 2
            ;;
        --image=*)
            CONTAINER_IMAGE="${1#*=}"
            MODE="container"
            shift
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            MODE="container"
            shift
            ;;
        --build-only)
            BUILD_ONLY=true
            NO_WRAPPER=true
            MODE="container"
            shift
            ;;
        --no-wrapper)
            NO_WRAPPER=true
            MODE="container"
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
pf-runner Installation Script (Container-first)

USAGE:
    ./install.sh [OPTIONS]

OPTIONS:
    --mode MODE       Install mode: container (default) or native
    --container       Alias for --mode container
    --native          Alias for --mode native

    --runtime RUNTIME Container runtime (podman|docker). Implies container mode
    --image IMAGE     pf-runner image name:tag (default: ${RUNNER_IMAGE_DEFAULT})
    --skip-build      Skip container image build (assumes images exist)
    --build-only      Build container images only (skip wrapper install)
    --no-wrapper      Skip installing the pf wrapper (container mode)

    --prefix PATH     Install prefix
                     Default: ${DEFAULT_PREFIX_NATIVE} for native,
                              ${DEFAULT_PREFIX_CONTAINER} for container (non-root)
    --skip-deps       Skip system dependency installation (native mode)
    --help, -h        Show this help message

EXAMPLES:
    # Container-first install (user prefix by default)
    ./install.sh --runtime podman

    # Native system-wide install (requires sudo)
    sudo ./install.sh --mode native

    # Native user install
    ./install.sh --mode native --prefix ~/.local

    # Build container images only
    ./install.sh --mode container --build-only

WHAT THIS SCRIPT DOES (container mode):
    1. Builds pf base + pf-runner images (optional)
    2. Installs the pf wrapper script
    3. Sets up shell completions (optional)

WHAT THIS SCRIPT DOES (native mode):
    1. Checks prerequisites (Python 3, Git)
    2. Installs system dependencies (optional)
    3. Sets up Python virtual environment
    4. Installs Python dependencies (fabric, lark)
    5. Installs pf-runner to specified prefix
    6. Sets up shell completions (optional)
    7. Validates installation

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
    if [[ "$MODE" != "container" && "$MODE" != "native" ]]; then
        log_error "Invalid --mode: $MODE (expected 'container' or 'native')"
        exit 1
    fi

    if [[ "$BUILD_ONLY" == true && "$SKIP_BUILD" == true ]]; then
        log_error "--build-only and --skip-build cannot be used together"
        exit 1
    fi

    if [[ "$MODE" == "native" ]]; then
        if [[ "$SKIP_BUILD" == true || "$NO_WRAPPER" == true || "$BUILD_ONLY" == true ]]; then
            log_warning "Container-specific options ignored in native mode"
        fi
    else
        if [[ "$SKIP_DEPS" == true ]]; then
            log_warning "--skip-deps has no effect in container mode"
        fi
    fi

    if [[ "$PREFIX_SET" == false ]]; then
        if [[ "$MODE" == "container" ]]; then
            if [[ $EUID -eq 0 ]]; then
                PREFIX="$DEFAULT_PREFIX_NATIVE"
            else
                PREFIX="$DEFAULT_PREFIX_CONTAINER"
            fi
        else
            PREFIX="$DEFAULT_PREFIX_NATIVE"
        fi
    fi
}

# Check if running as root when needed
check_permissions() {
    if [[ "$PREFIX" == "/usr/local" ]] || [[ "$PREFIX" == "/usr"* ]]; then
        if [[ $EUID -ne 0 ]]; then
            log_error "Installation to ${PREFIX} requires root privileges."
            log_info "Try: sudo ./install.sh --mode ${MODE}"
            log_info "Or use user installation: ./install.sh --mode ${MODE} --prefix ~/.local"
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
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
        log_error "Python 3.8 or higher is required. Found: $python_version"
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
    
    # Install Python dependencies (fabric is bundled locally)
    log_info "Installing Python dependencies..."
    $PIP_CMD install "lark>=1.1.0"
    
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
    
    # Copy bundled fabric library
    log_info "Copying bundled fabric library to $lib_dir"
    if [[ -d "${SCRIPT_DIR}/fabric" ]]; then
        cp -r "${SCRIPT_DIR}/fabric" "$lib_dir/"
        log_success "Bundled fabric library copied successfully"
    else
        log_warning "Bundled fabric directory not found at ${SCRIPT_DIR}/fabric"
    fi
    
    # Update shebang in main script
    if [[ "$PREFIX" != "/usr/local" ]] && [[ "$PREFIX" != "/usr"* ]]; then
        # User installation - use virtual environment python
        local venv_python="${PREFIX}/lib/pf-runner-venv/bin/python"
        sed -i "1s|^.*$|#!${venv_python}|" "${lib_dir}/pf_parser.py"
    else
        # System installation - use system python
        sed -i "1s|^.*$|#!/usr/bin/env python3|" "${lib_dir}/pf_parser.py"
    fi
    
    # Make executable
    chmod +x "${lib_dir}/pf_parser.py"
    
    # Create pf executable
    cat > "${bin_dir}/pf" << EOF
#!/usr/bin/env bash
# pf - Wrapper script for pf-runner
exec "${lib_dir}/pf_parser.py" "\$@"
EOF
    chmod +x "${bin_dir}/pf"
    
    # Create symlink for local development
    if [[ -d "$lib_dir" ]]; then
        ln -sfn pf_parser.py "${lib_dir}/pf"
    fi
    
    log_success "pf-runner installed to $lib_dir"
    log_success "pf executable created at ${bin_dir}/pf"
}

check_container_runtime() {
    if command -v "${CONTAINER_RT}" >/dev/null 2>&1; then
        return 0
    fi

    if [[ "$CONTAINER_RT_SET" == false ]]; then
        if command -v podman >/dev/null 2>&1; then
            CONTAINER_RT="podman"
            return 0
        fi
        if command -v docker >/dev/null 2>&1; then
            CONTAINER_RT="docker"
            log_warning "podman not found; using docker instead"
            return 0
        fi
    fi

    log_error "Container runtime '${CONTAINER_RT}' not found."
    log_info "Install podman or docker, or run: ./install.sh --mode native"
    exit 1
}

image_exists() {
    local image="$1"
    if [[ "$CONTAINER_RT" == "podman" ]]; then
        podman image exists "$image" >/dev/null 2>&1
    else
        docker image inspect "$image" >/dev/null 2>&1
    fi
}

build_container_images() {
    if [[ "$SKIP_BUILD" == true ]]; then
        log_info "Skipping container image build (--skip-build)"
        return 0
    fi

    log_info "Building base image (${BASE_IMAGE_DEFAULT})..."
    "${CONTAINER_RT}" build -t "${BASE_IMAGE_DEFAULT}" -f "containers/dockerfiles/Dockerfile.base" "${SCRIPT_DIR}"

    log_info "Building pf-runner image (${CONTAINER_IMAGE})..."
    "${CONTAINER_RT}" build -t "${CONTAINER_IMAGE}" -f "containers/dockerfiles/Dockerfile.pf-runner" "${SCRIPT_DIR}"

    log_success "Container images built successfully"
}

install_container_wrapper() {
    if [[ "$NO_WRAPPER" == true ]]; then
        log_info "Skipping wrapper install (--no-wrapper)"
        return 0
    fi

    local lib_dir="${PREFIX}/lib/pf-runner"
    local bin_dir="${PREFIX}/bin"

    mkdir -p "$lib_dir" "$bin_dir"

    log_info "Installing pf wrapper..."
    cp "${PF_RUNNER_DIR}/pf_universal" "${lib_dir}/pf_universal"
    chmod +x "${lib_dir}/pf_universal"

    cat > "${bin_dir}/pf" << EOF
#!/usr/bin/env bash
if [[ -z "\${PF_IMAGE:-}" ]]; then
  export PF_IMAGE="${CONTAINER_IMAGE}"
fi
if [[ -z "\${PF_RUNTIME:-}" ]]; then
  export PF_RUNTIME="${CONTAINER_RT}"
fi
exec "${lib_dir}/pf_universal" "\$@"
EOF
    chmod +x "${bin_dir}/pf"

    log_success "pf wrapper installed to ${bin_dir}/pf"
}

validate_container_installation() {
    log_info "Validating container installation..."

    if [[ "$NO_WRAPPER" != true ]]; then
        local pf_cmd="${PREFIX}/bin/pf"
        if [[ ! -x "$pf_cmd" ]]; then
            log_error "pf wrapper not found or not executable at $pf_cmd"
            return 1
        fi
    fi

    if [[ "$SKIP_BUILD" != true ]]; then
        if ! image_exists "${CONTAINER_IMAGE}"; then
            log_error "Container image not found: ${CONTAINER_IMAGE}"
            return 1
        fi
    fi

    log_success "Container installation validation passed"
    return 0
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
    
    # Test basic pf functionality
    log_info "Testing pf --version..."
    if ! "$pf_cmd" --version >/dev/null 2>&1; then
        log_error "pf --version failed"
        return 1
    fi
    
    log_info "Testing pf list..."
    if ! "$pf_cmd" list >/dev/null 2>&1; then
        log_error "pf list failed"
        return 1
    fi
    
    # Test a simple task if available
    log_info "Testing basic pf task execution..."
    if "$pf_cmd" list 2>/dev/null | grep -q "hello\|test\|demo" 2>/dev/null; then
        # Try to run a simple task
        local test_task
        test_task=$("$pf_cmd" list 2>/dev/null | grep -E "hello|test|demo" | head -1 | awk '{print $1}' || echo "")
        if [[ -n "$test_task" ]]; then
            log_info "Running test task: $test_task"
            if "$pf_cmd" "$test_task" >/dev/null 2>&1; then
                log_success "Test task '$test_task' executed successfully"
            else
                log_warning "Test task '$test_task' failed, but basic pf functionality works"
            fi
        fi
    fi
    
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

    # Check permissions
    check_permissions

    if [[ "$MODE" == "container" ]]; then
        check_container_runtime
        log_info "Container runtime: ${CONTAINER_RT}"
        log_info "pf-runner image: ${CONTAINER_IMAGE}"

        build_container_images

        if [[ "$NO_WRAPPER" != true ]]; then
            install_container_wrapper
            install_completions
        else
            log_info "Wrapper installation skipped"
        fi

        if validate_container_installation; then
            echo ""
            log_success "🎉 pf-runner container installation completed successfully!"
            echo ""
            log_info "Installation summary:"
            echo "  • container runtime: ${CONTAINER_RT}"
            echo "  • base image: ${BASE_IMAGE_DEFAULT}"
            echo "  • pf-runner image: ${CONTAINER_IMAGE}"
            if [[ "$NO_WRAPPER" != true ]]; then
                echo "  • pf wrapper: ${PREFIX}/bin/pf"
                echo "  • wrapper script: ${PREFIX}/lib/pf-runner/pf_universal"
                echo ""
                update_path_info
                echo ""
                log_info "Next steps:"
                echo "  1. Restart your shell or run: source ~/.bashrc"
                echo "  2. Try: pf --version"
                echo "  3. Try: pf list"
                echo "  4. Build full container suite: pf install-full runtime=${CONTAINER_RT}"
            else
                echo "  • pf wrapper: skipped (--no-wrapper)"
                echo ""
                log_info "Next steps:"
                echo "  1. Install the wrapper later with:"
                echo "     ./install.sh --mode container --runtime ${CONTAINER_RT}"
                echo "  2. Or run directly with:"
                echo "     PF_IMAGE=${CONTAINER_IMAGE} PF_RUNTIME=${CONTAINER_RT} ${PF_RUNNER_DIR}/pf_universal"
            fi
            echo ""
            log_success "Happy task running! 🚀"
        else
            log_error "Container installation validation failed"
            exit 1
        fi
        return 0
    fi

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
        echo "  • Python dependencies: fabric, lark"
        echo ""

        update_path_info

        echo ""
        log_info "Next steps:"
        echo "  1. Restart your shell or run: source ~/.bashrc"
        echo "  2. Try: pf --version"
        echo "  3. Try: pf list"
        echo "  4. Read the documentation: cat README.md"
        echo ""
        log_success "Happy task running! 🚀"
    else
        log_error "Native installation validation failed"
        exit 1
    fi
}

# Run main function
main "$@"
