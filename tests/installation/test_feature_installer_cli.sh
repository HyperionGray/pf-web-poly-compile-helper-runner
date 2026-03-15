#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

pass_count=0
fail_count=0

run_check() {
  local name="$1"
  local script_path="$2"
  local help_output=""
  local dry_output=""

  echo "[TEST] ${name}"

  if [[ ! -x "$script_path" ]]; then
    echo "  [FAIL] Script is not executable: ${script_path}"
    fail_count=$((fail_count + 1))
    return
  fi

  if ! help_output="$("$script_path" --help 2>&1)"; then
    echo "  [FAIL] --help returned non-zero"
    fail_count=$((fail_count + 1))
    return
  fi

  if [[ "$help_output" != *"Usage:"* ]] || [[ "$help_output" != *"--dry-run"* ]]; then
    echo "  [FAIL] --help missing expected usage/options text"
    fail_count=$((fail_count + 1))
    return
  fi

  if ! dry_output="$("$script_path" --dry-run 2>&1)"; then
    echo "  [FAIL] --dry-run returned non-zero"
    fail_count=$((fail_count + 1))
    return
  fi

  if [[ "$dry_output" != *"[DRY-RUN]"* ]]; then
    echo "  [FAIL] --dry-run output missing [DRY-RUN] marker"
    fail_count=$((fail_count + 1))
    return
  fi

  echo "  [PASS] --help and --dry-run are functional"
  pass_count=$((pass_count + 1))
}

run_check "Injection installer CLI" "$REPO_ROOT/scripts/injection/install-injection-tools.sh"
run_check "git-filter-repo installer CLI" "$REPO_ROOT/scripts/gitops/install-git-filter-repo.sh"
run_check "PR tools installer CLI" "$REPO_ROOT/scripts/gitops/install-pr-tools.sh"

echo ""
echo "Installer CLI test summary: pass=${pass_count} fail=${fail_count}"

if [[ "$fail_count" -ne 0 ]]; then
  exit 1
fi

