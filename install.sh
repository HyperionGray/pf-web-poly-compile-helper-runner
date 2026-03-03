#!/usr/bin/env bash
# install.sh - Simple native installer for pf-runner base runner
# Usage: ./install.sh [--prefix PATH] [--skip-deps] [--help]

set -euo pipefail

# Configuration
DEFAULT_PREFIX="/usr/local"
DEFAULT_PREFIX_USER="${HOME}/.local"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PF_RUNNER_DIR="${SCRIPT_DIR}/pf-runner"

# ------------- logging -------------
if [[ -t 1 ]]; then
  RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; BLUE=$'\033[0;34m'; NC=$'\033[0m'
else
  RED=''; GREEN=''; YELLOW=''; BLUE=''; NC=''
fi
log()   { printf '%b\n' "${BLUE}[INFO]${NC} $*"; }
warn()  { printf '%b\n' "${YELLOW}[WARN]${NC} $*" >&2; }
error() { printf '%b\n' "${RED}[ERROR]${NC} $*" >&2; }
die()   { error "$*"; exit 1; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

run_as_root() {
  if [[ "$(id -u 2>/dev/null || echo 1)" -eq 0 ]]; then
    "$@"
  elif command_exists sudo; then
    sudo "$@"
  else
    die "This step requires root privileges: $*"
  fi
}

usage() {
  cat <<'USAGE'
pf-runner native installer (containers deprecated)

Usage: ./install.sh [--prefix PATH] [--skip-deps] [--help]

Options:
  --prefix PATH   Install prefix (/usr/local for root, ~/.local otherwise)
  --skip-deps     Skip OS package installation (python3/pip/rsync/build tools)
  --help, -h      Show this help message
USAGE
}

# Parse command line arguments
PREFIX=""
PREFIX_SET=false
SKIP_DEPS=false
SHOW_HELP=false
REPO_ROOT="${SCRIPT_DIR}"

while [[ $# -gt 0 ]]; do
    case $1 in
        --prefix)
            PREFIX="$2"
            PREFIX_SET=true
            shift 2
            ;;
        --prefix=*)
            PREFIX="${1#*=}"
            PREFIX_SET=true
            shift
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}" >&2
            SHOW_HELP=true
            shift
            ;;
    esac
done

# Help function
show_help() {
    cat << EOF
pf-runner Native Installation Script

USAGE:
    ./install.sh [OPTIONS]

OPTIONS:
    --prefix PATH     Install prefix
                      Default: ${DEFAULT_PREFIX} (system-wide, requires sudo)
                               ${DEFAULT_PREFIX_USER} (user install, no sudo)
    --skip-deps       Skip system dependency installation
    --help, -h        Show this help message

EXAMPLES:
    # System-wide install (requires sudo)
    sudo ./install.sh

    # User install (no sudo required)
    ./install.sh --prefix ~/.local

    # User install without installing system dependencies
    ./install.sh --prefix ~/.local --skip-deps

WHAT THIS SCRIPT DOES:
    1. Checks prerequisites (Python 3.8+, Git, pip)
    2. Installs system dependencies (optional)
    3. Sets up Python virtual environment (for user installs)
    4. Installs Python dependencies (lark, fabric, typer)
    5. Copies pf-runner files to installation directory
    6. Creates pf executable wrapper
    7. Installs shell completions (optional)
    8. Validates installation

EOF
}

