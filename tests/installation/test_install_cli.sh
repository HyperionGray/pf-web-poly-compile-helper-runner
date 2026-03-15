#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${REPO_ROOT}"

fail() {
  echo "[FAIL] $*" >&2
  exit 1
}

pass() {
  echo "[PASS] $*"
}

help_output="$(./install.sh --help)"
echo "${help_output}" | grep -F -- "--dry-run" >/dev/null || fail "--help missing --dry-run"
echo "${help_output}" | grep -F -- "--post-install-help" >/dev/null || fail "--help missing --post-install-help"
pass "help text includes new CLI flags"

guidance_output="$(./install.sh --post-install-help --mode native --prefix /tmp/pf-test-prefix)"
echo "${guidance_output}" | grep -F "Post-install usage guidance" >/dev/null || fail "missing post-install guidance header"
echo "${guidance_output}" | grep -F "/tmp/pf-test-prefix/bin/pf --help" >/dev/null || fail "missing native post-install command"
pass "post-install help prints next-step commands"

dry_run_output="$(./install.sh --dry-run --mode native --prefix /tmp/pf-test-prefix --skip-deps)"
echo "${dry_run_output}" | grep -F "Dry-run plan" >/dev/null || fail "dry-run header not shown"
echo "${dry_run_output}" | grep -F "no files will be modified" >/dev/null || fail "dry-run safety text missing"
echo "${dry_run_output}" | grep -F "Mode: native" >/dev/null || fail "dry-run mode not shown"
pass "native dry-run renders plan"

container_dry_run_output="$(./install.sh --dry-run --mode container --runtime podman --prefix /tmp/pf-test-prefix)"
echo "${container_dry_run_output}" | grep -F "Mode: container" >/dev/null || fail "container dry-run mode missing"
echo "${container_dry_run_output}" | grep -F "Step: build images" >/dev/null || fail "container build step not shown"
pass "container dry-run renders plan"

echo "[PASS] installer CLI tests completed"
