#!/usr/bin/env bash
# install-static.sh - Install pf-runner (Python-based, no build required)
# Usage: ./install-static.sh [--prefix PATH]

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

show_help() {
    cat << EOF
pf-runner Installer (No Build Required)

USAGE:
    ./install-static.sh [OPTIONS]

OPTIONS:
    --prefix PATH     Install prefix (default: /usr/local or ~/.local)
    --help, -h        Show this help message

EXAMPLES:
    # System-wide install (requires sudo)
    sudo ./install-static.sh

    # User install (no sudo required)
    ./install-static.sh --prefix ~/.local

WHAT THIS DOES:
    Installs pf-runner from source without requiring any build step.
    Copies the pf-runner-full directory and creates a wrapper script.
    No Python dependencies are installed - you need to install them separately
    or use the Makefile in pf-runner-full.

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

# Set default prefix
if [[ "$PREFIX_SET" == false ]]; then
    if [[ $EUID -eq 0 ]]; then
        PREFIX="$DEFAULT_PREFIX"
    else
        PREFIX="$DEFAULT_PREFIX_USER"
    fi
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

# Check source files before installing the no-build wrapper.
if [[ ! -d "$PF_RUNNER_FULL_DIR" ]]; then
    log_error "pf-runner-full directory not found at $PF_RUNNER_FULL_DIR"
    log_info "This script must be run from the repository root."
    exit 1
fi

for required_file in pf_main.py pf_parser.py pf.lark; do
    if [[ ! -f "$PF_RUNNER_FULL_DIR/$required_file" ]]; then
        log_error "Required file not found: $PF_RUNNER_FULL_DIR/$required_file"
        exit 1
    fi
done

shopt -s nullglob
PYTHON_FILES=("$PF_RUNNER_FULL_DIR"/*.py)
shopt -u nullglob

if [[ ${#PYTHON_FILES[@]} -eq 0 ]]; then
    log_error "No Python source files found in $PF_RUNNER_FULL_DIR"
    exit 1
fi

echo -e "${BLUE}pf-runner Installer${NC}"
echo "===================="
echo ""

log_info "Installing pf-runner from source..."

# Create directories
LIB_DIR="${PREFIX}/lib/pf-runner"
BIN_DIR="${PREFIX}/bin"
mkdir -p "$LIB_DIR" "$BIN_DIR"

# Copy pf-runner-full directory
log_info "Copying pf-runner files to $LIB_DIR"

if ! cp "${PYTHON_FILES[@]}" "$LIB_DIR/"; then
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

# Copy bundled sources that the runner may reference at runtime.
if [[ -d "$PF_RUNNER_FULL_DIR/pf-files" ]]; then
    cp -r "$PF_RUNNER_FULL_DIR/pf-files" "$LIB_DIR/"
fi

if [[ -d "$PF_RUNNER_FULL_DIR/addon" ]]; then
    cp -r "$PF_RUNNER_FULL_DIR/addon" "$LIB_DIR/"
fi

if [[ -d "$PF_RUNNER_FULL_DIR/vendor" ]]; then
    cp -r "$PF_RUNNER_FULL_DIR/vendor" "$LIB_DIR/"
fi

if [[ -f "$PF_RUNNER_FULL_DIR/test.pf" ]]; then
    cp "$PF_RUNNER_FULL_DIR/test.pf" "$LIB_DIR/"
fi

# Create pf wrapper executable.
cat > "${BIN_DIR}/pf" << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

PREFIX_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LIB_DIR="${PREFIX_DIR}/lib/pf-runner"
DEFAULT_VENV_PY="${PREFIX_DIR}/lib/pf-runner-venv/bin/python"

if [[ -n "${PF_PYTHON:-}" && -x "${PF_PYTHON}" ]]; then
    PYTHON_BIN="${PF_PYTHON}"
elif [[ -x "${DEFAULT_VENV_PY}" ]]; then
    PYTHON_BIN="${DEFAULT_VENV_PY}"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
else
    echo "ERROR: Python 3 is required to run pf." >&2
    exit 1
fi

export PYTHONPATH="${LIB_DIR}${PYTHONPATH:+:${PYTHONPATH}}"

exec "${PYTHON_BIN}" - "${LIB_DIR}" "$@" <<'PY'
import sys
from pathlib import Path

lib_dir = Path(sys.argv[1])
args = sys.argv[2:]
sys.path.insert(0, str(lib_dir))

try:
    import pf_main
except ImportError as exc:
    print(f"ERROR: Could not import pf_main from {lib_dir}", file=sys.stderr)
    print(f"Error: {exc}", file=sys.stderr)
    print("", file=sys.stderr)
    print("Install runtime dependencies with:", file=sys.stderr)
    print("  python3 -m pip install 'lark>=1.1.0' 'fabric>=3.2,<4' 'typer>=0.12'", file=sys.stderr)
    print("Or point pf at a prepared interpreter:", file=sys.stderr)
    print("  PF_PYTHON=/path/to/python pf --version", file=sys.stderr)
    sys.exit(1)

exit_code = pf_main.main(args)
sys.exit(exit_code if exit_code is not None else 0)
PY
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
echo "  1. If needed, prepare a runtime Python with pf dependencies:"
echo "     python3 -m pip install 'lark>=1.1.0' 'fabric>=3.2,<4' 'typer>=0.12'"
echo "  2. Or point pf at a prepared interpreter:"
echo "     PF_PYTHON=/path/to/python pf --version"
echo "  3. Try: pf --version"
echo "  4. Run with a project Pfyfile, for example:"
echo "     pf ${LIB_DIR}/test.pf list"
echo ""
log_success "Happy task running! 🚀"
