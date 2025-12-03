#!/usr/bin/env bash
# distro-extract.sh - Extract installed package files to output directory
#
# This script is used inside distro containers to:
# 1. Install a package using the native package manager
# 2. Extract the installed files to /output for host access
#
# Usage:
#   distro-extract <package-name> [additional-packages...]

set -euo pipefail

# Detect package manager
detect_package_manager() {
    if command -v dnf &>/dev/null; then
        echo "dnf"
    elif command -v yum &>/dev/null; then
        echo "yum"
    elif command -v pacman &>/dev/null; then
        echo "pacman"
    elif command -v zypper &>/dev/null; then
        echo "zypper"
    elif command -v apt-get &>/dev/null; then
        echo "apt"
    else
        echo "unknown"
    fi
}

# Install package using the appropriate package manager
install_package() {
    local pkg_manager="$1"
    shift
    local packages="$@"

    case "$pkg_manager" in
        dnf|yum)
            sudo "$pkg_manager" install -y $packages
            ;;
        pacman)
            sudo pacman -S --noconfirm $packages
            ;;
        zypper)
            sudo zypper --non-interactive install -y $packages
            ;;
        apt)
            sudo apt-get update && sudo apt-get install -y $packages
            ;;
        *)
            echo "ERROR: Unknown package manager: $pkg_manager"
            exit 1
            ;;
    esac
}

# Get list of files installed by a package
get_package_files() {
    local pkg_manager="$1"
    local package="$2"

    case "$pkg_manager" in
        dnf|yum)
            rpm -ql "$package" 2>/dev/null || true
            ;;
        pacman)
            pacman -Ql "$package" 2>/dev/null | awk '{print $2}' || true
            ;;
        zypper)
            rpm -ql "$package" 2>/dev/null || true
            ;;
        apt)
            dpkg -L "$package" 2>/dev/null || true
            ;;
        *)
            echo "ERROR: Unknown package manager: $pkg_manager"
            exit 1
            ;;
    esac
}

# Copy files to output directory
copy_to_output() {
    local file="$1"
    local output_base="/output"

    # Skip if not a file or doesn't exist
    [[ -f "$file" ]] || return 0

    # Determine target directory based on file location
    local target_dir
    if [[ "$file" == /usr/bin/* ]] || [[ "$file" == /bin/* ]]; then
        target_dir="$output_base/bin"
    elif [[ "$file" == /usr/sbin/* ]] || [[ "$file" == /sbin/* ]]; then
        target_dir="$output_base/bin"
    elif [[ "$file" == /usr/lib/* ]] || [[ "$file" == /lib/* ]] || [[ "$file" == /usr/lib64/* ]]; then
        target_dir="$output_base/lib"
    elif [[ "$file" == /usr/share/* ]]; then
        target_dir="$output_base/share"
    elif [[ "$file" == /etc/* ]]; then
        target_dir="$output_base/etc"
    else
        # Preserve full path for other files
        target_dir="$output_base/other$(dirname "$file")"
    fi

    mkdir -p "$target_dir"
    cp -a "$file" "$target_dir/" 2>/dev/null || true
}

# Main extraction function
extract_package() {
    local pkg_manager="$1"
    local package="$2"

    echo "Extracting files for package: $package"
    
    local files
    files=$(get_package_files "$pkg_manager" "$package")
    
    local count=0
    while IFS= read -r file; do
        [[ -z "$file" ]] && continue
        copy_to_output "$file"
        ((count++)) || true
    done <<< "$files"
    
    echo "Extracted $count files for $package"
}

# Main
main() {
    if [[ $# -lt 1 ]]; then
        echo "Usage: distro-extract <package-name> [additional-packages...]"
        echo ""
        echo "Installs packages and extracts their files to /output"
        exit 1
    fi

    local pkg_manager
    pkg_manager=$(detect_package_manager)
    echo "Detected package manager: $pkg_manager"

    # Install all packages first
    echo "Installing packages: $@"
    install_package "$pkg_manager" "$@"

    # Then extract files for each package
    for package in "$@"; do
        extract_package "$pkg_manager" "$package"
    done

    echo ""
    echo "Extraction complete. Files are in /output/"
    ls -la /output/
}

main "$@"