abs_path() {
  local p="$1"
  if [[ "$p" == "~"* ]]; then p="${p/#\~/${HOME}}"; fi
  if command_exists python3; then
    python3 - "$p" <<'PY'
import os, sys
print(os.path.abspath(sys.argv[1]))
PY
  else
    [[ "$p" = /* ]] && printf '%s\n' "$p" || printf '%s\n' "$(pwd -P)/$p"
  fi
}

# Set default prefix
ensure_permissions() {
  if [[ "$PREFIX" == /usr* ]] && [[ "$(id -u 2>/dev/null || echo 1)" -ne 0 ]]; then
    die "Installing to $PREFIX requires root. Try: sudo ./install.sh or ./install.sh --prefix ~/.local"
  fi
}

# Detect operating system
detect_os() {
  local sys="$(uname -s 2>/dev/null || echo unknown)"
  case "$sys" in
    Linux)
      command_exists apt-get && { echo debian; return; }
      command_exists dnf && { echo rhel; return; }
      command_exists yum && { echo rhel; return; }
      command_exists pacman && { echo arch; return; }
      echo linux ;;
    Darwin) echo macos ;;
    *) echo unknown ;;
  esac
}

install_system_deps() {
  [[ "$SKIP_DEPS" == true ]] && { log "Skipping OS dependency install"; return; }
  case "$(detect_os)" in
    debian)
      run_as_root apt-get update
      run_as_root apt-get install -y python3 python3-venv python3-pip git build-essential rsync curl ;;
    rhel)
      if command_exists dnf; then
        run_as_root dnf install -y python3 python3-venv python3-pip git gcc gcc-c++ make rsync curl
      else
        run_as_root yum install -y python3 python3-venv python3-pip git gcc gcc-c++ make rsync curl
      fi ;;
    arch)
      run_as_root pacman -Sy --noconfirm python python-pip base-devel git rsync curl ;;
    macos)
      warn "macOS detected. Ensure Python 3.8+, pip, rsync, and build tools are installed." ;;
    *)
      warn "Unknown OS; dependency installation skipped." ;;
  esac
}

ensure_prereqs() {
  log "Checking prerequisites"
  command_exists python3 || die "python3 is required"
  command_exists git || die "git is required"
  command_exists rsync || die "rsync is required"
  python3 -m pip --version >/dev/null 2>&1 || die "pip is required"
  python3 - <<'PY' || die "Python 3.8+ is required"
import sys
sys.exit(0 if sys.version_info >= (3,8) else 1)
PY
}

setup_python_env() {
  log "Setting up Python environment"
  local venv=""
  if [[ "$PREFIX" == /usr* ]]; then
    venv=""
  else
    venv="$PREFIX/lib/pf-runner-venv"
    mkdir -p "$PREFIX/lib"
    python3 -m venv "$venv"
    # shellcheck disable=SC1091
    source "$venv/bin/activate"
    python3 -m pip install --upgrade pip
  fi
  python3 -m pip install --upgrade "fabric>=3.2,<4" "lark" "typer" "json5" "rich"
}

copy_dir_follow() {
  local src="$1" dest="$2" exclude="$3"
  [[ -d "$src" ]] || return 0
  mkdir -p "$dest"
  local args=(-aL --ignore-missing-args)
  [[ -n "$exclude" ]] && args+=(--exclude "$exclude")
  rsync "${args[@]}" "${src}/" "${dest}/" || true  # Ignore rsync errors for symlinks
}

copy_item_follow() {
  local src="$1" dest="$2"
  [[ -e "$src" ]] || return 0
  mkdir -p "$dest"
  rsync -aL "$src" "$dest/" || true  # Ignore rsync errors for symlinks
}

copy_project() {
  log "Copying project files..."
  local assets_root="${PF_FILES_DIR:-${PREFIX}/lib/pf-files}"

  mkdir -p "$PREFIX/lib/pf-runner" "$assets_root" "$assets_root/pf" "$PREFIX/bin"

  copy_dir_follow "$REPO_ROOT/pf-runner" "$PREFIX/lib/pf-runner" ""
  copy_dir_follow "$REPO_ROOT/pf" "$assets_root/pf" ""

  copy_item_follow "$REPO_ROOT/pf.config.json5" "$assets_root"
  copy_item_follow "$REPO_ROOT/Pfyfile.pf" "$assets_root"

  for dir in tools scripts demos containers web docs examples third-party; do
    if [[ "$dir" == "third-party" ]]; then
      copy_dir_follow "$REPO_ROOT/$dir" "$assets_root/$dir" "archive/**"
      continue
    fi
    if [[ "$dir" == "containers" ]]; then
      copy_dir_follow "$REPO_ROOT/$dir" "$assets_root/$dir" "deprecated/"
      continue
    fi
    copy_dir_follow "$REPO_ROOT/$dir" "$assets_root/$dir" ""
  done

  for file in docker-compose.yml docker-compose.gpu.yml podman-compose.yml podman-compose.gpu.yml tools-capabilities.json; do
    copy_item_follow "$REPO_ROOT/$file" "$assets_root"
  done
}

write_wrapper() {
  local venv_path=""
  if [[ "$PREFIX" != /usr* ]]; then
    venv_path="$PREFIX/lib/pf-runner-venv"
  fi
  
  log "Installing wrapper to ${PREFIX}/bin/pf"
  cat > "${PREFIX}/bin/pf" <<'WRAPPER_EOF'
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="$(dirname "$SCRIPT_DIR")"
PF_RUNNER="${PREFIX}/lib/pf-runner"
VENV_PATH="${PREFIX}/lib/pf-runner-venv"

# Activate venv if it exists
if [[ -d "$VENV_PATH" ]] && [[ -f "$VENV_PATH/bin/activate" ]]; then
    source "$VENV_PATH/bin/activate"
fi

# Run pf-runner
exec python3 "${PF_RUNNER}/pf_main.py" "$@"
WRAPPER_EOF
  
  chmod +x "${PREFIX}/bin/pf"
}

check_prerequisites() {
  log "Checking prerequisites..."
  ensure_prereqs
}

install_pf_runner() {
  log "Installing pf-runner files..."
  copy_project
  write_wrapper
}

install_completions() {
  log "Installing shell completions..."
  
  # Check if completions directory exists
  if [[ ! -d "${REPO_ROOT}/pf-runner/completions" ]]; then
    warn "Completions directory not found, skipping"
    return 0
  fi
  
  # Install bash completion
  if [[ -d "/etc/bash_completion.d" ]] && [[ "$PREFIX" == "/usr/local" || "$PREFIX" == "/usr"* ]]; then
    run_as_root cp "${REPO_ROOT}/pf-runner/completions/pf-completion.bash" "/etc/bash_completion.d/pf" 2>/dev/null || true
    log "Installed bash completion to /etc/bash_completion.d/pf"
  elif [[ -d "${HOME}/.local/share/bash-completion/completions" ]]; then
    mkdir -p "${HOME}/.local/share/bash-completion/completions"
    cp "${REPO_ROOT}/pf-runner/completions/pf-completion.bash" "${HOME}/.local/share/bash-completion/completions/pf" 2>/dev/null || true
    log "Installed bash completion to ~/.local/share/bash-completion/completions/pf"
  fi
  
  # Install zsh completion
  if [[ -d "/usr/local/share/zsh/site-functions" ]] && [[ "$PREFIX" == "/usr/local" || "$PREFIX" == "/usr"* ]]; then
    run_as_root cp "${REPO_ROOT}/pf-runner/completions/_pf" "/usr/local/share/zsh/site-functions/_pf" 2>/dev/null || true
    log "Installed zsh completion to /usr/local/share/zsh/site-functions/_pf"
  elif mkdir -p "${HOME}/.zsh/completions" 2>/dev/null; then
    cp "${REPO_ROOT}/pf-runner/completions/_pf" "${HOME}/.zsh/completions/_pf" 2>/dev/null || true
    log "Installed zsh completion to ~/.zsh/completions/_pf"
  fi
}

validate_installation() {
  log "Validating installation..."
  
  local pf_cmd="${PREFIX}/bin/pf"
  
  # Check if pf command exists and is executable
  if [[ ! -x "$pf_cmd" ]]; then
    error "pf command not found or not executable at $pf_cmd"
    return 1
  fi
  
  log "Installation validated successfully"
  return 0
}

update_path_info() {
  local bin_dir="${PREFIX}/bin"
  
  # Check if bin directory is in PATH
  if [[ ":$PATH:" != *":${bin_dir}:"* ]]; then
    warn "The installation directory ${bin_dir} is not in your PATH"
    log "Add the following to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
    echo ""
    echo "    export PATH=\"${bin_dir}:\$PATH\""
    echo ""
  fi
}

# Show help if requested
if [[ "$SHOW_HELP" == true ]]; then
  show_help
  exit 0
fi

# Set default prefix if not specified
if [[ "$PREFIX_SET" == false ]]; then
  if [[ $EUID -eq 0 ]]; then
    PREFIX="$DEFAULT_PREFIX"
  else
    PREFIX="$DEFAULT_PREFIX_USER"
  fi
fi

log "pf-runner Native Installer"
log "Installation prefix: $PREFIX"
echo ""

ensure_permissions
install_system_deps
ensure_prereqs
setup_python_env
copy_project
write_wrapper
install_completions
validate_installation

echo ""
log "Installation completed successfully!"
log "pf-runner installed to: ${PREFIX}/lib/pf-runner"
log "pf executable: ${PREFIX}/bin/pf"
echo ""
update_path_info
echo ""
log "Try: pf --version"
log "Try: pf list"
