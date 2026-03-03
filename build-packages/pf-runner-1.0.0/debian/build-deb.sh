#!/usr/bin/env bash
# Build a .deb package for pf-runner
#
# Usage: ./build-deb.sh [version]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VERSION="${1:-1.0.0}"
PKG_NAME="pf-runner"
PKG_DIR="${SCRIPT_DIR}/build/${PKG_NAME}_${VERSION}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Clean previous build
log_info "Cleaning previous build..."
rm -rf "${SCRIPT_DIR}/build"
mkdir -p "${PKG_DIR}"

# Create directory structure
log_info "Creating package structure..."
mkdir -p "${PKG_DIR}/DEBIAN"
mkdir -p "${PKG_DIR}/usr/local/lib/pf-runner"
mkdir -p "${PKG_DIR}/usr/local/bin"

# Copy control file
log_info "Copying control files..."
sed "s/Version: .*/Version: ${VERSION}/" "${SCRIPT_DIR}/control" > "${PKG_DIR}/DEBIAN/control"
cp "${SCRIPT_DIR}/postinst" "${PKG_DIR}/DEBIAN/postinst"
chmod 755 "${PKG_DIR}/DEBIAN/postinst"

# Copy pf-runner files (exclude caches/build artifacts)
log_info "Copying pf-runner files..."
if command -v rsync >/dev/null 2>&1; then
    rsync -a \
        --exclude "__pycache__/" \
        --exclude "*.pyc" \
        --exclude "*.pyo" \
        --exclude "*.egg-info/" \
        --exclude ".pytest_cache/" \
        --exclude ".pf-venv/" \
        --exclude ".venv/" \
        --exclude "bak/" \
        "${REPO_ROOT}/pf-runner/" "${PKG_DIR}/usr/local/lib/pf-runner/"
else
    cp -r "${REPO_ROOT}/pf-runner"/* "${PKG_DIR}/usr/local/lib/pf-runner/"
    find "${PKG_DIR}/usr/local/lib/pf-runner" -type d -name "__pycache__" -prune -exec rm -rf {} + || true
    find "${PKG_DIR}/usr/local/lib/pf-runner" -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete || true
    rm -rf "${PKG_DIR}/usr/local/lib/pf-runner/bak" || true
fi

# Create pf wrapper
log_info "Creating pf executable..."
cat > "${PKG_DIR}/usr/local/bin/pf" << 'EOF'
#!/usr/bin/env bash
# pf - Wrapper script for pf-runner
exec /usr/local/lib/pf-runner/pf_main.py "$@"
EOF
chmod 755 "${PKG_DIR}/usr/local/bin/pf"

# Build the package
log_info "Building .deb package..."
dpkg-deb --build "${PKG_DIR}"

# The output deb file location
OUTPUT_DEB="${SCRIPT_DIR}/build/${PKG_NAME}_${VERSION}.deb"
log_success "Package built: ${OUTPUT_DEB}"

# Display package info
log_info "Package information:"
dpkg-deb --info "${OUTPUT_DEB}"

log_success "Done! To install: sudo dpkg -i ${OUTPUT_DEB}"
