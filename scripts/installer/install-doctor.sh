#!/usr/bin/env bash
set -euo pipefail

STRICT=false

show_help() {
  cat <<'EOF'
pf install-doctor - Post-install readiness checks

Usage:
  pf install-doctor
  pf install-doctor strict=true
  bash scripts/installer/install-doctor.sh [--strict]

What it checks:
  - Core runtime (pf, python3, node)
  - Installer-related tools (checksec, git-filter-repo, injection toolchain)
  - Optional exploit tooling (pwntools import)

Exit behavior:
  - Default: exits 0, even if tools are missing (guidance mode)
  - Strict: exits 1 when any check fails
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi

if [[ "${1:-}" == "--strict" ]]; then
  STRICT=true
fi

ok_count=0
missing_count=0
total_count=0

declare -A suggested_tasks=()

log_section() {
  echo ""
  echo "== $1 =="
}

check_cmd() {
  local label="$1"
  local cmd="$2"
  local fix_task="$3"
  total_count=$((total_count + 1))

  if command -v "$cmd" >/dev/null 2>&1; then
    echo "[OK] ${label}: $(command -v "$cmd")"
    ok_count=$((ok_count + 1))
  else
    echo "[MISSING] ${label}: command '${cmd}' not found"
    missing_count=$((missing_count + 1))
    suggested_tasks["$fix_task"]=1
  fi
}

check_python_module() {
  local label="$1"
  local module="$2"
  local fix_task="$3"
  total_count=$((total_count + 1))

  if python3 -c "import ${module}" >/dev/null 2>&1; then
    echo "[OK] ${label}: python module '${module}' import works"
    ok_count=$((ok_count + 1))
  else
    echo "[MISSING] ${label}: python module '${module}' not importable"
    missing_count=$((missing_count + 1))
    suggested_tasks["$fix_task"]=1
  fi
}

echo "pf Installer Doctor"
echo "==================="
echo "Strict mode: ${STRICT}"

log_section "Core runtime"
check_cmd "pf CLI" "pf" "pf install"
check_cmd "Python runtime" "python3" "pf install"
check_cmd "Node.js runtime" "node" "pf install"

log_section "Installer verification targets"
check_cmd "checksec" "checksec" "pf install-checksec"
check_cmd "git-filter-repo" "git-filter-repo" "pf install-git-filter-repo"
check_cmd "patchelf" "patchelf" "pf install-injection-tools"
check_cmd "nasm" "nasm" "pf install-injection-tools"
check_cmd "wasm-opt (binaryen)" "wasm-opt" "pf install-injection-tools"
check_cmd "wat2wasm (wabt)" "wat2wasm" "pf install-injection-tools"
check_python_module "pwntools" "pwn" "pf install-pwntools"

echo ""
echo "Summary: ${ok_count}/${total_count} checks passed, ${missing_count} missing"

if (( missing_count > 0 )); then
  echo ""
  echo "Recommended next steps:"
  for task in "${!suggested_tasks[@]}"; do
    echo "  - ${task}"
  done
fi

if [[ "$STRICT" == "true" && $missing_count -gt 0 ]]; then
  exit 1
fi
