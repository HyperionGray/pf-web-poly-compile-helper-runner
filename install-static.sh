#!/usr/bin/env bash
# install-static.sh - Install prebuilt pf static executable.

set -euo pipefail

DEFAULT_PREFIX_NATIVE="/usr/local"
DEFAULT_PREFIX_USER="${HOME:-/tmp}/.local"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

STATIC_CANDIDATES=(
  "${SCRIPT_DIR}/pf-runner-full/pf-static"
  "${SCRIPT_DIR}/pf-runner/pf-static"
)

PREFIX=""
PREFIX_SET=false
DRY_RUN=false
SHOW_HELP=false

log_info() { printf '%s\n' "[INFO] $*"; }
log_success() { printf '%s\n' "[SUCCESS] $*"; }
log_warning() { printf '%s\n' "[WARNING] $*" >&2; }
log_error() { printf '%s\n' "[ERROR] $*" >&2; }

show_help() {
  cat <<'EOF'
pf-runner Static Installer

USAGE:
  ./install-static.sh [OPTIONS]

OPTIONS:
  --prefix PATH     Install prefix (default: /usr/local as root, ~/.local otherwise)
  --dry-run         Show planned actions without modifying files
  --help, -h        Show this help message

EXAMPLES:
  sudo ./install-static.sh
  ./install-static.sh --prefix ~/.local
  ./install-static.sh --dry-run --prefix ~/.local

NOTES:
  This installer expects a prebuilt static executable (pf-static).
  Build one with:
    cd pf-runner-full
    make build-static
EOF
}

resolve_static_executable() {
  local candidate=""
  for candidate in "${STATIC_CANDIDATES[@]}"; do
    if [[ -f "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

detect_shell_profile() {
  local shell_name
  shell_name="$(basename "${SHELL:-sh}")"
  case "$shell_name" in
    zsh) printf '%s\n' "${HOME:-/tmp}/.zshrc" ;;
    bash)
      if [[ -f "${HOME:-/tmp}/.bashrc" || ! -f "${HOME:-/tmp}/.bash_profile" ]]; then
        printf '%s\n' "${HOME:-/tmp}/.bashrc"
      else
        printf '%s\n' "${HOME:-/tmp}/.bash_profile"
      fi
      ;;
    fish) printf '%s\n' "${HOME:-/tmp}/.config/fish/config.fish" ;;
    *) printf '%s\n' "${HOME:-/tmp}/.profile" ;;
  esac
}

path_export_line() {
  local bin_dir="$1"
  local shell_name
  shell_name="$(basename "${SHELL:-sh}")"
  if [[ "$shell_name" == "fish" ]]; then
    printf '%s\n' "set -gx PATH \"${bin_dir}\" \$PATH"
  else
    printf '%s\n' "export PATH=\"${bin_dir}:\$PATH\""
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prefix)
      PREFIX="${2:-}"
      PREFIX_SET=true
      shift 2
      ;;
    --prefix=*)
      PREFIX="${1#*=}"
      PREFIX_SET=true
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --help|-h)
      SHOW_HELP=true
      shift
      ;;
    *)
      log_error "Unknown option: $1"
      SHOW_HELP=true
      shift
      ;;
  esac
done

if [[ "$SHOW_HELP" == true ]]; then
  show_help
  exit 0
fi

if [[ "$PREFIX_SET" == false ]]; then
  if [[ "$(id -u 2>/dev/null || echo 1)" -eq 0 ]]; then
    PREFIX="$DEFAULT_PREFIX_NATIVE"
  else
    PREFIX="$DEFAULT_PREFIX_USER"
  fi
fi

if [[ "$PREFIX" == "/usr/local" || "$PREFIX" == "/usr"* ]]; then
  if [[ "$(id -u 2>/dev/null || echo 1)" -ne 0 ]]; then
    log_error "Installation to ${PREFIX} requires root privileges."
    log_info "Try: sudo ./install-static.sh"
    log_info "Or use user installation: ./install-static.sh --prefix ~/.local"
    exit 1
  fi
fi

LIB_DIR="${PREFIX}/lib/pf-runner"
BIN_DIR="${PREFIX}/bin"
TARGET="${BIN_DIR}/pf"
STATIC_EXEC=""
if STATIC_EXEC="$(resolve_static_executable)"; then
  :
else
  STATIC_EXEC=""
fi

if [[ "$DRY_RUN" == true ]]; then
  log_info "Dry run mode enabled. No files will be modified."
  if [[ -n "$STATIC_EXEC" ]]; then
    log_info "Static executable source: ${STATIC_EXEC}"
  else
    log_warning "Static executable not found yet."
    log_info "Build with: cd pf-runner-full && make build-static"
  fi
  log_info "Would create directories:"
  log_info "  ${LIB_DIR}"
  log_info "  ${BIN_DIR}"
  log_info "Would install executable to: ${TARGET}"
  if [[ "$PREFIX" != "/usr/local" && "$PREFIX" != "/usr"* ]] && [[ ":${PATH:-}:" != *":${BIN_DIR}:"* ]]; then
    log_info "Suggested profile: $(detect_shell_profile)"
    log_info "Suggested PATH line: $(path_export_line "${BIN_DIR}")"
  fi
  exit 0
fi

if [[ -z "$STATIC_EXEC" ]]; then
  log_error "Could not find pf-static executable."
  log_info "Checked:"
  for candidate in "${STATIC_CANDIDATES[@]}"; do
    log_info "  - ${candidate}"
  done
  log_info "Build static binary with:"
  log_info "  cd pf-runner-full && make build-static"
  exit 1
fi

printf '%s\n' "pf-runner Static Installer"
printf '%s\n\n' "=========================="

mkdir -p "${LIB_DIR}" "${BIN_DIR}"
install -m 0755 "${STATIC_EXEC}" "${TARGET}"

log_success "Installed static pf executable to ${TARGET}"

if [[ "$PREFIX" != "/usr/local" && "$PREFIX" != "/usr"* ]]; then
  if [[ ":${PATH:-}:" != *":${BIN_DIR}:"* ]]; then
    log_warning "Installation directory is not in PATH: ${BIN_DIR}"
    log_info "Add this line to $(detect_shell_profile):"
    log_info "  $(path_export_line "${BIN_DIR}")"
  else
    log_success "Installation directory is already in PATH: ${BIN_DIR}"
  fi
fi

log_info "Next steps:"
log_info "  1. Run: ${TARGET} --version"
log_info "  2. Run: ${TARGET} list"
log_success "Static installation completed."
