#!/usr/bin/env bash
# Native-only installer for pf-runner and bundled tasks (container paths deprecated).

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_PREFIX_ROOT="/usr/local"
DEFAULT_PREFIX_USER="${HOME}/.local"

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

PREFIX=""
SKIP_DEPS=false
PF_FILES_DIR=""

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --prefix) PREFIX="$2"; shift 2 ;;
      --prefix=*) PREFIX="${1#*=}"; shift ;;
      --skip-deps) SKIP_DEPS=true; shift ;;
      --help|-h) usage; exit 0 ;;
      --mode|--mode=*) warn "Container/package modes deprecated; proceeding with native install"; [[ "$1" == --mode ]] && shift 2 || shift ;;
      --container|--runtime|--image) warn "Container install flags are deprecated; ignoring $1"; shift 2 ;;
      --container=*|--runtime=*|--image=*) warn "Container install flags are deprecated; ignoring $1"; shift ;;
      *) warn "Ignoring unknown option: $1"; shift ;;
    esac
  done
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

set_defaults() {
  if [[ -z "$PREFIX" ]]; then
    if [[ "$(id -u 2>/dev/null || echo 1)" -eq 0 ]]; then
      PREFIX="$DEFAULT_PREFIX_ROOT"
    else
      PREFIX="$DEFAULT_PREFIX_USER"
    fi
  fi
  PREFIX="$(abs_path "$PREFIX")"
}

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

ensure_permissions() {
  if [[ "$PREFIX" == /usr* ]] && [[ "$(id -u 2>/dev/null || echo 1)" -ne 0 ]]; then
    die "Installing to $PREFIX requires root. Try: sudo ./install.sh --prefix ~/.local"
  fi
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
  rsync "${args[@]}" "${src}/" "${dest}/"
}

copy_item_follow() {
  local src="$1" dest="$2"
  [[ -e "$src" ]] || return 0
  mkdir -p "$dest"
  rsync -aL "$src" "$dest/"
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
  local pf_files="${PF_FILES_DIR:-${PREFIX}/lib/pf-files}"
  log "Installing wrapper to ${PREFIX}/bin/pf"
  cat > "${PREFIX}/bin/pf" <<EOF
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd -P)"
LIB_DIR="\$(cd "\${SCRIPT_DIR}/../lib/pf-runner" && pwd -P)"
VENV_PY="\${SCRIPT_DIR}/../lib/pf-runner-venv/bin/python3"
PF_FILES_DIR="${pf_files}"
DEFAULT_PFY="\${PF_FILES_DIR}/Pfyfile.pf"

if [[ -z "\${PFY_FILE:-}" && -f "\${DEFAULT_PFY}" ]]; then
  export PFY_FILE="\${DEFAULT_PFY}"
  export PFY_ROOT="\${PF_FILES_DIR}"
fi

if [[ -x "\${VENV_PY}" ]]; then
  exec "\${VENV_PY}" "\${LIB_DIR}/pf_main.py" "\$@"
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 "\${LIB_DIR}/pf_main.py" "\$@"
fi

echo "python3 is required to run pf (missing in PATH)." >&2
exit 1
EOF
  chmod +x "${PREFIX}/bin/pf"
}

validate_install() {
  log "Validating installation"
  [[ -x "${PREFIX}/bin/pf" ]] || die "pf launcher missing"
  "${PREFIX}/bin/pf" --help >/dev/null 2>&1 || die "pf --help failed"
  log "pf installed successfully to ${PREFIX}"
  if [[ "$PREFIX" != /usr* ]]; then
    warn "Add ${PREFIX}/bin to your PATH (e.g. export PATH=\"${PREFIX}/bin:$PATH\")"
  fi
}

parse_args "$@"
set_defaults
PF_FILES_DIR="${PREFIX}/lib/pf-files"
ensure_permissions
install_system_deps
ensure_prereqs
setup_python_env
copy_project
write_wrapper
validate_install

log "Native installation complete (container modes deprecated)."
