#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-core}"

usage() {
  cat <<'EOF'
Usage: verify-installation.sh [profile]

Profiles:
  core     Verify pf and core dependencies (default)
  web      Verify web toolchain commands
  exploit  Verify exploit tooling commands
  debug    Verify debugger commands
  fuzzing  Verify fuzzing toolchain commands
  all      Verify every profile
EOF
}

if [[ "${PROFILE}" == "-h" || "${PROFILE}" == "--help" ]]; then
  usage
  exit 0
fi

case "${PROFILE}" in
  core|web|exploit|debug|fuzzing|all) ;;
  *)
    echo "[ERR] Unknown profile: ${PROFILE}" >&2
    usage >&2
    exit 2
    ;;
esac

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PF_MAIN="${ROOT}/pf-runner-full/pf_main.py"
missing_required=0

check_cmd() {
  local cmd="$1"
  local desc="$2"
  if command -v "${cmd}" >/dev/null 2>&1; then
    echo "[OK] ${cmd} - ${desc}"
  else
    echo "[MISSING] ${cmd} - ${desc}"
    missing_required=$((missing_required + 1))
  fi
}

check_python_module() {
  local mod="$1"
  local desc="$2"
  if python3 -c "import ${mod}" >/dev/null 2>&1; then
    echo "[OK] python module '${mod}' - ${desc}"
  else
    echo "[MISSING] python module '${mod}' - ${desc}"
    missing_required=$((missing_required + 1))
  fi
}

PF_CMD=""
PF_CMD_HEALTHY=false
if command -v pf >/dev/null 2>&1; then
  PF_CMD="pf"
  if pf --version >/dev/null 2>&1; then
    PF_CMD_HEALTHY=true
  fi
fi

echo "Installer verification"
echo "Profile: ${PROFILE}"
echo ""

echo "Core verification:"
if [[ "${PF_CMD_HEALTHY}" == true ]]; then
  if "${PF_CMD}" --version >/dev/null 2>&1; then
    echo "[OK] pf --version"
  else
    echo "[MISSING] pf --version failed"
    missing_required=$((missing_required + 1))
  fi
  if "${PF_CMD}" --help >/dev/null 2>&1; then
    echo "[OK] pf --help"
  else
    echo "[WARN] pf --help failed (non-fatal in nested task contexts)"
  fi
elif [[ -f "${PF_MAIN}" ]] && python3 "${PF_MAIN}" -V >/dev/null 2>&1; then
  echo "[OK] python3 pf_main.py -V (local source-tree runner)"
  if [[ -n "${PF_CMD}" ]]; then
    echo "[WARN] 'pf' exists in PATH but is not healthy in this environment"
  fi
else
  echo "[MISSING] Could not validate pf via PATH command or local pf_main.py"
  missing_required=$((missing_required + 1))
fi

check_cmd "python3" "runtime interpreter"
check_cmd "git" "repository tooling"
check_cmd "curl" "download utility"
echo ""

if [[ "${PROFILE}" == "web" || "${PROFILE}" == "all" ]]; then
  echo "Web profile verification:"
  check_cmd "node" "Node.js runtime"
  check_cmd "npm" "Node package manager"
  check_cmd "npx" "Node package executable runner"
  echo ""
fi

if [[ "${PROFILE}" == "exploit" || "${PROFILE}" == "all" ]]; then
  echo "Exploit profile verification:"
  check_python_module "pwn" "pwntools"
  check_cmd "checksec" "binary hardening analysis"
  check_cmd "ROPgadget" "ROP gadget discovery"
  check_cmd "ropper" "ROP helper"
  echo ""
fi

if [[ "${PROFILE}" == "debug" || "${PROFILE}" == "all" ]]; then
  echo "Debug profile verification:"
  check_cmd "gdb" "GNU debugger"
  check_cmd "lldb" "LLVM debugger"
  echo ""
fi

if [[ "${PROFILE}" == "fuzzing" || "${PROFILE}" == "all" ]]; then
  echo "Fuzzing profile verification:"
  check_cmd "clang" "compiler for sanitizer/fuzzing tasks"
  check_cmd "afl-fuzz" "AFL++ runtime"
  echo ""
fi

echo "Summary:"
echo "  Missing required checks: ${missing_required}"
echo ""

if [[ "${missing_required}" -gt 0 ]]; then
  echo "[ERR] Verification failed."
  echo "Install missing items, then rerun: pf install-verify profile=${PROFILE}"
  exit 1
fi

echo "[OK] Verification passed."
exit 0
