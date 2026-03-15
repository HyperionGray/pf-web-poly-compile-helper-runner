#!/usr/bin/env bash
# Test script to verify pf help works before installation

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -x "${SCRIPT_DIR}/pf-runner/pf" ]; then
    PF_CMD=("${SCRIPT_DIR}/pf-runner/pf")
    PF_MODE="wrapper"
elif [ -f "${SCRIPT_DIR}/pf-runner-full/pf_main.py" ]; then
    PF_CMD=(python3 "${SCRIPT_DIR}/pf-runner-full/pf_main.py" -f "${SCRIPT_DIR}/pf-files/Pfyfile.pf")
    PF_MODE="runner"
elif command -v pf >/dev/null 2>&1; then
    PF_CMD=(pf)
    PF_MODE="installed"
else
    echo "✗ FAIL: Could not locate a runnable pf command"
    exit 1
fi

echo "Testing pf help before installation..."
echo ""

# Test 1: pf help
echo "Test 1: pf help"
OUTPUT=$("${PF_CMD[@]}" help 2>&1)
if echo "$OUTPUT" | grep -qiE "usage: pf|pf -"; then
    echo "✓ PASS: 'pf help' shows help text"
else
    echo "✗ FAIL: 'pf help' did not show expected help text"
    exit 1
fi
echo ""

# Test 2: pf --help
echo "Test 2: pf --help"
if OUTPUT=$("${PF_CMD[@]}" --help 2>&1); then
    if echo "$OUTPUT" | grep -qiE "usage: pf|pf -"; then
        echo "✓ PASS: 'pf --help' shows help text"
    else
        echo "✗ FAIL: 'pf --help' did not show expected help text"
        exit 1
    fi
elif [ "$PF_MODE" = "runner" ]; then
    echo "⊘ SKIP: runner mode does not support top-level --help without wrapper"
else
    echo "✗ FAIL: 'pf --help' command failed"
    exit 1
fi
echo ""

# Test 3: pf -h
echo "Test 3: pf -h"
if OUTPUT=$("${PF_CMD[@]}" -h 2>&1); then
    if echo "$OUTPUT" | grep -qiE "usage: pf|pf -"; then
        echo "✓ PASS: 'pf -h' shows help text"
    else
        echo "✗ FAIL: 'pf -h' did not show expected help text"
        exit 1
    fi
elif [ "$PF_MODE" = "runner" ]; then
    echo "⊘ SKIP: runner mode does not support top-level -h without wrapper"
else
    echo "✗ FAIL: 'pf -h' command failed"
    exit 1
fi
echo ""

# Test 4: Check help includes installation guidance tasks
echo "Test 4: Verify help includes installer guidance tasks"
if [ "$PF_MODE" = "wrapper" ]; then
    OUTPUT=$("${PF_CMD[@]}" help 2>&1)
else
    OUTPUT=$("${PF_CMD[@]}" install-help 2>&1)
fi
if echo "$OUTPUT" | grep -q "install-prereq-check" && echo "$OUTPUT" | grep -q "install-verify"; then
    echo "✓ PASS: Help includes install-prereq-check and install-verify"
else
    echo "✗ FAIL: Help missing install-prereq-check/install-verify guidance"
    exit 1
fi
echo ""

# Test 5: Check non-help command behavior based on execution mode
echo "Test 5: Verify non-help command behavior"
if [ "$PF_MODE" = "wrapper" ]; then
    if OUTPUT=$("${PF_CMD[@]}" list 2>&1); then
        echo "✗ FAIL: 'pf list' should fail in wrapper pre-install mode"
        exit 1
    else
        if echo "$OUTPUT" | grep -qi "error"; then
            echo "✓ PASS: wrapper mode shows expected error for 'pf list'"
        else
            echo "✗ FAIL: wrapper mode error message unexpected"
            exit 1
        fi
    fi
else
    if OUTPUT=$("${PF_CMD[@]}" list 2>&1); then
        echo "✓ PASS: runner/installed mode allows 'pf list'"
    else
        echo "✗ FAIL: 'pf list' unexpectedly failed in ${PF_MODE} mode"
        exit 1
    fi
fi
echo ""

# Test 6: Wrapper mode should include help hint in error output
echo "Test 6: Verify error/help guidance behavior"
if [ "$PF_MODE" = "wrapper" ]; then
    OUTPUT=$("${PF_CMD[@]}" list 2>&1 || true)
    if echo "$OUTPUT" | grep -qi "help"; then
        echo "✓ PASS: Error message includes help hint"
    else
        echo "✗ FAIL: Error message missing help hint"
        exit 1
    fi
else
    echo "⊘ SKIP: Not in wrapper mode (mode=${PF_MODE})"
fi
echo ""

# Test 7: Verify category installer help isn't truncated
echo "Test 7: Verify category-installation-help includes setup sections"
OUTPUT=$("${PF_CMD[@]}" category-installation-help 2>&1)
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
