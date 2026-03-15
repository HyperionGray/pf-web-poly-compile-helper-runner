#!/usr/bin/env bash
# install-static.sh - Install pf-runner from source files (no build step)
# Usage: ./install-static.sh [--prefix PATH] [--dry-run] [--verify]

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

PREFIX=""
PREFIX_SET=false
SHOW_HELP=false
DRY_RUN=false
VERIFY_INSTALL=false

show_help() {
    cat << EOF
pf-runner Static Installer (source-file install, no build required)

USAGE:
    ./install-static.sh [OPTIONS]

OPTIONS:
    --prefix PATH     Install prefix (default: /usr/local when root, ~/.local otherwise)
    --dry-run         Print planned actions without modifying the system
    --verify          Run post-install verification commands
    --help, -h        Show this help message

EXAMPLES:
    # System-wide install (requires sudo)
    sudo ./install-static.sh

    # User install (no sudo required)
    ./install-static.sh --prefix ~/.local

    # Preview actions only
    ./install-static.sh --prefix ~/.local --dry-run

    # Install and immediately verify
    ./install-static.sh --prefix ~/.local --verify
EOF
}

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

run_cmd() {
    if [[ "$DRY_RUN" == true ]]; then
        printf '[DRY-RUN] '
        printf '%q ' "$@"
        printf '\n'
        return 0
    fi
    "$@"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --prefix)
            if [[ $# -lt 2 ]]; then
                log_error "--prefix requires a value"
                exit 1
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
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --verify)
            VERIFY_INSTALL=true
            shift
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            SHOW_HELP=true
            shift
            ;;
    esac
done

if [[ "$SHOW_HELP" == true ]]; then
    show_help
    exit 0
fi

if [[ "$PREFIX_SET" == false ]]; then
    if [[ $EUID -eq 0 ]]; then
        PREFIX="$DEFAULT_PREFIX"
    else
        PREFIX="$DEFAULT_PREFIX_USER"
    fi
fi

if [[ "$PREFIX" == /usr* ]] && [[ $EUID -ne 0 ]]; then
    log_error "Installation to ${PREFIX} requires root privileges."
    log_info "Try: sudo ./install-static.sh --prefix ${PREFIX}"
    log_info "Or use user installation: ./install-static.sh --prefix ~/.local"
    exit 1
fi

if [[ ! -d "$PF_RUNNER_FULL_DIR" ]]; then
    log_error "Source directory not found: $PF_RUNNER_FULL_DIR"
    log_info "Run this script from repository root."
    exit 1
fi

if [[ ! -f "$PF_RUNNER_FULL_DIR/pf_main.py" ]]; then
    log_error "Missing required source file: $PF_RUNNER_FULL_DIR/pf_main.py"
    exit 1
fi

if [[ ! -f "$PF_RUNNER_FULL_DIR/pf.lark" ]]; then
    log_error "Missing required grammar file: $PF_RUNNER_FULL_DIR/pf.lark"
    exit 1
fi

LIB_DIR="${PREFIX}/lib/pf-runner"
BIN_DIR="${PREFIX}/bin"

echo -e "${BLUE}pf-runner Static Installer${NC}"
echo "=========================="
echo ""
log_info "Prefix: ${PREFIX}"
if [[ "$DRY_RUN" == true ]]; then
    log_info "Running in dry-run mode (no changes will be made)"
fi
echo ""

run_cmd mkdir -p "$LIB_DIR" "$BIN_DIR"

log_info "Copying pf-runner Python sources to ${LIB_DIR}"
run_cmd cp -r "$PF_RUNNER_FULL_DIR"/*.py "$LIB_DIR/"
run_cmd cp "$PF_RUNNER_FULL_DIR/pf.lark" "$LIB_DIR/"

if [[ -d "$PF_RUNNER_FULL_DIR/pf_runner.egg-info" ]]; then
    run_cmd cp -r "$PF_RUNNER_FULL_DIR/pf_runner.egg-info" "$LIB_DIR/"
fi

if [[ -d "$PF_RUNNER_FULL_DIR/pf-files" ]]; then
    run_cmd cp -r "$PF_RUNNER_FULL_DIR/pf-files" "$LIB_DIR/"
fi

if [[ -f "$PF_RUNNER_FULL_DIR/test.pf" ]]; then
    run_cmd cp "$PF_RUNNER_FULL_DIR/test.pf" "$LIB_DIR/"
fi

if [[ "$DRY_RUN" == true ]]; then
    printf '[DRY-RUN] would write wrapper script to %s\n' "${BIN_DIR}/pf"
else
    cat > "${BIN_DIR}/pf" << 'EOF'
#!/usr/bin/env python3
import sys
from pathlib import Path

lib_dir = Path(__file__).resolve().parent.parent / "lib" / "pf-runner"
sys.path.insert(0, str(lib_dir))

try:
    import pf_main
except ImportError as exc:
    print(f"ERROR: Could not import pf_main from {lib_dir}", file=sys.stderr)
    print(f"Import error: {exc}", file=sys.stderr)
    print("", file=sys.stderr)
    print("Install dependencies and try again:", file=sys.stderr)
    print("  pip install 'lark>=1.1.0' 'fabric>=3.2,<4' 'typer>=0.12'", file=sys.stderr)
    sys.exit(1)

exit_code = pf_main.main(sys.argv[1:])
sys.exit(0 if exit_code is None else exit_code)
EOF
    run_cmd chmod +x "${BIN_DIR}/pf"
fi

log_success "pf-runner files installed to ${LIB_DIR}"
log_success "pf wrapper installed to ${BIN_DIR}/pf"

if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    log_warning "The installation directory ${BIN_DIR} is not in your PATH"
    log_info "Add this to your shell profile (~/.bashrc, ~/.zshrc):"
    echo ""
    echo "    export PATH=\"${BIN_DIR}:\$PATH\""
    echo ""
else
    log_success "Installation directory already present in PATH"
fi

if [[ "$VERIFY_INSTALL" == true ]]; then
    echo ""
    if [[ "$DRY_RUN" == true ]]; then
        log_info "Verification skipped in dry-run mode."
    else
        log_info "Running post-install verification..."
        if "${BIN_DIR}/pf" -V >/dev/null 2>&1; then
            log_success "Verification: pf -V"
        else
            log_error "Verification failed: ${BIN_DIR}/pf -V"
            exit 1
        fi

        if [[ -f "${LIB_DIR}/test.pf" ]] && "${BIN_DIR}/pf" "${LIB_DIR}/test.pf" list >/dev/null 2>&1; then
            log_success "Verification: pf test.pf list"
        else
            log_warning "Skipped task-list verification (test.pf not available or command failed)"
        fi
    fi
fi

echo ""
log_success "Installation completed."
echo ""
log_info "Next steps:"
echo "  1. ${BIN_DIR}/pf -V"
echo "  2. ${BIN_DIR}/pf list"
echo "  3. ${BIN_DIR}/pf \"${LIB_DIR}/test.pf\" smoke  # if test.pf is present"
