#!/usr/bin/env bash
# Canonical package build entrypoint (Debian only)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="1.0.0"
INSTALL=false
FORMAT="deb"

show_help() {
    cat << EOF
pf-runner package builder

USAGE:
    ./deb/build-packages.sh [OPTIONS] [FORMAT]

OPTIONS:
    --version VERSION    Package version (default: $VERSION)
    --install            Install package after build (Debian only)
    --help, -h           Show this help message

FORMAT:
    deb                  Build Debian package (default)
    rpm                  Not currently supported

EXAMPLES:
    ./deb/build-packages.sh
    ./deb/build-packages.sh --version 1.0.1 deb
    ./deb/build-packages.sh --install
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --version)
            VERSION="$2"
            shift 2
            ;;
        --version=*)
            VERSION="${1#*=}"
            shift
            ;;
        --install)
            INSTALL=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        deb|rpm)
            FORMAT="$1"
            shift
            ;;
        *)
            echo "[ERROR] Unknown option: $1" >&2
            show_help
            exit 1
            ;;
    esac
done

if [[ "$FORMAT" == "rpm" ]]; then
    echo "[ERROR] RPM build is not implemented in the canonical installer flow yet." >&2
    echo "        Use Debian packaging for now: ./deb/build-packages.sh deb" >&2
    exit 1
fi

"${SCRIPT_DIR}/build-deb.sh" "$VERSION"

if [[ "$INSTALL" == true ]]; then
    DEB_PATH="${SCRIPT_DIR}/build/pf-runner_${VERSION}.deb"
    sudo dpkg -i "$DEB_PATH" || { sudo apt-get install -f -y && sudo dpkg -i "$DEB_PATH"; }
fi
