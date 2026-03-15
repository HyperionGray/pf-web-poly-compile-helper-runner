#!/usr/bin/env bash
# check-install-prereqs.sh - Validate local prerequisites for pf installers.

set -euo pipefail

REPORT_ONLY=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --report-only)
            REPORT_ONLY=true
            shift
            ;;
        --help|-h)
            cat <<'EOF'
Usage: check-install-prereqs.sh [--report-only]

Checks required and optional tools used by pf installer workflows.

Options:
  --report-only   Always exit 0 (useful for informational checks in CI/logs)
  --help, -h      Show this help message
EOF
            exit 0
            ;;
        *)
            echo "[ERR] Unknown option: $1" >&2
            exit 2
            ;;
    esac
done

detect_pkg_manager() {
    if command -v apt-get >/dev/null 2>&1; then
        echo "apt"
    elif command -v dnf >/dev/null 2>&1; then
        echo "dnf"
    elif command -v yum >/dev/null 2>&1; then
        echo "yum"
    elif command -v pacman >/dev/null 2>&1; then
        echo "pacman"
    elif command -v brew >/dev/null 2>&1; then
        echo "brew"
    else
        echo "unknown"
    fi
}

print_install_hint() {
    local pm="$1"
    echo ""
    echo "Suggested install command for missing basics:"
    case "$pm" in
        apt)
            echo "  sudo apt-get update && sudo apt-get install -y python3 python3-pip git curl build-essential"
            ;;
        dnf)
            echo "  sudo dnf install -y python3 python3-pip git curl gcc make"
            ;;
        yum)
            echo "  sudo yum install -y python3 python3-pip git curl gcc make"
            ;;
        pacman)
            echo "  sudo pacman -Sy --noconfirm python python-pip git curl base-devel"
            ;;
        brew)
            echo "  brew install python git curl"
            ;;
        *)
            echo "  Install Python 3.10+, pip, git, and curl using your system package manager."
            ;;
    esac
}

check_cmd() {
    local cmd="$1"
    if command -v "$cmd" >/dev/null 2>&1; then
        printf '[OK] %-12s %s\n' "$cmd" "$(command -v "$cmd")"
        return 0
    fi
    printf '[NO] %-12s not found\n' "$cmd"
    return 1
}

echo "========================================"
echo "PF Installer Prerequisite Check"
echo "========================================"
echo ""

missing_required=0
pkg_manager="$(detect_pkg_manager)"

echo "Detected package manager: ${pkg_manager}"
echo ""

echo "Required tools:"
check_cmd python3 || missing_required=$((missing_required + 1))
check_cmd git || missing_required=$((missing_required + 1))

if python3 -m pip --version >/dev/null 2>&1; then
    printf '[OK] %-12s %s\n' "pip" "$(python3 -m pip --version | awk '{print $1, $2}')"
else
    printf '[NO] %-12s python3 -m pip unavailable\n' "pip"
    missing_required=$((missing_required + 1))
fi

if python3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >/dev/null 2>&1; then
    printf '[OK] %-12s %s\n' "python>=3.10" "$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')"
else
    printf '[NO] %-12s %s\n' "python>=3.10" "python3 is too old"
    missing_required=$((missing_required + 1))
fi

echo ""
echo "Optional (recommended) tools:"
check_cmd curl || true
check_cmd gcc || true
check_cmd make || true

echo ""
if [[ "$missing_required" -eq 0 ]]; then
    echo "[OK] All required prerequisites are available."
    echo "Next steps:"
    echo "  pf install-prereq-check      # Re-run this check"
    echo "  pf install prefix=~/.local   # User-local install without sudo"
    echo "  pf install-smoke-test        # Validate installation path"
    exit 0
fi

echo "[ERR] Missing required prerequisites: ${missing_required}"
print_install_hint "$pkg_manager"

if [[ "$REPORT_ONLY" == "true" ]]; then
    echo ""
    echo "[WARN] --report-only enabled; returning success despite missing prerequisites."
    exit 0
fi

exit 1
