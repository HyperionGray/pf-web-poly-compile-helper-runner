#!/usr/bin/env bash

if declare -F __pf_runtime_loaded >/dev/null 2>&1; then
  return 0
fi
__pf_runtime_loaded() { :; }

pf_runtime_python_candidates() {
  local candidates=()
  local candidate=""
  local resolved=""
  local seen=":"

  if [[ -n "${PF_STABLE_PYTHON:-}" ]]; then
    candidates+=("${PF_STABLE_PYTHON}")
  fi

  candidates+=(
    "/usr/bin/python3"
    "/usr/local/bin/python3"
    "/opt/homebrew/bin/python3"
    "/opt/local/bin/python3"
  )

  if command -v python3 >/dev/null 2>&1; then
    candidates+=("$(command -v python3)")
  fi

  if command -v python >/dev/null 2>&1; then
    candidates+=("$(command -v python)")
  fi

  for candidate in "${candidates[@]}"; do
    [[ -n "$candidate" ]] || continue
    resolved="$candidate"
    if command -v readlink >/dev/null 2>&1; then
      resolved="$(readlink -f "$candidate" 2>/dev/null || printf '%s' "$candidate")"
    fi
    if [[ -x "$resolved" && "$seen" != *":${resolved}:"* ]]; then
      printf '%s\n' "$resolved"
      seen="${seen}${resolved}:"
    fi
  done
}

pf_collect_vendor_paths() {
  local runner_dir="$1"
  local candidates=()
  local candidate=""
  local seen=":"

  if [[ -n "${PF_VENDOR_PATH:-}" ]]; then
    candidates+=("${PF_VENDOR_PATH}")
  fi

  candidates+=("${runner_dir}/vendor")

  if [[ -n "${HOME:-}" ]]; then
    candidates+=("${HOME}/.local/lib/pf-runner/vendor")
  fi

  candidates+=(
    "/usr/local/lib/pf-runner/vendor"
    "/usr/lib/pf-runner/vendor"
  )

  for candidate in "${candidates[@]}"; do
    [[ -d "$candidate" ]] || continue
    if [[ "$seen" != *":${candidate}:"* ]]; then
      printf '%s\n' "$candidate"
      seen="${seen}${candidate}:"
    fi
  done
}

pf_python_has_pf_deps() {
  local python_bin="$1"
  "$python_bin" - <<'PY' >/dev/null 2>&1
import importlib

for name in ("fabric", "lark", "typer", "json5", "rich"):
    importlib.import_module(name)
PY
}

pf_export_runtime_env() {
  local runner_dir="$1"
  local pfy_root="$2"
  local default_pfy="${pfy_root}/Pfyfile.pf"
  local vendors=()
  local vendor_path=""
  local vendor=""

  if [[ -z "${PFY_FILE:-}" && -f "$default_pfy" ]]; then
    export PFY_FILE="$default_pfy"
    export PFY_ROOT="$pfy_root"
  fi

  while IFS= read -r vendor; do
    vendors+=("$vendor")
  done < <(pf_collect_vendor_paths "$runner_dir")

  if (( ${#vendors[@]} == 0 )); then
    PF_VENDOR_ACTIVE=0
    return 0
  fi

  vendor_path="$(IFS=:; printf '%s' "${vendors[*]}")"
  if [[ -n "${PYTHONPATH:-}" ]]; then
    export PYTHONPATH="${vendor_path}:${PYTHONPATH}"
  else
    export PYTHONPATH="${vendor_path}"
  fi
  export PYTHONNOUSERSITE=1
  PF_VENDOR_ACTIVE=1
}

pf_resolve_python() {
  local candidate=""

  if [[ -n "${PF_PYTHON:-}" ]]; then
    [[ -x "${PF_PYTHON}" ]] || {
      echo "pf: PF_PYTHON is not executable: ${PF_PYTHON}" >&2
      return 1
    }
    printf '%s\n' "${PF_PYTHON}"
    return 0
  fi

  if [[ "${PF_VENDOR_ACTIVE:-0}" == "1" ]]; then
    while IFS= read -r candidate; do
      printf '%s\n' "$candidate"
      return 0
    done < <(pf_runtime_python_candidates)
    return 1
  fi

  while IFS= read -r candidate; do
    if pf_python_has_pf_deps "$candidate"; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done < <(pf_runtime_python_candidates)

  return 1
}

pf_exec_runner() {
  local runner_dir="$1"
  local pfy_root="$2"
  local python_bin=""
  shift 2

  pf_export_runtime_env "$runner_dir" "$pfy_root"
  python_bin="$(pf_resolve_python)" || {
    echo "pf: could not find a usable Python 3 runtime. Run ./install.sh or set PF_PYTHON=/path/to/python3." >&2
    return 1
  }

  exec "$python_bin" "${runner_dir}/pf_main.py" "$@"
}
