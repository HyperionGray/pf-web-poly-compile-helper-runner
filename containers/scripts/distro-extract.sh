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

# Run a command with root privileges, falling back to sudo or su when available.
run_as_root() {
    if [[ $(id -u) -eq 0 ]]; then
        "$@"
    elif command -v sudo &>/dev/null; then
        sudo "$@"
    elif command -v su &>/dev/null; then
        su -m root -c "$*"
    else
        echo "ERROR: need root privileges to run: $*" >&2
        echo "Install sudo in the image or run the container as root." >&2
        exit 1
    fi
}

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
    elif command -v pkg &>/dev/null; then
        echo "pkg"
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
    # Use "$@" to properly handle packages as separate arguments
    local -a packages=("$@")

    case "$pkg_manager" in
        dnf|yum)
            run_as_root "$pkg_manager" install -y "${packages[@]}"
            ;;
        pacman)
            run_as_root pacman -S --noconfirm "${packages[@]}"
            ;;
        zypper)
            run_as_root zypper --non-interactive install -y "${packages[@]}"
            ;;
        pkg)
            run_as_root env ASSUME_ALWAYS_YES=yes pkg install -y "${packages[@]}"
            ;;
        apt)
            run_as_root apt-get update
            run_as_root apt-get install -y "${packages[@]}"
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
        pkg)
            pkg info -l "$package" 2>/dev/null | awk '/^\// {print $1}' || true
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

# List installed packages (names only) for diffing dependency installs.
list_installed_packages() {
    local pkg_manager="$1"

    case "$pkg_manager" in
        dnf|yum|zypper)
            rpm -qa --qf '%{NAME}\n' | sort -u
            ;;
        pacman)
            pacman -Qq | sort -u
            ;;
        pkg)
            pkg query -a '%n' 2>/dev/null | sort -u
            ;;
        apt)
            dpkg-query -W -f='${Package}\n' | sort -u
            ;;
        *)
            echo ""
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
    elif [[ "$file" == /usr/lib/* ]] || [[ "$file" == /lib/* ]] || [[ "$file" == /usr/lib64/* ]] || [[ "$file" == /lib64/* ]]; then
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

# Extract multiple packages, skipping duplicates.
extract_packages() {
    local pkg_manager="$1"
    shift

    declare -A seen=()
    for package in "$@"; do
        [[ -z "${package}" ]] && continue
        if [[ -n "${seen[$package]:-}" ]]; then
            continue
        fi
        seen["$package"]=1
        extract_package "$pkg_manager" "$package"
    done
}

# Copy any runtime library dependencies discovered via ldd on extracted binaries.
copy_ldd_dependencies() {
    local bin
    while IFS= read -r bin; do
        [[ -x "$bin" ]] || continue
        ldd "$bin" 2>/dev/null | awk '{for (i=1;i<=NF;i++) if ($i ~ /^\//) print $i}' | while IFS= read -r dep; do
            [[ -f "$dep" ]] || continue
            copy_to_output "$dep"
        done || true
    done < <(find /output/bin -type f -perm -111 2>/dev/null)
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

    # Snapshot installed packages before install so we can extract deps too.
    local before_packages after_packages
    local -a new_packages combined_packages
    before_packages="$(list_installed_packages "$pkg_manager")"

    # Install all packages first
    echo "Installing packages: $@"
    install_package "$pkg_manager" "$@"

    # Compute newly added packages (dependencies included)
    after_packages="$(list_installed_packages "$pkg_manager")"
    mapfile -t new_packages < <(comm -13 <(printf '%s\n' "$before_packages") <(printf '%s\n' "$after_packages"))

    # Combine requested packages and new dependencies for extraction
    combined_packages=("$@")
    for pkg in "${new_packages[@]}"; do
        [[ -z "$pkg" ]] && continue
        combined_packages+=("$pkg")
    done

    echo "Extracting packages (requested + dependencies): ${combined_packages[*]}"
    extract_packages "$pkg_manager" "${combined_packages[@]}"

    echo "Capturing runtime library dependencies via ldd..."
    copy_ldd_dependencies

    echo ""
    echo "Extraction complete. Files are in /output/"
    ls -la /output/
}

main "$@"
