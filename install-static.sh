#!/usr/bin/env bash
# install-static.sh - Install pf as static binary or Python wrapper.
# Usage: ./install-static.sh [--prefix PATH] [--mode auto|static|python]

set -euo pipefail

DEFAULT_PREFIX="/usr/local"
DEFAULT_PREFIX_USER="${HOME}/.local"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PF_RUNNER_FULL_DIR="${SCRIPT_DIR}/pf-runner-full"
STATIC_EXEC="${PF_RUNNER_FULL_DIR}/pf-static"
TEST_PF="${PF_RUNNER_FULL_DIR}/test.pf"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

PREFIX=""
PREFIX_SET=false
MODE="auto"
BUILD_STATIC_IF_MISSING=false
VERIFY_INSTALL=false

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
    cat << 'EOF'
pf installer (static + fallback modes)

USAGE:
    ./install-static.sh [OPTIONS]

OPTIONS:
    --prefix PATH                 Install prefix (default: /usr/local or ~/.local)
    --mode auto|static|python    Install mode (default: auto)
    --build-static-if-missing    Build pf-static via pf-runner-full/Makefile when missing
    --verify                     Run post-install smoke checks (pf -V and optional list test)
    --help, -h                   Show this help message

MODES:
    auto    Use static binary when available, otherwise install Python wrapper.
    static  Require and install pf-runner-full/pf-static.
    python  Install Python wrapper + runtime files into <prefix>/lib/pf-runner.

EXAMPLES:
    # System-wide install (auto mode)
    sudo ./install-static.sh

    # User install with static binary only
    ./install-static.sh --prefix ~/.local --mode static

    # User install and auto-build static binary if needed
    ./install-static.sh --prefix ~/.local --build-static-if-missing --verify
EOF
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
        --mode)
            if [[ $# -lt 2 ]]; then
                log_error "--mode requires one of: auto, static, python"
                exit 1
            fi
            MODE="$2"
            shift 2
            ;;
        --mode=*)
            MODE="${1#*=}"
            shift
            ;;
        --build-static-if-missing)
            BUILD_STATIC_IF_MISSING=true
            shift
            ;;
        --verify)
            VERIFY_INSTALL=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

if [[ "$MODE" != "auto" && "$MODE" != "static" && "$MODE" != "python" ]]; then
    log_error "Invalid mode '$MODE' (expected auto|static|python)"
    exit 1
fi

if [[ "$PREFIX_SET" == false ]]; then
    if [[ $EUID -eq 0 ]]; then
        PREFIX="$DEFAULT_PREFIX"
    else
        PREFIX="$DEFAULT_PREFIX_USER"
    fi
fi

