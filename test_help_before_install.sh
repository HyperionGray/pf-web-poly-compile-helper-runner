#!/usr/bin/env bash
# Test script to verify pf help works before installation

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PF_SCRIPT="${SCRIPT_DIR}/pf-runner/pf"

echo "Testing pf help before installation..."
echo ""

# Test 1: pf help
echo "Test 1: pf help"
OUTPUT=$("${PF_SCRIPT}" help 2>&1)
if echo "$OUTPUT" | grep -q "pf - Polyglot Task Runner"; then
    echo "✓ PASS: 'pf help' shows help text"
else
    echo "✗ FAIL: 'pf help' did not show expected help text"
    exit 1
fi
echo ""

# Test 2: pf --help
echo "Test 2: pf --help"
OUTPUT=$("${PF_SCRIPT}" --help 2>&1)
if echo "$OUTPUT" | grep -q "pf - Polyglot Task Runner"; then
    echo "✓ PASS: 'pf --help' shows help text"
else
    echo "✗ FAIL: 'pf --help' did not show expected help text"
    exit 1
fi
echo ""

# Test 3: pf -h
echo "Test 3: pf -h"
OUTPUT=$("${PF_SCRIPT}" -h 2>&1)
if echo "$OUTPUT" | grep -q "pf - Polyglot Task Runner"; then
    echo "✓ PASS: 'pf -h' shows help text"
else
    echo "✗ FAIL: 'pf -h' did not show expected help text"
    exit 1
fi
echo ""

# Test 4: Check help includes installation instructions
echo "Test 4: Verify help includes installation instructions"
OUTPUT=$("${PF_SCRIPT}" help 2>&1)
if echo "$OUTPUT" | grep -q "quick-install.sh"; then
    echo "✓ PASS: Help includes quick-install.sh reference"
else
    echo "✗ FAIL: Help missing quick-install.sh reference"
    exit 1
fi
echo ""

# Test 5: Check that non-help commands still show error
echo "Test 5: Verify non-help commands show error"
if OUTPUT=$("${PF_SCRIPT}" list 2>&1); then
    echo "✗ FAIL: 'pf list' should fail before installation"
    exit 1
else
    if echo "$OUTPUT" | grep -q "container image.*not found"; then
        echo "✓ PASS: 'pf list' shows appropriate error"
    else
        echo "✗ FAIL: 'pf list' error message unexpected"
        exit 1
    fi
fi
echo ""

# Test 6: Check error message includes help hint
echo "Test 6: Verify error messages include help hint"
OUTPUT=$("${PF_SCRIPT}" list 2>&1 || true)
if echo "$OUTPUT" | grep -q "run:.*pf help"; then
    echo "✓ PASS: Error message includes help hint"
else
    echo "✗ FAIL: Error message missing help hint"
    exit 1
fi
echo ""

echo "================================================"
echo "All tests passed! ✓"
echo "================================================"
