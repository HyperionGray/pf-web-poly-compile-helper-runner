#!/usr/bin/env bash
# build-packages.sh - Build native packages for pf-runner
# Supports: deb (Debian/Ubuntu), rpm (Red Hat/Fedora), pkg.tar.zst (Arch)

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
    ./build-packages.sh [OPTIONS] [FORMATS...]

OPTIONS:
    --version VERSION    Package version (default: $VERSION)
    --release RELEASE    Package release (default: $RELEASE)
    --build-dir DIR      Build directory (default: $BUILD_DIR)
    --clean              Clean build directory before building
    --install            Install packages after building (requires sudo)
    --help, -h           Show this help message

FORMATS:
    deb                  Build Debian/Ubuntu packages
    rpm                  Build Red Hat/Fedora packages  
    arch                 Build Arch Linux packages
    all                  Build all supported formats (default)

EXAMPLES:
    # Build all package formats
    ./build-packages.sh

    # Build only Debian packages
    ./build-packages.sh deb

    # Build and install Debian packages
    ./build-packages.sh --install deb

    # Clean build and build all formats
    ./build-packages.sh --clean all

REQUIREMENTS:
    For deb: debuild, dpkg-buildpackage
    For rpm: rpmbuild, rpm-build
    For arch: makepkg, pacman

EOF
}

# Parse command line arguments
FORMATS=()
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
        deb|rpm|arch|all)
            FORMATS+=("$1")
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Default to all formats if none specified
if [[ ${#FORMATS[@]} -eq 0 ]]; then
    FORMATS=("all")
fi

# Expand "all" format
if [[ " ${FORMATS[*]} " =~ " all " ]]; then
    FORMATS=("deb" "rpm" "arch")
fi

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

# Build RPM packages
build_rpm() {
    log_info "Building RPM packages..."
    
    # Check for required tools
    if ! command -v rpmbuild >/dev/null 2>&1; then
        log_error "rpmbuild not found. Install with: sudo dnf install rpm-build"
        return 1
    fi
    
    # Create RPM build directories
    local rpm_dir="${BUILD_DIR}/rpm"
    mkdir -p "$rpm_dir"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
    
    # Copy spec file and source
    cp "${SCRIPT_DIR}/pf-runner.spec" "$rpm_dir/SPECS/"
    cp "${BUILD_DIR}/pf-runner-${VERSION}.tar.gz" "$rpm_dir/SOURCES/"
    
    # Update spec file with current date
    sed -i "s/\$(date \"+%a %b %d %Y\")/$(date "+%a %b %d %Y")/" "$rpm_dir/SPECS/pf-runner.spec"
    
    # Build packages
    log_info "Running rpmbuild..."
    rpmbuild --define "_topdir $rpm_dir" -ba "$rpm_dir/SPECS/pf-runner.spec"
    
    # Move packages to build directory
    find "$rpm_dir/RPMS" -name "*.rpm" -exec mv {} "$rpm_dir/" \;
    find "$rpm_dir/SRPMS" -name "*.rpm" -exec mv {} "$rpm_dir/" \;
    
    log_success "RPM packages built in: $rpm_dir"
    ls -la "$rpm_dir"/*.rpm
}

# Build Arch packages
build_arch() {
    log_info "Building Arch Linux packages..."
    
    # Check for required tools
    if ! command -v makepkg >/dev/null 2>&1; then
        log_error "makepkg not found. Install with: sudo pacman -S base-devel"
        return 1
    fi
    
    # Create build directory
    local arch_dir="${BUILD_DIR}/arch"
    mkdir -p "$arch_dir"
    
    # Copy PKGBUILD and source
    cp "${SCRIPT_DIR}/PKGBUILD" "$arch_dir/"
    cp "${BUILD_DIR}/pf-runner-${VERSION}.tar.gz" "$arch_dir/"
    
    # Build packages
    cd "$arch_dir"
    log_info "Running makepkg..."
    makepkg -sf --noconfirm
    
    log_success "Arch packages built in: $arch_dir"
    ls -la "$arch_dir"/*.pkg.tar.*
}

# Install packages
install_packages() {
    if [[ "$INSTALL" != true ]]; then
        return 0
    fi
    
    log_info "Installing packages..."
    
    # Detect package manager and install appropriate packages
    if command -v apt-get >/dev/null 2>&1 && [[ " ${FORMATS[*]} " =~ " deb " ]]; then
        log_info "Installing Debian packages..."
        sudo dpkg -i "${BUILD_DIR}/deb"/*.deb || true
        sudo apt-get install -f -y  # Fix any dependency issues
        
    elif command -v dnf >/dev/null 2>&1 && [[ " ${FORMATS[*]} " =~ " rpm " ]]; then
        log_info "Installing RPM packages..."
        sudo dnf install -y "${BUILD_DIR}/rpm"/*.rpm
        
    elif command -v yum >/dev/null 2>&1 && [[ " ${FORMATS[*]} " =~ " rpm " ]]; then
        log_info "Installing RPM packages..."
        sudo yum install -y "${BUILD_DIR}/rpm"/*.rpm
        
    elif command -v pacman >/dev/null 2>&1 && [[ " ${FORMATS[*]} " =~ " arch " ]]; then
        log_info "Installing Arch packages..."
        sudo pacman -U --noconfirm "${BUILD_DIR}/arch"/*.pkg.tar.*
        
    else
        log_warning "No compatible package manager found for installation"
        return 1
    fi
    
    log_success "Packages installed successfully!"
}

# Main execution
main() {
    echo -e "${BLUE}pf-runner Package Builder${NC}"
    echo "========================="
    echo ""
    
    log_info "Building packages for formats: ${FORMATS[*]}"
    log_info "Version: $VERSION-$RELEASE"
    log_info "Build directory: $BUILD_DIR"
    echo ""
    
    # Create source tarball
    create_source_tarball
    
    # Build packages for each format
    for format in "${FORMATS[@]}"; do
        case "$format" in
            deb)
                build_deb
                ;;
            rpm)
                build_rpm
                ;;
            arch)
                build_arch
                ;;
            *)
                log_error "Unknown format: $format"
                exit 1
                ;;
        esac
        echo ""
    done
    
    # Install packages if requested
    install_packages
    
    echo ""
    log_success "🎉 Package building completed successfully!"
    echo ""
    log_info "Built packages:"
    find "$BUILD_DIR" -name "*.deb" -o -name "*.rpm" -o -name "*.pkg.tar.*" | sort
    echo ""
    
    if [[ "$INSTALL" != true ]]; then
        log_info "To install packages, run with --install flag or use your package manager:"
        echo "  Debian/Ubuntu: sudo dpkg -i build-packages/deb/*.deb && sudo apt-get install -f"
        echo "  Red Hat/Fedora: sudo dnf install build-packages/rpm/*.rpm"
        echo "  Arch Linux: sudo pacman -U build-packages/arch/*.pkg.tar.*"
    fi
}

# Run main function
main "$@"