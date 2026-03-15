#!/usr/bin/env bash
# install-static.sh - Install pf-runner static executable
# Usage: ./install-static.sh [--prefix PATH] [--dry-run]

set -euo pipefail

# Configuration
DEFAULT_PREFIX="/usr/local"
DEFAULT_PREFIX_USER="${HOME}/.local"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATIC_EXEC="${SCRIPT_DIR}/pf-runner-full/pf-static"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Parse arguments
PREFIX=""
PREFIX_SET=false
DRY_RUN=false
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
        --dry-run)
            DRY_RUN=true
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
    --dry-run         Show planned actions without changing files
    --help, -h        Show this help message

EXAMPLES:
    # System-wide install (requires sudo)
    sudo ./install-static.sh

    # User install (no sudo required)
    ./install-static.sh --prefix ~/.local

WHAT THIS DOES:
    Installs the pre-built static pf executable from:
      ${STATIC_EXEC}
    Requires the static binary to be built first:
      cd pf-runner-full && make build-static

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
        if [[ "$DRY_RUN" == true ]]; then
            log_warning "Dry-run: installation to ${PREFIX} would require root privileges."
        else
            log_error "Installation to ${PREFIX} requires root privileges."
            log_info "Try: sudo ./install-static.sh"
            log_info "Or use user installation: ./install-static.sh --prefix ~/.local"
            exit 1
        fi
    fi
fi

# Check if static executable exists
if [[ ! -f "$STATIC_EXEC" ]]; then
    if [[ "$DRY_RUN" == true ]]; then
        log_warning "Dry-run: static executable not found at $STATIC_EXEC"
        log_info "Dry-run can still show planned actions."
    else
        log_error "Static executable not found at $STATIC_EXEC"
        log_info "Please build it first by running:"
        log_info "  cd pf-runner-full && make build-static"
        log_info ""
        log_info "This will create a standalone executable using PyInstaller."
        exit 1
    fi
fi

echo -e "${BLUE}pf-runner Installer${NC}"
echo "===================="
echo ""

log_info "Installing static pf executable..."

# Create directories
BIN_DIR="${PREFIX}/bin"
mkdir -p "$BIN_DIR"

if [[ "$DRY_RUN" == true ]]; then
    log_info "Dry-run mode enabled. No files were changed."
    log_info "Planned actions:"
    echo "  1. Create directory:"
    echo "     - ${BIN_DIR}"
    echo "  2. Copy static executable:"
    echo "     ${STATIC_EXEC} -> ${BIN_DIR}/pf"
    echo "  3. Mark executable:"
    echo "     chmod +x ${BIN_DIR}/pf"
    echo ""
    log_info "Dry-run complete."
    exit 0
fi

if ! cp "$STATIC_EXEC" "${BIN_DIR}/pf"; then
    log_error "Failed to copy static executable from ${STATIC_EXEC}"
    exit 1
fi
chmod +x "${BIN_DIR}/pf"

log_success "pf-runner static executable installed to ${BIN_DIR}/pf"

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
