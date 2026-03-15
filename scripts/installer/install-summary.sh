#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [[ -f "${SCRIPT_DIR}/common.sh" ]]; then
  # shellcheck disable=SC1091
  source "${SCRIPT_DIR}/common.sh"
fi

if ! command -v log_info >/dev/null 2>&1; then
  log_info() { printf '%s\n' "[INFO] $*"; }
  log_success() { printf '%s\n' "[OK] $*"; }
  log_warning() { printf '%s\n' "[WARN] $*" >&2; }
fi

show_help() {
  cat <<'EOF'
pf installer summary

Usage:
  scripts/installer/install-summary.sh

Description:
  Prints an installation status overview for pf core runtime plus common
  tool bundles (exploit, injection, debugging, fuzzing, package tooling).
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi

check_cmd() {
  local cmd="${1:-}"
  command -v "$cmd" >/dev/null 2>&1
}

check_py_module() {
  local module="${1:-}"
  python3 - "$module" >/dev/null 2>&1 <<'PY'
import importlib
import sys
name = sys.argv[1]
importlib.import_module(name)
PY
}

mark() {
  local ok="${1:-false}"
  if [[ "$ok" == "true" ]]; then
    printf '%s' "OK"
  else
    printf '%s' "NO"
  fi
}

declare -A CATEGORY_TOTAL=()
declare -A CATEGORY_OK=()
declare -a ROWS=()

add_row() {
  local category="${1}"
  local component="${2}"
  local ok="${3}"
  local detail="${4}"

  CATEGORY_TOTAL["$category"]=$(( ${CATEGORY_TOTAL["$category"]:-0} + 1 ))
  if [[ "$ok" == "true" ]]; then
    CATEGORY_OK["$category"]=$(( ${CATEGORY_OK["$category"]:-0} + 1 ))
  fi

  ROWS+=("${category}|${component}|$(mark "$ok")|${detail}")
}

add_cmd_check() {
  local category="${1}"
  local component="${2}"
  local cmd="${3}"
  if check_cmd "$cmd"; then
    add_row "$category" "$component" "true" "$(command -v "$cmd")"
  else
    add_row "$category" "$component" "false" "not found in PATH"
  fi
}

add_py_check() {
  local category="${1}"
  local component="${2}"
  local module="${3}"
  if check_py_module "$module"; then
    add_row "$category" "$component" "true" "python module '${module}'"
  else
    add_row "$category" "$component" "false" "missing python module '${module}'"
  fi
}

add_core_pf_check() {
  local pf_cmd=""
  pf_cmd="$(command -v pf 2>/dev/null || true)"
  if [[ -n "$pf_cmd" ]]; then
    local version
    version="$(pf --version 2>/dev/null || true)"
    if [[ -n "$version" ]]; then
      add_row "core" "pf command" "true" "$version"
    else
      add_row "core" "pf command" "true" "$pf_cmd"
    fi
  else
    add_row "core" "pf command" "false" "not found in PATH"
  fi
}

add_core_python_check() {
  if check_cmd python3; then
    local v
    v="$(python3 --version 2>/dev/null || true)"
    add_row "core" "python3" "true" "${v:-python3 detected}"
  else
    add_row "core" "python3" "false" "python3 is required"
  fi
}

add_core_pf_check
add_core_python_check
add_cmd_check "core" "git" "git"
add_py_check "core" "lark" "lark"
add_py_check "core" "typer" "typer"
add_py_check "core" "fabric" "fabric"

add_py_check "exploit" "pwntools" "pwn"
add_cmd_check "exploit" "checksec" "checksec"
add_cmd_check "exploit" "ROPgadget" "ROPgadget"
add_cmd_check "exploit" "ropper" "ropper"

add_cmd_check "injection" "patchelf" "patchelf"
add_cmd_check "injection" "nasm" "nasm"
add_cmd_check "injection" "wat2wasm" "wat2wasm"
add_cmd_check "injection" "wasm-opt" "wasm-opt"

add_cmd_check "debug" "radare2 (r2)" "r2"
add_cmd_check "debug" "oryx" "oryx"
add_cmd_check "debug" "binsider" "binsider"
add_cmd_check "debug" "ghidra" "ghidra"

add_cmd_check "fuzzing" "afl-fuzz" "afl-fuzz"
add_cmd_check "fuzzing" "clang" "clang"

add_cmd_check "packages" "dpkg" "dpkg"
add_cmd_check "packages" "rpm" "rpm"
add_cmd_check "packages" "flatpak" "flatpak"
add_cmd_check "packages" "snap" "snap"

printf '%s\n' "INSTALLATION SUMMARY"
printf '%s\n' "===================="
printf 'Repo: %s\n' "$REPO_ROOT"
printf '\n'
printf '%-10s  %-22s  %-4s  %s\n' "Category" "Component" "Stat" "Details"
printf '%-10s  %-22s  %-4s  %s\n' "--------" "---------" "----" "-------"

for row in "${ROWS[@]}"; do
  IFS='|' read -r category component stat detail <<<"$row"
  printf '%-10s  %-22s  %-4s  %s\n' "$category" "$component" "$stat" "$detail"
done

printf '\n'
printf '%s\n' "CATEGORY HEALTH"
printf '%s\n' "---------------"

for category in core exploit injection debug fuzzing packages; do
  total="${CATEGORY_TOTAL[$category]:-0}"
  ok="${CATEGORY_OK[$category]:-0}"
  printf '%-10s  %d/%d installed\n' "$category" "$ok" "$total"
done

printf '\n'
printf '%s\n' "SUGGESTED NEXT COMMANDS"
printf '%s\n' "-----------------------"

if [[ "${CATEGORY_OK[core]:-0}" -lt "${CATEGORY_TOTAL[core]:-0}" ]]; then
  printf '%s\n' "  pf install prefix=~/.local"
fi
if [[ "${CATEGORY_OK[exploit]:-0}" -lt "${CATEGORY_TOTAL[exploit]:-0}" ]]; then
  printf '%s\n' "  pf install-exploit-tools"
fi
if [[ "${CATEGORY_OK[injection]:-0}" -lt "${CATEGORY_TOTAL[injection]:-0}" ]]; then
  printf '%s\n' "  pf install-injection-tools"
fi
if [[ "${CATEGORY_OK[debug]:-0}" -lt "${CATEGORY_TOTAL[debug]:-0}" ]]; then
  printf '%s\n' "  pf install-all-debug-tools"
fi
if [[ "${CATEGORY_OK[fuzzing]:-0}" -lt "${CATEGORY_TOTAL[fuzzing]:-0}" ]]; then
  printf '%s\n' "  pf install-fuzzing-tools"
fi
if [[ "${CATEGORY_OK[packages]:-0}" -lt "${CATEGORY_TOTAL[packages]:-0}" ]]; then
  printf '%s\n' "  pf install-pkg-tools"
  printf '%s\n' "  pf install-flatpak"
  printf '%s\n' "  pf install-snap"
fi

printf '\n'
log_info "Tip: run this command again after installer tasks to verify progress."
