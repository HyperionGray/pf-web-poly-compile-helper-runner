#!/usr/bin/env bash
set -euo pipefail

if declare -F __pf_installer_common_loaded >/dev/null 2>&1; then
  return 0
fi
__pf_installer_common_loaded() { :; }

command_exists() {
  local cmd="${1:-}"
  [[ -n "$cmd" ]] || return 1
  command -v "$cmd" >/dev/null 2>&1
}

pf_home_dir() {
  local uid=""
  uid="$(id -u 2>/dev/null || true)"

  if command_exists getent && [[ -n "$uid" ]]; then
    local entry=""
    entry="$(getent passwd "$uid" 2>/dev/null || true)"
    if [[ -n "$entry" ]]; then
      local home=""
      home="$(printf '%s' "$entry" | awk -F: '{print $6}')"
      if [[ -n "$home" ]]; then
        printf '%s\n' "$home"
        return 0
      fi
    fi
  fi

  if [[ -r /etc/passwd && -n "$uid" ]]; then
    local home=""
    home="$(awk -F: -v uid="$uid" '$3==uid{print $6; exit}' /etc/passwd 2>/dev/null || true)"
    if [[ -n "$home" ]]; then
      printf '%s\n' "$home"
      return 0
    fi
  fi

  printf '%s\n' "/tmp"
  return 0
}

pf_expand_path() {
  local p="${1:-}"
  if [[ "$p" == "~" ]]; then
    printf '%s\n' "$(pf_home_dir)"
    return 0
  fi
  if [[ "$p" == "~/"* ]]; then
    printf '%s\n' "$(pf_home_dir)/${p#\~/}"
    return 0
  fi
  printf '%s\n' "$p"
}

pf_abs_path() {
  local p
  p="$(pf_expand_path "${1:-}")"
  if command_exists python3; then
    python3 - "$p" <<'PY'
import os
import sys

print(os.path.abspath(sys.argv[1]))
PY
    return 0
  fi
  if [[ "$p" = /* ]]; then
    printf '%s\n' "$p"
  else
    printf '%s\n' "$(pwd -P)/$p"
  fi
}

pf_color_enabled() {
  if [[ ! -t 1 ]]; then
    return 1
  fi
  return 0
}

if pf_color_enabled; then
  RED=$'\033[0;31m'
  GREEN=$'\033[0;32m'
  YELLOW=$'\033[1;33m'
  BLUE=$'\033[0;34m'
  NC=$'\033[0m'
else
  RED=''
  GREEN=''
  YELLOW=''
  BLUE=''
  NC=''
fi

log_info() { printf '%b\n' "${BLUE}[INFO]${NC} $*"; }
log_success() { printf '%b\n' "${GREEN}[SUCCESS]${NC} $*"; }
log_warning() { printf '%b\n' "${YELLOW}[WARNING]${NC} $*" >&2; }
log_error() { printf '%b\n' "${RED}[ERROR]${NC} $*" >&2; }

die() {
  log_error "$*"
  exit 1
}

run_as_root() {
  if [[ "$(id -u 2>/dev/null || echo 1)" -eq 0 ]]; then
    "$@"
    return $?
  fi
  if command_exists sudo; then
    sudo "$@"
    return $?
  fi
  die "This step requires root privileges: $*"
}

detect_os() {
  local sys=""
  sys="$(uname -s 2>/dev/null || echo unknown)"
  case "$sys" in
    Linux)
      if command_exists apt-get; then echo debian; return 0; fi
      if command_exists dnf || command_exists yum; then echo rhel; return 0; fi
      if command_exists pacman; then echo arch; return 0; fi
      echo linux
      ;;
    Darwin)
      echo macos
      ;;
    *)
      echo unknown
      ;;
  esac
}

sed_in_place() {
  local expression="$1"
  local file="$2"

  if sed --version >/dev/null 2>&1; then
    sed -i "$expression" "$file"
    return 0
  fi
  sed -i '' "$expression" "$file"
}

rewrite_shebang() {
  local file="$1"
  local shebang="$2"

  command_exists python3 || die "python3 is required to rewrite shebangs"

  python3 - "$file" "$shebang" <<'PY'
import sys

path = sys.argv[1]
shebang = sys.argv[2]

with open(path, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.read().splitlines(True)

if lines:
    lines[0] = shebang + "\n"
else:
    lines = [shebang + "\n"]

with open(path, "w", encoding="utf-8") as f:
    f.writelines(lines)
PY
}

installer_check_permissions() {
  if [[ "$PREFIX" == "/usr/local" ]] || [[ "$PREFIX" == "/usr"* ]]; then
    if [[ "$(id -u 2>/dev/null || echo 1)" -ne 0 ]]; then
      die "Installation to ${PREFIX} requires root privileges. Try sudo, or use --prefix ~/.local"
    fi
  fi
}

installer_update_path_info() {
  local bin_dir="${PREFIX}/bin"

  if [[ "$PREFIX" == "/usr/local" || "$PREFIX" == "/usr"* ]]; then
    log_success "Installed to a system prefix: ${bin_dir}"
    return 0
  fi

  log_warning "Ensure your shell can find: ${bin_dir}"
  log_info "If you don't want to modify shell settings, run pf via full path:"
  log_info "  ${bin_dir}/pf"
}
