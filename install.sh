#!/usr/bin/env bash
# install.sh - Compatibility installer entrypoint
# Routes to scripts/install.sh (native) or install-static.sh (static source install)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NATIVE_INSTALLER="${SCRIPT_DIR}/scripts/install.sh"
STATIC_INSTALLER="${SCRIPT_DIR}/install-static.sh"

MODE="native"
PASSTHROUGH_ARGS=()

show_help() {
    cat << EOF
pf-runner Installer Entry Point

USAGE:
    ./install.sh [--mode native|static] [installer options...]

MODES:
    native   Use scripts/install.sh (default)
    static   Use install-static.sh (source-file install, no build step)

EXAMPLES:
    ./install.sh --mode static --prefix ~/.local --verify
    ./install.sh --prefix ~/.local --skip-deps
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode)
            if [[ $# -lt 2 ]]; then
                echo "Error: --mode requires a value (native|static)" >&2
                exit 1
            fi
            MODE="$2"
            shift 2
            ;;
        --mode=*)
            MODE="${1#*=}"
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            PASSTHROUGH_ARGS+=("$1")
            shift
            ;;
    esac
done

case "$MODE" in
    native)
        if [[ ! -x "$NATIVE_INSTALLER" ]]; then
            echo "Error: native installer not found: $NATIVE_INSTALLER" >&2
            exit 1
        fi
        exec "$NATIVE_INSTALLER" "${PASSTHROUGH_ARGS[@]}"
        ;;
    static)
        if [[ ! -x "$STATIC_INSTALLER" ]]; then
            echo "Error: static installer not found: $STATIC_INSTALLER" >&2
            exit 1
        fi
        exec "$STATIC_INSTALLER" "${PASSTHROUGH_ARGS[@]}"
        ;;
    *)
        echo "Error: unknown mode '$MODE' (expected native|static)" >&2
        exit 1
        ;;
esac
