#!/usr/bin/env bash
# Test script to verify pf help works from the repository checkout

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PF_SCRIPT="${SCRIPT_DIR}/pf-runner-full/pf"

echo "Testing pf help before installation..."
echo ""

# Test 1: pf help
echo "Test 1: pf help"
OUTPUT=$("${PF_SCRIPT}" help 2>&1)
if echo "$OUTPUT" | grep -q "usage: pf" && echo "$OUTPUT" | grep -q "single-file, symbol-free Fabric runner"; then
    echo "✓ PASS: 'pf help' shows help text"
else
    echo "✗ FAIL: 'pf help' did not show expected help text"
    exit 1
fi
echo ""

# Test 2: pf --help
echo "Test 2: pf --help"
OUTPUT=$("${PF_SCRIPT}" --help 2>&1)
if echo "$OUTPUT" | grep -q "usage: pf" && echo "$OUTPUT" | grep -q "single-file, symbol-free Fabric runner"; then
    echo "✓ PASS: 'pf --help' shows help text"
else
    echo "✗ FAIL: 'pf --help' did not show expected help text"
    exit 1
fi
echo ""

# Test 3: pf -h
echo "Test 3: pf -h"
OUTPUT=$("${PF_SCRIPT}" -h 2>&1)
if echo "$OUTPUT" | grep -q "usage: pf" && echo "$OUTPUT" | grep -q "single-file, symbol-free Fabric runner"; then
    echo "✓ PASS: 'pf -h' shows help text"
else
    echo "✗ FAIL: 'pf -h' did not show expected help text"
    exit 1
fi
echo ""

# Test 4: Check help includes core CLI options
echo "Test 4: Verify help includes core CLI options"
OUTPUT=$("${PF_SCRIPT}" help 2>&1)
if echo "$OUTPUT" | grep -q -- "-f, --file FILE"; then
    echo "✓ PASS: Help includes file-selection option"
else
    echo "✗ FAIL: Help missing file-selection option"
    exit 1
fi
echo ""

# Test 5: Verify list works from the repository checkout
echo "Test 5: Verify 'pf list' works from the repository checkout"
if OUTPUT=$("${PF_SCRIPT}" list 2>&1); then
    if echo "$OUTPUT" | grep -q "Usage: pf run <task_name>"; then
        echo "✓ PASS: 'pf list' works and shows usage hint"
    else
        echo "✗ FAIL: 'pf list' output missing expected usage hint"
        exit 1
    fi
else
    echo "✗ FAIL: 'pf list' should succeed from the repository checkout"
    exit 1
fi
echo ""

# Test 6: Verify task list contains core section header
echo "Test 6: Verify task list contains the core task section"
OUTPUT=$("${PF_SCRIPT}" list 2>&1)
if echo "$OUTPUT" | grep -q "Core tasks:"; then
    echo "✓ PASS: Task list includes core tasks"
else
    echo "✗ FAIL: Task list missing core section"
    exit 1
fi
echo ""

echo "================================================"
echo "All tests passed! ✓"
echo "================================================"
