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

# Test 4: Check help includes installation guidance tasks
echo "Test 4: Verify help includes installer guidance tasks"
OUTPUT=$("${PF_SCRIPT}" help 2>&1)
if echo "$OUTPUT" | grep -q "install-prereq-check"; then
    echo "✓ PASS: Help includes install-prereq-check"
else
    echo "✗ FAIL: Help missing install-prereq-check"
    exit 1
fi
echo ""

# Test 5: Check that non-help commands still show error
echo "Test 5: Verify non-help commands show error"
if OUTPUT=$("${PF_SCRIPT}" list 2>&1); then
    echo "✗ FAIL: 'pf list' should fail before installation"
    exit 1
else
    # Check for key error indicators instead of exact text
    if echo "$OUTPUT" | grep -qi "error"; then
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
# Look for "help" keyword in the error output
if echo "$OUTPUT" | grep -qi "help"; then
    echo "✓ PASS: Error message includes help hint"
else
    echo "✗ FAIL: Error message missing help hint"
    exit 1
fi
echo ""

# Test 7: Verify category installer help isn't truncated
echo "Test 7: Verify category-installation-help includes setup sections"
OUTPUT=$("${PF_SCRIPT}" category-installation-help 2>&1)
if echo "$OUTPUT" | grep -q "Bundle / CI Helpers:" && echo "$OUTPUT" | grep -q "module-install-help"; then
    echo "✓ PASS: category-installation-help includes full setup and bundle guidance"
else
    echo "✗ FAIL: category-installation-help output appears incomplete"
    exit 1
fi
echo ""

echo "================================================"
echo "All tests passed! ✓"
echo "================================================"
