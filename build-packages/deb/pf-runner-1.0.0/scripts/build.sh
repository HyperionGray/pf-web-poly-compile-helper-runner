#!/usr/bin/env bash
# Build script for bish (bash with enhanced features)
# Handles dependency checking and installation

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a library is available for linking
check_library() {
    local lib_name="$1"
    local lib_flag="$2"
    
    log_info "Checking for library: $lib_name"
    
    # Try to compile a simple test program
    cat > /tmp/test_${lib_name}.c << EOF
int main() { return 0; }
EOF
    
    if gcc -o /tmp/test_${lib_name} /tmp/test_${lib_name}.c ${lib_flag} >/dev/null 2>&1; then
        log_success "Library $lib_name is available"
        rm -f /tmp/test_${lib_name} /tmp/test_${lib_name}.c
        return 0
    else
        log_error "Library $lib_name is not available"
        rm -f /tmp/test_${lib_name} /tmp/test_${lib_name}.c
        return 1
    fi
}

# Function to install SQLite3 development libraries
install_sqlite3_dev() {
    log_info "Installing SQLite3 development libraries..."
    
    if command_exists apt-get; then
        # Debian/Ubuntu
        log_info "Detected Debian/Ubuntu system"
        if [[ $EUID -eq 0 ]]; then
            apt-get update && apt-get install -y libsqlite3-dev
        else
            sudo apt-get update && sudo apt-get install -y libsqlite3-dev
        fi
    elif command_exists yum; then
        # RHEL/CentOS/Fedora (older)
        log_info "Detected RHEL/CentOS system"
        if [[ $EUID -eq 0 ]]; then
            yum install -y sqlite-devel
        else
            sudo yum install -y sqlite-devel
        fi
    elif command_exists dnf; then
        # Fedora (newer)
        log_info "Detected Fedora system"
        if [[ $EUID -eq 0 ]]; then
            dnf install -y sqlite-devel
        else
            sudo dnf install -y sqlite-devel
        fi
    elif command_exists pacman; then
        # Arch Linux
        log_info "Detected Arch Linux system"
        if [[ $EUID -eq 0 ]]; then
            pacman -S --noconfirm sqlite
        else
            sudo pacman -S --noconfirm sqlite
        fi
    elif command_exists zypper; then
        # openSUSE
        log_info "Detected openSUSE system"
        if [[ $EUID -eq 0 ]]; then
            zypper install -y sqlite3-devel
        else
            sudo zypper install -y sqlite3-devel
        fi
    elif command_exists apk; then
        # Alpine Linux
        log_info "Detected Alpine Linux system"
        if [[ $EUID -eq 0 ]]; then
            apk add --no-cache sqlite-dev
        else
            sudo apk add --no-cache sqlite-dev
        fi
    else
        log_error "Unknown package manager. Please install SQLite3 development libraries manually."
        log_info "Common package names:"
        log_info "  - Debian/Ubuntu: libsqlite3-dev"
        log_info "  - RHEL/CentOS/Fedora: sqlite-devel"
        log_info "  - Arch Linux: sqlite"
        log_info "  - openSUSE: sqlite3-devel"
        log_info "  - Alpine: sqlite-dev"
        return 1
    fi
}

# Function to check and install build dependencies
check_dependencies() {
    log_info "Checking build dependencies..."
    
    local missing_deps=()
    
    # Check for essential build tools
    if ! command_exists gcc; then
        missing_deps+=("gcc")
    fi
    
    if ! command_exists make; then
        missing_deps+=("make")
    fi
    
    # Check for SQLite3 library
    if ! check_library "sqlite3" "-lsqlite3"; then
        log_warning "SQLite3 development library not found"
        log_info "Attempting to install SQLite3 development libraries..."
        
        if install_sqlite3_dev; then
            log_success "SQLite3 development libraries installed"
            # Verify installation
            if ! check_library "sqlite3" "-lsqlite3"; then
                log_error "SQLite3 library still not available after installation"
                return 1
            fi
        else
            log_error "Failed to install SQLite3 development libraries"
            return 1
        fi
    fi
    
    # Check for other common libraries that might be needed
    local other_libs=("readline" "history" "dl")
    for lib in "${other_libs[@]}"; do
        if ! check_library "$lib" "-l$lib"; then
            log_warning "Library $lib not found, but continuing..."
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing build dependencies: ${missing_deps[*]}"
        log_info "Please install the missing dependencies and try again"
        return 1
    fi
    
    log_success "All dependencies are available"
    return 0
}

# Function to find and build the project
build_project() {
    log_info "Looking for build configuration..."
    
    # Look for Makefile in current directory
    if [[ -f "Makefile" ]]; then
        log_info "Found Makefile in current directory"
        log_info "Running make..."
        make
        return $?
    fi
    
    # Look for Makefile in subdirectories
    local makefiles=($(find . -name "Makefile" -type f | head -5))
    
    if [[ ${#makefiles[@]} -gt 0 ]]; then
        log_info "Found Makefiles in subdirectories:"
        for makefile in "${makefiles[@]}"; do
            log_info "  - $makefile"
        done
        
        # Ask user which one to use or try the first one
        local makefile_dir=$(dirname "${makefiles[0]}")
        log_info "Using Makefile in: $makefile_dir"
        
        cd "$makefile_dir"
        make
        return $?
    fi
    
    # Look for source files that might need compilation
    local c_files=($(find . -name "*.c" -type f | head -10))
    
    if [[ ${#c_files[@]} -gt 0 ]]; then
        log_info "Found C source files, but no Makefile"
        log_info "This build script cannot automatically compile without a Makefile"
        log_info "Found source files:"
        for c_file in "${c_files[@]}"; do
            log_info "  - $c_file"
        done
        log_error "Please create a Makefile or use a different build method"
        return 1
    fi
    
    # No build files found
    log_error "No Makefile or source files found"
    log_info "This appears to be a Python project (pf-runner)"
    log_info "The build error you encountered might be from a different context"
    log_info ""
    log_info "If you're trying to build the pf-runner project, use:"
    log_info "  cd pf-runner && python3 setup.py build"
    log_info ""
    log_info "If you're trying to build a different project, make sure you're in the correct directory"
    
    return 1
}

# Main function
main() {
    log_info "Starting build process..."
    log_info "Working directory: $(pwd)"
    
    # Parse command line arguments
    local version=""
    while [[ $# -gt 0 ]]; do
        case $1 in
            --version=*)
                version="${1#*=}"
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [--version=VERSION]"
                echo ""
                echo "Build script for bish (bash with enhanced features)"
                echo ""
                echo "Options:"
                echo "  --version=VERSION  Set build version"
                echo "  --help, -h         Show this help message"
                echo ""
                echo "This script will:"
                echo "  1. Check for build dependencies"
                echo "  2. Install missing SQLite3 development libraries"
                echo "  3. Build the project using available Makefile"
                exit 0
                ;;
            *)
                log_warning "Unknown option: $1"
                shift
                ;;
        esac
    done
    
    if [[ -n "$version" ]]; then
        log_info "Build version: $version"
    fi
    
    # Check dependencies
    if ! check_dependencies; then
        log_error "Dependency check failed"
        exit 1
    fi
    
    # Build the project
    if build_project; then
        log_success "Build completed successfully"
        exit 0
    else
        log_error "Build failed"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"