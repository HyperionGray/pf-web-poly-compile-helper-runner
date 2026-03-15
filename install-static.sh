#!/usr/bin/env bash
# install-static.sh - Install pf-runner (Python-based, no build required)
# Usage: ./install-static.sh [--prefix PATH] [--verify|--verify-only]

set -euo pipefail

# Configuration
DEFAULT_PREFIX="/usr/local"
DEFAULT_PREFIX_USER="${HOME}/.local"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PF_RUNNER_FULL_DIR="${SCRIPT_DIR}/pf-runner-full"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Parse arguments
PREFIX=""
PREFIX_SET=false
SHOW_HELP=false
VERIFY_AFTER_INSTALL=false
VERIFY_ONLY=false

# Runtime dependency guidance for the Python wrapper
REQUIRED_PYTHON_MODULES=("lark" "fabric" "typer")
PIP_REQUIREMENTS=("lark>=1.1.0" "fabric>=3.2,<4" "typer>=0.12")

while [[ $# -gt 0 ]]; do
    case $1 in
        --prefix)
            if [[ $# -lt 2 ]]; then
                echo -e "${RED}Error: --prefix requires a path${NC}" >&2
                SHOW_HELP=true
                break
            fi
            PREFIX="$2"
            PREFIX_SET=true
            shift 2
            ;;
        --prefix=*)
            PREFIX="${1#*=}"
            PREFIX_SET=true
            shift
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        --verify)
            VERIFY_AFTER_INSTALL=true
            shift
            ;;
        --verify-only)
            VERIFY_AFTER_INSTALL=true
            VERIFY_ONLY=true
            shift
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}" >&2
            SHOW_HELP=true
            shift
            ;;
    esac
done

show_help() {
    cat << EOF
pf-runner Installer (No Build Required)

USAGE:
    ./install-static.sh [OPTIONS]

OPTIONS:
    --prefix PATH     Install prefix (default: /usr/local or ~/.local)
    --verify          Run post-install verification checks
    --verify-only     Only run verification checks (no install)
    --help, -h        Show this help message

EXAMPLES:
    # System-wide install (requires sudo)
    sudo ./install-static.sh

    # User install (no sudo required)
    ./install-static.sh --prefix ~/.local

    # Install and immediately verify
    ./install-static.sh --prefix ~/.local --verify

    # Verify an existing installation
    ./install-static.sh --prefix ~/.local --verify-only

WHAT THIS DOES:
    Installs pf-runner from source without requiring any build step.
    Copies the pf-runner-full directory and creates a wrapper script.
    No Python dependencies are installed - you need to install them separately
    or use the Makefile in pf-runner-full. Use --verify/--verify-only to
    validate the installed command and dependency health.

EOF
}

if [[ "$SHOW_HELP" == true ]]; then
    show_help
    exit 0
fi

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

build_pip_hint() {
    local joined_requirements
    joined_requirements=$(printf "'%s' " "${PIP_REQUIREMENTS[@]}")
    if [[ $EUID -eq 0 ]]; then
        echo "python3 -m pip install ${joined_requirements% }"
    else
        echo "python3 -m pip install --user ${joined_requirements% }"
    fi
}

