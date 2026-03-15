#!/usr/bin/env bash
#
# Common bash helpers for scripts in this repo.
# Intended to be sourced (not executed).
#

if [[ -n "${__PF_BASH_LIB_SOURCED:-}" ]]; then
  return 0
fi
__PF_BASH_LIB_SOURCED=1

command_exists() {
  local cmd="${1:-}"
  [[ -n "$cmd" ]] || return 1
  command -v "$cmd" >/dev/null 2>&1
}

pf_is_tty() {
  [[ -t 1 ]]
}

if pf_is_tty; then
  RED=$'\033[0;31m'
  GREEN=$'\033[0;32m'
  YELLOW=$'\033[1;33m'
  BLUE=$'\033[0;34m'
  CYAN=$'\033[0;36m'
  BOLD=$'\033[1m'
  NC=$'\033[0m'
else
  RED=''
  GREEN=''
  YELLOW=''
  BLUE=''
  CYAN=''
  BOLD=''
  NC=''
fi

log_info() { printf '%b\n' "${BLUE}[INFO]${NC} $*"; }
log_success() { printf '%b\n' "${GREEN}[SUCCESS]${NC} $*"; }
log_warning() { printf '%b\n' "${YELLOW}[WARNING]${NC} $*" >&2; }
log_error() { printf '%b\n' "${RED}[ERROR]${NC} $*" >&2; }
log_header() { printf '%b\n' "${BOLD}${CYAN}$*${NC}"; }

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
  log_error "This step requires root privileges: $*"
  return 1
}

detect_os() {
  local uname_s=""
  uname_s="$(uname -s 2>/dev/null || true)"

  case "$uname_s" in
    Linux)
      if [[ -f /etc/os-release ]]; then
        if grep -qiE '^(ID|ID_LIKE)=.*(debian|ubuntu)' /etc/os-release; then
          echo "debian"
          return 0
        fi
        if grep -qiE '^(ID|ID_LIKE)=.*(rhel|fedora|centos)' /etc/os-release; then
          echo "rhel"
          return 0
        fi
        if grep -qiE '^(ID|ID_LIKE)=.*arch' /etc/os-release; then
          echo "arch"
          return 0
        fi
      fi

      if command_exists apt-get; then echo "debian"
      elif command_exists dnf || command_exists yum; then echo "rhel"
      elif command_exists pacman; then echo "arch"
      else echo "linux"; fi
      ;;
    Darwin) echo "macos" ;;
    *) echo "unknown" ;;
  esac
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

pf_containers_systemd_dir() {
  printf '%s\n' "$(pf_home_dir)/.config/containers/systemd"
}

