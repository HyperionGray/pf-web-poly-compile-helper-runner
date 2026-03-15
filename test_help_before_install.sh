#!/usr/bin/env bash
# Validate installer help and preflight output.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALLER="${REPO_ROOT}/install.sh"

echo "Testing installer help and preflight output..."
echo ""

HELP_OUTPUT="$("${INSTALLER}" --help 2>&1)"
if ! printf '%s\n' "${HELP_OUTPUT}" | grep -q -- "--check"; then
  echo "✗ FAIL: installer help does not mention --check"
  exit 1
fi
echo "✓ PASS: installer help includes --check"

CHECK_OUTPUT="$("${INSTALLER}" --check --skip-deps --prefix "${HOME}/.local" 2>&1)"
if ! printf '%s\n' "${CHECK_OUTPUT}" | grep -q "Preflight checks passed"; then
  echo "✗ FAIL: preflight check mode did not report success"
  exit 1
fi
echo "✓ PASS: preflight check mode reports readiness"

echo ""
echo "================================================"
echo "All tests passed! ✓"
echo "================================================"
