#!/usr/bin/env bash
# Build a .deb package for pf-runner using dpkg-buildpackage
#
# Usage: ./build-deb.sh [version]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VERSION="${1:-}"

log_info() {
    echo "[INFO] $1"
}

log_success() {
    echo "[OK] $1"
}

log_info "Cleaning previous build output..."
rm -rf "${SCRIPT_DIR}/build"
mkdir -p "${SCRIPT_DIR}/build"

log_info "Preparing changelog..."
if [[ -n "${VERSION}" ]]; then
    sed -i "1s/(.*)/(${VERSION}-1)/" "${REPO_ROOT}/debian/changelog"
fi
sed -i "s/\\$(date -R)/$(date -R)/" "${REPO_ROOT}/debian/changelog"

log_info "Building packages with dpkg-buildpackage..."
cd "${REPO_ROOT}"
dpkg-buildpackage -us -uc -b

log_info "Collecting .deb artifacts..."
ARTIFACT_DIR="$(dirname "${REPO_ROOT}")"
mv "${ARTIFACT_DIR}"/*.deb "${SCRIPT_DIR}/build/" 2>/dev/null || true
mv "${ARTIFACT_DIR}"/*.changes "${SCRIPT_DIR}/build/" 2>/dev/null || true
mv "${ARTIFACT_DIR}"/*.buildinfo "${SCRIPT_DIR}/build/" 2>/dev/null || true

log_success "Build complete. Artifacts in ${SCRIPT_DIR}/build"
ls -1 "${SCRIPT_DIR}/build"/*.deb 2>/dev/null || log_info "No .deb files found."
