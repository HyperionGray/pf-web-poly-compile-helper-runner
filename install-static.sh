#!/usr/bin/env bash
# install-static.sh - Install pf-runner source runtime (no build required)
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
SELF_TEST=false

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
        --self-test)
            SELF_TEST=true
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
    --self-test       Run post-install smoke tests (pf -V, pf --help, pf list)
    --help, -h        Show this help message

EXAMPLES:
    # System-wide install (requires sudo)
    sudo ./install-static.sh

    # User install (no sudo required)
    ./install-static.sh --prefix ~/.local

WHAT THIS DOES:
    Installs pf-runner from source without requiring any build step.
    Copies runtime files from pf-runner-full and creates a wrapper script.
    No Python dependencies are installed - you need to install them separately.
    Use --self-test to validate the install immediately after deployment.

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

# Check if source runtime exists
if [[ ! -d "$PF_RUNNER_FULL_DIR" ]]; then
    log_error "pf-runner-full directory not found at $PF_RUNNER_FULL_DIR"
    log_info "Please run this script from the repository root directory."
    exit 1
fi

# Required source files
for required_file in pf_main.py pf.lark; do
    if [[ ! -f "$PF_RUNNER_FULL_DIR/$required_file" ]]; then
        log_error "Required source file not found: $PF_RUNNER_FULL_DIR/$required_file"
        exit 1
    fi
done

if [[ ! -d "$PF_RUNNER_FULL_DIR/pf-files" ]]; then
    log_error "Required task directory not found: $PF_RUNNER_FULL_DIR/pf-files"
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

# Copy Python files
if ! cp -r "$PF_RUNNER_FULL_DIR"/*.py "$LIB_DIR/" 2>/dev/null; then
    log_error "Failed to copy Python files from $PF_RUNNER_FULL_DIR"
    exit 1
fi

# Copy grammar file (required)
cp "$PF_RUNNER_FULL_DIR/pf.lark" "$LIB_DIR/"

# Copy default task files (required for pf list/help discovery)
cp -r "$PF_RUNNER_FULL_DIR/pf-files" "$LIB_DIR/"

# Copy egg-info if it exists (optional)
if [[ -d "$PF_RUNNER_FULL_DIR/pf_runner.egg-info" ]]; then
    cp -r "$PF_RUNNER_FULL_DIR/pf_runner.egg-info" "$LIB_DIR/"
fi

# Create pf wrapper executable
cat > "${BIN_DIR}/pf" << 'EOF'
#!/usr/bin/env python3
# pf - Wrapper for pf-runner
import sys
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

run_self_test() {
    local pf_cmd="${BIN_DIR}/pf"
    local test_dir

    log_info "Running post-install self-test..."

    if ! "$pf_cmd" -V >/dev/null 2>&1; then
        log_error "Self-test failed: pf -V"
        return 1
    fi

    if ! "$pf_cmd" --help >/dev/null 2>&1; then
        log_error "Self-test failed: pf --help"
        return 1
    fi

    test_dir="$(mktemp -d)"
    if ! (cd "$test_dir" && "$pf_cmd" list >/dev/null 2>&1); then
        rm -rf "$test_dir"
        log_error "Self-test failed: pf list"
        return 1
    fi
    rm -rf "$test_dir"

    log_success "Self-test passed (pf -V, pf --help, pf list)"
}

log_success "pf-runner installed to ${LIB_DIR}"
log_success "pf executable installed to ${BIN_DIR}/pf"

if [[ "$SELF_TEST" == true ]]; then
    if ! run_self_test; then
        log_error "Installation completed, but self-test failed."
        log_info "Install dependencies manually if needed:"
        log_info "  pip install 'lark>=1.1.0' 'fabric>=3.2,<4' 'typer>=0.12'"
        exit 1
    fi
fi

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
log_success "Happy task running! 🚀"
