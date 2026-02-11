#!/usr/bin/env bash
#
# Build helpers for scripts/build.sh
# Intended to be sourced (not executed).
#

if [[ -n "${__PF_BUILD_LIB_SOURCED:-}" ]]; then
  return 0
fi
__PF_BUILD_LIB_SOURCED=1

LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=pf-bash-lib.sh
source "${LIB_DIR}/pf-bash-lib.sh"

pf_repo_root() {
  local candidate=""
  candidate="$(cd "${LIB_DIR}/../.." && pwd)"
  if [[ -d "${candidate}/.git" || -f "${candidate}/pyproject.toml" || -f "${candidate}/Pfyfile.pf" ]]; then
    printf '%s\n' "${candidate}"
    return 0
  fi
  printf '%s\n' "${candidate}"
}

check_library() {
  local name="$1"
  local flag="${2:-}"

  if command_exists pkg-config; then
    if pkg-config --exists "$name" >/dev/null 2>&1; then
      return 0
    fi
  fi

  for dir in /usr/include /usr/local/include; do
    if [[ -f "${dir}/${name}.h" ]]; then
      return 0
    fi
  done

  if [[ -n "$flag" ]]; then
    local libname=""
    libname="$(printf '%s' "$flag" | sed 's/^-l//')"
    for dir in /usr/lib /usr/lib64 /usr/local/lib /usr/local/lib64; do
      if compgen -G "${dir}/lib${libname}.*" >/dev/null 2>&1; then
        return 0
      fi
    done
  fi

  return 1
}

install_sqlite3_dev() {
  local os_id=""
  os_id="$(detect_os)"

  case "$os_id" in
    debian)
      run_as_root apt-get update
      run_as_root apt-get install -y libsqlite3-dev
      ;;
    rhel)
      if command_exists dnf; then
        run_as_root dnf install -y sqlite-devel
      else
        run_as_root yum install -y sqlite-devel
      fi
      ;;
    arch)
      run_as_root pacman -Sy --noconfirm sqlite
      ;;
    macos)
      if command_exists brew; then
        brew install sqlite
      else
        return 1
      fi
      ;;
    *)
      return 1
      ;;
  esac
}

check_dependencies() {
  local requested_cc="${1:-}"
  local auto_install="${2:-1}"
  local compiler=""

  if [[ -n "$requested_cc" ]]; then
    compiler="$requested_cc"
  elif command_exists cc; then
    compiler="cc"
  elif command_exists gcc; then
    compiler="gcc"
  elif command_exists clang; then
    compiler="clang"
  fi

  if [[ -z "$compiler" ]]; then
    log_error "No C compiler found (cc/gcc/clang)"
    return 1
  fi

  if ! command_exists make; then
    log_error "make is required but not found"
    return 1
  fi

  if check_library "sqlite3" "-lsqlite3"; then
    return 0
  fi

  log_warning "sqlite3 development libraries not found"
  if [[ "$auto_install" -eq 1 ]]; then
    log_info "Attempting to install sqlite3 development libraries..."
    if ! install_sqlite3_dev; then
      log_error "Automatic sqlite3 install failed; install sqlite3 dev packages manually"
      return 1
    fi
    if check_library "sqlite3" "-lsqlite3"; then
      return 0
    fi
  fi

  log_error "sqlite3 development libraries still missing"
  return 1
}

build_project() {
  local root=""
  root="$(pf_repo_root)"

  local makefile=""
  if [[ -f "${root}/Makefile" ]]; then
    makefile="${root}/Makefile"
  elif [[ -f "${root}/makefile" ]]; then
    makefile="${root}/makefile"
  elif [[ -f "${root}/GNUmakefile" ]]; then
    makefile="${root}/GNUmakefile"
  fi

  if [[ -z "$makefile" ]]; then
    log_warning "No Makefile detected at ${root}; nothing to build"
    return 0
  fi

  log_info "Using Makefile: ${makefile}"
  (cd "${root}" && make)
}
