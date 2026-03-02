#!/usr/bin/env bash
# build-packages.sh - Build Debian packages for pf-runner
# Note: RPM and Arch package support has been deprecated
# See bak/installers/README.md for more information

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build-packages"
VERSION="1.0.0"
RELEASE="1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Utility functions
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

# Help function
show_help() {
    cat << EOF
pf-runner Package Builder

USAGE:
    ./build-packages.sh [OPTIONS]

OPTIONS:
    --version VERSION    Package version (default: $VERSION)
    --release RELEASE    Package release (default: $RELEASE)
    --build-dir DIR      Build directory (default: $BUILD_DIR)
    --clean              Clean build directory before building
    --install            Install packages after building (requires sudo)
    --help, -h           Show this help message

EXAMPLES:
    # Build Debian packages
    ./build-packages.sh

    # Build and install Debian packages
    ./build-packages.sh --install

    # Clean build and build packages
    ./build-packages.sh --clean

REQUIREMENTS:
    debuild, dpkg-buildpackage (install with: sudo apt-get install dpkg-dev)

NOTE:
    RPM and Arch package support has been deprecated. This script now only
    builds Debian packages. See bak/installers/README.md for more information.

EOF
}

# Parse command line arguments
CLEAN=false
INSTALL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            VERSION="$2"
            shift 2
            ;;
        --version=*)
            VERSION="${1#*=}"
            shift
            ;;
        --release)
            RELEASE="$2"
            shift 2
            ;;
        --release=*)
            RELEASE="${1#*=}"
            shift
            ;;
        --build-dir)
            BUILD_DIR="$2"
            shift 2
            ;;
        --build-dir=*)
            BUILD_DIR="${1#*=}"
            shift
            ;;
        --clean)
            CLEAN=true
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
        deb)
            # Accept 'deb' for backward compatibility, but it's now the default
            shift
            ;;
        rpm|arch|all)
            log_error "Format '$1' is no longer supported. Only .deb packages are built."
            log_error "See bak/installers/README.md for more information."
            exit 1
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Clean build directory if requested
if [[ "$CLEAN" == true ]]; then
    log_info "Cleaning build directory: $BUILD_DIR"
    rm -rf "$BUILD_DIR"
fi

# Create build directory
mkdir -p "$BUILD_DIR"

# Create source tarball
create_source_tarball() {
    local tarball_name="pf-runner-${VERSION}.tar.gz"
    local tarball_path="${BUILD_DIR}/${tarball_name}"
    
    log_info "Creating source tarball: $tarball_name"
    
    # Create temporary directory for source
    local temp_dir="${BUILD_DIR}/pf-runner-${VERSION}"
    mkdir -p "$temp_dir"
    
    # Copy source files (exclude build directories and git)
    rsync -av \
        --exclude='.git*' \
        --exclude='build*' \
        --exclude='*.deb' \
        --exclude='*.rpm' \
        --exclude='*.pkg.tar.*' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        "${SCRIPT_DIR}/" "$temp_dir/"
    
    # Create tarball
    cd "$BUILD_DIR"
    tar -czf "$tarball_name" "pf-runner-${VERSION}/"
    
    log_success "Source tarball created: $tarball_path"
    echo "$tarball_path"
}

# Build Debian packages
build_deb() {
    log_info "Building Debian packages..."
    
    # Check for required tools
    if ! command -v dpkg-buildpackage >/dev/null 2>&1; then
        log_error "dpkg-buildpackage not found. Install with: sudo apt-get install dpkg-dev"
        return 1
    fi
    
    # Create build directory
    local deb_dir="${BUILD_DIR}/deb"
    mkdir -p "$deb_dir"
    
    # Extract source
    cd "$deb_dir"
    tar -xzf "${BUILD_DIR}/pf-runner-${VERSION}.tar.gz"
    cd "pf-runner-${VERSION}"
    
    # Update changelog with current date
    sed -i "s/\$(date -R)/$(date -R)/" debian/changelog
    
    # Build packages
    log_info "Running dpkg-buildpackage..."
    dpkg-buildpackage -us -uc -b
    
    # Move packages to build directory
    mv ../*.deb "$deb_dir/"
    
    log_success "Debian packages built in: $deb_dir"
    ls -la "$deb_dir"/*.deb
}

# RPM and Arch package building has been deprecated
# See bak/installers/README.md for more information

# Install packages
install_packages() {
    if [[ "$INSTALL" != true ]]; then
        return 0
    fi
    
    log_info "Installing Debian packages..."
    
    if ! command -v apt-get >/dev/null 2>&1; then
        log_error "apt-get not found. This script only supports Debian/Ubuntu systems."
        log_error "For other systems, use the static executable installer: ./install-static.sh"
        return 1
    fi
    
    sudo dpkg -i "${BUILD_DIR}/deb"/*.deb || true
    sudo apt-get install -f -y  # Fix any dependency issues
    
    log_success "Packages installed successfully!"
}

# Main execution
main() {
    echo -e "${BLUE}pf-runner Debian Package Builder${NC}"
    echo "=================================="
    echo ""
    
    log_info "Building Debian packages"
    log_info "Version: $VERSION-$RELEASE"
    log_info "Build directory: $BUILD_DIR"
    echo ""
    
    # Create source tarball
    create_source_tarball
    
    # Build Debian packages
    build_deb
    echo ""
    
    # Install packages if requested
    install_packages
    
    echo ""
    log_success "🎉 Package building completed successfully!"
    echo ""
    log_info "Built packages:"
    find "$BUILD_DIR" -name "*.deb" | sort
    echo ""
    
    if [[ "$INSTALL" != true ]]; then
        log_info "To install packages, run with --install flag or use:"
        echo "  sudo dpkg -i build-packages/deb/*.deb && sudo apt-get install -f"
    fi
}

# Run main function
main "$@"