if [[ "$PREFIX" == "/usr/local" ]] || [[ "$PREFIX" == /usr/* ]]; then
    if [[ $EUID -ne 0 ]]; then
        log_error "Installation to ${PREFIX} requires root privileges."
        log_info "Try: sudo ./install-static.sh"
        log_info "Or use user installation: ./install-static.sh --prefix ~/.local"
        exit 1
    fi
fi

if [[ ! -d "$PF_RUNNER_FULL_DIR" ]]; then
    log_error "Missing source directory: $PF_RUNNER_FULL_DIR"
    exit 1
fi

build_static_if_needed() {
    if [[ -f "$STATIC_EXEC" ]]; then
        return 0
    fi
    if [[ "$BUILD_STATIC_IF_MISSING" != true ]]; then
        return 1
    fi
    log_info "pf-static not found; building via Makefile..."
    make -C "$PF_RUNNER_FULL_DIR" build-static
    [[ -f "$STATIC_EXEC" ]]
}

INSTALL_MODE=""
case "$MODE" in
    static)
        if ! build_static_if_needed; then
            log_error "Static binary required but not found: $STATIC_EXEC"
            log_info "Build it with: (cd pf-runner-full && make build-static)"
            log_info "Or rerun with: --build-static-if-missing"
            exit 1
        fi
        INSTALL_MODE="static"
        ;;
    python)
        INSTALL_MODE="python"
        ;;
    auto)
        if build_static_if_needed; then
            INSTALL_MODE="static"
        else
            INSTALL_MODE="python"
            log_warning "pf-static not found; falling back to Python wrapper mode."
        fi
        ;;
esac

BIN_DIR="${PREFIX}/bin"
LIB_DIR="${PREFIX}/lib/pf-runner"
mkdir -p "$BIN_DIR"

install_static_mode() {
    log_info "Installing static binary to ${BIN_DIR}/pf"
    install -m 0755 "$STATIC_EXEC" "${BIN_DIR}/pf"
    log_success "Installed static pf executable"
}

install_python_mode() {
    log_info "Installing Python runtime files to ${LIB_DIR}"
    mkdir -p "$LIB_DIR"

    shopt -s nullglob
    local py_files=("${PF_RUNNER_FULL_DIR}"/*.py)
    shopt -u nullglob
    if [[ ${#py_files[@]} -eq 0 ]]; then
        log_error "No Python source files found in ${PF_RUNNER_FULL_DIR}"
        exit 1
    fi
    cp "${py_files[@]}" "$LIB_DIR/"

    if [[ ! -f "${PF_RUNNER_FULL_DIR}/pf.lark" ]]; then
        log_error "Required file missing: ${PF_RUNNER_FULL_DIR}/pf.lark"
        exit 1
    fi
    cp "${PF_RUNNER_FULL_DIR}/pf.lark" "$LIB_DIR/"

    if [[ -d "${PF_RUNNER_FULL_DIR}/pf-files" ]]; then
        cp -r "${PF_RUNNER_FULL_DIR}/pf-files" "$LIB_DIR/"
    fi

    if [[ -d "${PF_RUNNER_FULL_DIR}/pf_runner.egg-info" ]]; then
        cp -r "${PF_RUNNER_FULL_DIR}/pf_runner.egg-info" "$LIB_DIR/"
    fi

    cat > "${BIN_DIR}/pf" << 'EOF'
#!/usr/bin/env python3
import sys
from pathlib import Path

lib_dir = Path(__file__).parent.parent / "lib" / "pf-runner"
sys.path.insert(0, str(lib_dir))

try:
    import pf_main
except ImportError as exc:
    print(f"ERROR: Could not import pf_main from {lib_dir}", file=sys.stderr)
    print(f"Import error: {exc}", file=sys.stderr)
    print("", file=sys.stderr)
    print("Install runtime dependencies, for example:", file=sys.stderr)
    print("  pip install 'lark>=1.1.0' 'fabric>=3.2,<4' 'typer>=0.12'", file=sys.stderr)
    sys.exit(1)

exit_code = pf_main.main(sys.argv[1:])
sys.exit(exit_code if exit_code is not None else 0)
EOF
    chmod +x "${BIN_DIR}/pf"
    log_success "Installed Python wrapper executable"
}

run_verification() {
    local pf_bin="${BIN_DIR}/pf"
    log_info "Running post-install verification..."

    "$pf_bin" -V >/dev/null
    if [[ -f "$TEST_PF" ]]; then
        "$pf_bin" -f "$TEST_PF" list >/dev/null
        "$pf_bin" -f "$TEST_PF" smoke >/dev/null
    fi

    log_success "Verification passed"
}

echo -e "${BLUE}pf installer${NC}"
echo "============"
echo ""
log_info "Prefix: ${PREFIX}"
log_info "Mode: ${INSTALL_MODE}"

if [[ "$INSTALL_MODE" == "static" ]]; then
    install_static_mode
else
    install_python_mode
fi

if [[ "$VERIFY_INSTALL" == true ]]; then
    run_verification
else
    log_info "Skipping verification (use --verify to enable)."
fi

if [[ ":$PATH:" != *":${BIN_DIR}:"* ]]; then
    log_warning "The installation directory ${BIN_DIR} is not in your PATH."
    echo "Add this to your shell profile:"
    echo "  export PATH=\"${BIN_DIR}:\$PATH\""
else
    log_success "Installation directory already in PATH"
fi

echo ""
log_success "Installation completed."
log_info "Next steps:"
echo "  1. pf --version"
if [[ -f "$TEST_PF" ]]; then
    echo "  2. pf ${TEST_PF} list"
else
    echo "  2. pf list"
fi