check_python_dependencies() {
    local missing_modules=()

    log_info "Checking Python runtime dependencies..."
    for module in "${REQUIRED_PYTHON_MODULES[@]}"; do
        if python3 -c "import ${module}" >/dev/null 2>&1; then
            log_success "Dependency available: ${module}"
        else
            log_warning "Dependency missing: ${module}"
            missing_modules+=("${module}")
        fi
    done

    if [[ ${#missing_modules[@]} -gt 0 ]]; then
        log_warning "pf may fail until missing Python modules are installed."
        log_info "Install them with:"
        echo "  $(build_pip_hint)"
        return 1
    fi

    return 0
}

verify_installation() {
    local verify_ok=true
    local verify_stdout
    local verify_stderr
    local pf_cmd="${BIN_DIR}/pf"

    echo ""
    log_info "Running installation verification checks..."

    if [[ ! -x "$pf_cmd" ]]; then
        log_error "Expected executable not found: $pf_cmd"
        return 1
    fi
    log_success "Found executable: $pf_cmd"

    verify_stdout="$(mktemp)"
    verify_stderr="$(mktemp)"
    if "$pf_cmd" --version >"$verify_stdout" 2>"$verify_stderr"; then
        local version_line
        version_line="$(sed -n '1p' "$verify_stdout")"
        if [[ -n "$version_line" ]]; then
            log_success "pf --version output: $version_line"
        else
            log_success "pf --version executed successfully"
        fi
    else
        log_error "pf --version failed"
        log_info "First lines of stderr:"
        sed -n '1,5p' "$verify_stderr" | sed 's/^/  /'
        verify_ok=false
    fi
    rm -f "$verify_stdout" "$verify_stderr"

    if ! check_python_dependencies; then
        verify_ok=false
    fi

    if [[ "$verify_ok" == true ]]; then
        log_success "Verification checks passed."
        return 0
    fi

    log_error "Verification checks failed."
    return 1
}

# Set default prefix
if [[ "$PREFIX_SET" == false ]]; then
    if [[ $EUID -eq 0 ]]; then
        PREFIX="$DEFAULT_PREFIX"
    else
        PREFIX="$DEFAULT_PREFIX_USER"
    fi
fi

# Derived paths
LIB_DIR="${PREFIX}/lib/pf-runner"
BIN_DIR="${PREFIX}/bin"

if [[ "$VERIFY_ONLY" == true ]]; then
    verify_installation
    exit $?
fi

# Check permissions
if [[ "$PREFIX" == "/usr/local" ]] || [[ "$PREFIX" == "/usr"* ]]; then
    if [[ $EUID -ne 0 ]]; then
        log_error "Installation to ${PREFIX} requires root privileges."
        log_info "Try: sudo ./install-static.sh"
        log_info "Or use user installation: ./install-static.sh --prefix ~/.local"
        exit 1
    fi
fi

# Check if pf-runner-full directory exists
if [[ ! -d "$PF_RUNNER_FULL_DIR" ]]; then
    log_error "pf-runner source directory not found at $PF_RUNNER_FULL_DIR"
    exit 1
fi

echo -e "${BLUE}pf-runner Installer${NC}"
echo "===================="
echo ""

log_info "Installing pf-runner from source..."

# Create directories
mkdir -p "$LIB_DIR" "$BIN_DIR"

# Copy pf-runner-full directory
log_info "Copying pf-runner files to $LIB_DIR"

# Copy Python files
if ! cp -r "$PF_RUNNER_FULL_DIR"/*.py "$LIB_DIR/" 2>/dev/null; then
    log_error "Failed to copy Python files from $PF_RUNNER_FULL_DIR"
    exit 1
fi

# Copy grammar file (required)
if [[ ! -f "$PF_RUNNER_FULL_DIR/pf.lark" ]]; then
    log_error "Required file pf.lark not found in $PF_RUNNER_FULL_DIR"
    exit 1
fi
cp "$PF_RUNNER_FULL_DIR/pf.lark" "$LIB_DIR/"

# Copy egg-info if it exists (optional)
if [[ -d "$PF_RUNNER_FULL_DIR/pf_runner.egg-info" ]]; then
    cp -r "$PF_RUNNER_FULL_DIR/pf_runner.egg-info" "$LIB_DIR/"
fi

# Create pf wrapper executable
cat > "${BIN_DIR}/pf" << 'EOF'
#!/usr/bin/env python3
# pf - Wrapper for pf-runner
import sys
import os
from pathlib import Path

# Add library directory to path
lib_dir = Path(__file__).parent.parent / "lib" / "pf-runner"
sys.path.insert(0, str(lib_dir))

# Import and run pf_main
try:
    import pf_main
    exit_code = pf_main.main(sys.argv[1:])
    # Handle None return value (treat as success)
    sys.exit(exit_code if exit_code is not None else 0)
except ImportError as e:
    print(f"ERROR: Could not import pf_main from {lib_dir}", file=sys.stderr)
    print(f"Error: {e}", file=sys.stderr)
    print("", file=sys.stderr)
    print("Make sure Python dependencies are installed:", file=sys.stderr)
    print("  pip install 'lark>=1.1.0' 'fabric>=3.2,<4' 'typer>=0.12'", file=sys.stderr)
    sys.exit(1)
EOF
chmod +x "${BIN_DIR}/pf"

log_success "pf-runner installed to ${LIB_DIR}"
log_success "pf executable installed to ${BIN_DIR}/pf"

# Check if in PATH
if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    log_warning "The installation directory ${BIN_DIR} is not in your PATH"
    log_info "Add the following to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
    echo ""
    echo "    export PATH=\"${BIN_DIR}:\$PATH\""
    echo ""
else
    log_success "Installation directory is already in PATH"
fi

echo ""
log_success "🎉 Installation completed successfully!"
echo ""
log_info "Next steps:"
echo "  1. Try: pf --version"
echo "  2. Try: pf list"
echo ""

if [[ "$VERIFY_AFTER_INSTALL" == true ]]; then
    verify_installation
else
    log_info "Optional: run './install-static.sh --prefix ${PREFIX} --verify-only' for diagnostics."
fi

log_success "Happy task running! 🚀"
