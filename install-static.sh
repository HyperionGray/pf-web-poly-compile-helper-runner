#!/usr/bin/env bash
# install-static.sh - Install pf-runner from source files.
# Usage: ./install-static.sh [--prefix PATH] [--verify]

set -euo pipefail

# Configuration
DEFAULT_PREFIX="/usr/local"
DEFAULT_PREFIX_USER="${HOME}/.local"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PF_RUNNER_FULL_DIR="${SCRIPT_DIR}/pf-runner-full"
SOURCE_TEST_FILE="${PF_RUNNER_FULL_DIR}/test.pf"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
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

show_help() {
    cat << EOF
pf-runner Source Installer

USAGE:
    ./install-static.sh [OPTIONS]

OPTIONS:
    --prefix PATH     Install prefix (default: /usr/local or ~/.local)
    --verify          Run post-install smoke checks
    --help, -h        Show this help message

EXAMPLES:
    # System-wide install (requires sudo)
    sudo ./install-static.sh

    # User install (no sudo required)
    ./install-static.sh --prefix ~/.local

    # User install with post-install verification
    ./install-static.sh --prefix ~/.local --verify

WHAT THIS DOES:
    Installs pf-runner by copying pf-runner-full source files and creating
    a wrapper script at <prefix>/bin/pf.
    Python dependencies are not installed automatically. If missing, install:
      pip install 'lark>=1.1.0' 'fabric>=3.2,<4' 'typer>=0.12'

EOF
}

# Parse arguments
PREFIX=""
PREFIX_SET=false
VERIFY=false
SHOW_HELP=false
PARSE_ERROR=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --prefix)
            if [[ $# -lt 2 ]]; then
                log_error "--prefix requires a path argument"
                PARSE_ERROR=true
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
        --verify)
            VERIFY=true
            shift
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            PARSE_ERROR=true
            SHOW_HELP=true
            shift
            ;;
    esac
done

if [[ "$SHOW_HELP" == true ]]; then
    show_help
    if [[ "$PARSE_ERROR" == true ]]; then
        exit 1
    fi
    exit 0
fi

# Set default prefix
if [[ "$PREFIX_SET" == false ]]; then
    if [[ $EUID -eq 0 ]]; then
        PREFIX="$DEFAULT_PREFIX"
    else
        PREFIX="$DEFAULT_PREFIX_USER"
    fi
fi

# Check permissions
if [[ "$PREFIX" == "/usr/local" ]] || [[ "$PREFIX" == /usr/* ]]; then
    if [[ $EUID -ne 0 ]]; then
        log_error "Installation to ${PREFIX} requires root privileges."
        log_info "Try: sudo ./install-static.sh"
        log_info "Or use user installation: ./install-static.sh --prefix ~/.local"
        exit 1
    fi
fi

# Validate source tree
if [[ ! -d "$PF_RUNNER_FULL_DIR" ]]; then
    log_error "pf-runner-full directory not found at $PF_RUNNER_FULL_DIR"
    exit 1
fi

if [[ ! -f "${PF_RUNNER_FULL_DIR}/pf_main.py" ]]; then
    log_error "Required file missing: ${PF_RUNNER_FULL_DIR}/pf_main.py"
    exit 1
fi

if [[ ! -f "${PF_RUNNER_FULL_DIR}/pf.lark" ]]; then
    log_error "Required file missing: ${PF_RUNNER_FULL_DIR}/pf.lark"
    exit 1
fi

echo -e "${BLUE}pf-runner Source Installer${NC}"
echo "=========================="
echo ""

log_info "Installing pf-runner from ${PF_RUNNER_FULL_DIR}"

LIB_DIR="${PREFIX}/lib/pf-runner"
BIN_DIR="${PREFIX}/bin"
mkdir -p "$LIB_DIR" "$BIN_DIR"

log_info "Copying pf-runner files to ${LIB_DIR}"

shopt -s nullglob
PYTHON_SOURCES=("${PF_RUNNER_FULL_DIR}"/*.py)
shopt -u nullglob
if [[ ${#PYTHON_SOURCES[@]} -eq 0 ]]; then
    log_error "No Python source files found in ${PF_RUNNER_FULL_DIR}"
    exit 1
fi
cp "${PYTHON_SOURCES[@]}" "$LIB_DIR/"
cp "${PF_RUNNER_FULL_DIR}/pf.lark" "$LIB_DIR/"

# Optional metadata and example task file for smoke testing.
if [[ -d "${PF_RUNNER_FULL_DIR}/pf_runner.egg-info" ]]; then
    cp -r "${PF_RUNNER_FULL_DIR}/pf_runner.egg-info" "$LIB_DIR/"
fi

if [[ -f "$SOURCE_TEST_FILE" ]]; then
    cp "$SOURCE_TEST_FILE" "${LIB_DIR}/test.pf"
fi

cat > "${BIN_DIR}/pf" << 'EOF'
#!/usr/bin/env python3
# pf - Wrapper for pf-runner
import sys
from pathlib import Path

lib_dir = Path(__file__).resolve().parent.parent / "lib" / "pf-runner"
sys.path.insert(0, str(lib_dir))

try:
    import pf_main
    exit_code = pf_main.main(sys.argv[1:])
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

verify_installation() {
    local pf_bin="${BIN_DIR}/pf"
    local test_file="${LIB_DIR}/test.pf"

    log_info "Running post-install verification"

    if ! "${pf_bin}" -V >/dev/null 2>&1; then
        log_error "Verification failed: 'pf -V' did not succeed."
        log_info "Install dependencies and retry:"
        echo "    pip install 'lark>=1.1.0' 'fabric>=3.2,<4' 'typer>=0.12'"
        return 1
    fi

    if [[ -f "$test_file" ]]; then
        if ! "${pf_bin}" "$test_file" list >/dev/null 2>&1; then
            log_error "Verification failed: could not list tasks from ${test_file}"
            return 1
        fi
    else
        log_warning "Verification skipped task listing because ${test_file} is missing"
    fi

    log_success "Post-install verification passed"
}

log_success "pf-runner installed to ${LIB_DIR}"
log_success "pf executable installed to ${BIN_DIR}/pf"

if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    log_warning "The installation directory ${BIN_DIR} is not in your PATH"
    log_info "Add this line to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
    echo ""
    echo "    export PATH=\"${BIN_DIR}:\$PATH\""
    echo ""
else
    log_success "Installation directory is already in PATH"
fi

if [[ "$VERIFY" == true ]]; then
    verify_installation
else
    log_info "Run './install-static.sh --prefix ${PREFIX} --verify' to smoke test this installation."
fi

echo ""
log_success "Installation completed successfully."
echo ""
log_info "Next steps:"
echo "  1. Try: ${BIN_DIR}/pf -V"
echo "  2. Try: ${BIN_DIR}/pf ${LIB_DIR}/test.pf list"
