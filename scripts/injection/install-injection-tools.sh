#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/pf-bash-lib.sh
source "${SCRIPT_DIR}/../lib/pf-bash-lib.sh"

DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: install-injection-tools.sh [--dry-run] [--help]

Install binary injection dependencies:
  - patchelf
  - nasm
  - binaryen (wasm-merge)
  - wabt (wat2wasm)

Options:
  --dry-run   Print installation actions without executing them
  -h, --help  Show this help message and exit
EOF
}

run_cmd() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[DRY-RUN]'
    printf ' %q' "$@"
    printf '\n'
    return 0
  fi
  "$@"
}

run_root_cmd() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[DRY-RUN]'
    printf ' %q' "$@"
    printf '\n'
    return 0
  fi
  run_as_root "$@"
}

verify_tool() {
  local label="$1"
  local cmd="$2"
  local version_arg="$3"
  local output=""
  if command_exists "$cmd"; then
    output="$("$cmd" "$version_arg" 2>/dev/null || true)"
    output="${output%%$'\n'*}"
    if [[ -n "$output" ]]; then
      printf '  %-12s %s\n' "${label}:" "$output"
    else
      printf '  %-12s %s\n' "${label}:" "installed"
    fi
  else
    printf '  %-12s %s\n' "${label}:" "NOT installed"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      log_error "Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
  shift
done

echo "Installing binary injection tools..."
[[ "$DRY_RUN" -eq 1 ]] && echo "[DRY-RUN] No changes will be made."

os_family="$(detect_os)"
case "$os_family" in
  debian)
    run_root_cmd apt-get update
    run_root_cmd apt-get install -y patchelf nasm binaryen wabt
    ;;
  rhel)
    if command_exists dnf; then
      run_root_cmd dnf install -y patchelf nasm binaryen wabt
    elif command_exists yum; then
      run_root_cmd yum install -y patchelf nasm binaryen wabt
    else
      die "No supported package manager found for RHEL-like system"
    fi
    ;;
  arch)
    run_root_cmd pacman -S --noconfirm patchelf nasm binaryen wabt
    ;;
  macos)
    if command_exists brew; then
      run_cmd brew install patchelf nasm binaryen wabt
    else
      die "Homebrew not found; install it first and rerun"
    fi
    ;;
  *)
    die "Unsupported OS; install manually: patchelf nasm binaryen wabt"
    ;;
esac

echo ""
echo "Verifying installations..."
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "  skipped in --dry-run mode"
else
  verify_tool "patchelf" "patchelf" "--version"
  verify_tool "nasm" "nasm" "-version"
  verify_tool "binaryen" "wasm-merge" "--version"
  verify_tool "wabt" "wat2wasm" "--version"
fi

echo ""
echo "✅ Binary injection tools installation flow completed!"
echo ""
echo "USAGE EXAMPLES:"
echo "  pf compile-c-shared-lib source=code.c output=lib.so"
echo "  pf inject-shared-lib binary=./program lib=hook.so"
echo "  pf patch-binary-deps binary=./program old_lib=libold.so new_lib=./libnew.so"
echo "  pf demo-injection-workflow"
echo ""
echo "TEST COMMANDS:"
echo "  patchelf --version"
echo "  nasm -version"
echo "  wasm-merge --version"
echo "  wat2wasm --version"
echo ""
echo "NEXT STEPS:"
echo "  pf injection-help"
echo "  pf test-injection-workflow"
