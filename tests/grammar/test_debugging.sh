#!/bin/bash
# test_debugging.sh - Unit tests for debugging and reverse engineering tasks
# Tests GDB, LLDB, pwndbg integration, and RE tools

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASSED=0
FAILED=0
SKIPPED=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PF_RUNNER="$REPO_ROOT/pf-runner"
PF_CMD="python3 $PF_RUNNER/pf_parser.py"

echo "Testing Debugging and Reverse Engineering features"
echo "Repository: $REPO_ROOT"
echo ""

pass() {
    PASSED=$((PASSED + 1))
    echo -e "${GREEN}✓ PASS${NC}: $1"
}

fail() {
    FAILED=$((FAILED + 1))
    echo -e "${RED}✗ FAIL${NC}: $1"
    echo "  Reason: $2"
}

skip() {
    SKIPPED=$((SKIPPED + 1))
    echo -e "${YELLOW}○ SKIP${NC}: $1 (reason: $2)"
}

section() {
    echo ""
    echo -e "${BLUE}=== $1 ===${NC}"
    echo ""
}

cd "$REPO_ROOT"
TASK_LIST=$($PF_CMD Pfyfile.pf list 2>&1)

# ==============================================================================
section "1. Debugger Installation Tasks"
# ==============================================================================

# Test 1.1: install-debuggers exists
if echo "$TASK_LIST" | grep -q "install-debuggers"; then
    pass "install-debuggers task exists"
else
    fail "install-debuggers task exists" "Task not found"
fi

# Test 1.2: check-debuggers exists
if echo "$TASK_LIST" | grep -q "check-debuggers"; then
    pass "check-debuggers task exists"
else
    fail "check-debuggers task exists" "Task not found"
fi

# ==============================================================================
section "2. Debug Example Build Tasks"
# ==============================================================================

# Test 2.1: build-debug-examples exists
if echo "$TASK_LIST" | grep -q "build-debug-examples"; then
    pass "build-debug-examples task exists"
else
    fail "build-debug-examples task exists" "Task not found"
fi

# Test 2.2: clean-debug-examples exists
if echo "$TASK_LIST" | grep -q "clean-debug-examples"; then
    pass "clean-debug-examples task exists"
else
    fail "clean-debug-examples task exists" "Task not found"
fi

# ==============================================================================
section "3. Interactive Debugging Tasks"
# ==============================================================================

# Test 3.1: debug task exists
if echo "$TASK_LIST" | grep -q "^  debug "; then
    pass "debug task exists"
else
    fail "debug task exists" "Task not found"
fi

# Test 3.2: debug-gdb exists
if echo "$TASK_LIST" | grep -q "debug-gdb"; then
    pass "debug-gdb task exists"
else
    fail "debug-gdb task exists" "Task not found"
fi

# Test 3.3: debug-lldb exists
if echo "$TASK_LIST" | grep -q "debug-lldb"; then
    pass "debug-lldb task exists"
else
    fail "debug-lldb task exists" "Task not found"
fi

# Test 3.4: debug-info exists
if echo "$TASK_LIST" | grep -q "debug-info"; then
    pass "debug-info task exists"
else
    fail "debug-info task exists" "Task not found"
fi

# ==============================================================================
section "4. Reverse Engineering Tasks"
# ==============================================================================

# Test 4.1: disassemble exists
if echo "$TASK_LIST" | grep -q "disassemble"; then
    pass "disassemble task exists"
else
    fail "disassemble task exists" "Task not found"
fi

# Test 4.2: strings-analysis exists
if echo "$TASK_LIST" | grep -q "strings-analysis"; then
    pass "strings-analysis task exists"
else
    fail "strings-analysis task exists" "Task not found"
fi

# Test 4.3: binary-info exists
if echo "$TASK_LIST" | grep -q "binary-info"; then
    pass "binary-info task exists"
else
    fail "binary-info task exists" "Task not found"
fi

# ==============================================================================
section "5. Binary Lifting Tasks"
# ==============================================================================

# Test 5.1: install-retdec exists
if echo "$TASK_LIST" | grep -q "install-retdec"; then
    pass "install-retdec task exists"
else
    fail "install-retdec task exists" "Task not found"
fi

# Test 5.2: lift-binary-retdec exists
if echo "$TASK_LIST" | grep -q "lift-binary-retdec"; then
    pass "lift-binary-retdec task exists"
else
    fail "lift-binary-retdec task exists" "Task not found"
fi

# Test 5.3: lift-inspect exists
if echo "$TASK_LIST" | grep -q "lift-inspect"; then
    pass "lift-inspect task exists"
else
    fail "lift-inspect task exists" "Task not found"
fi

# Test 5.4: optimize-lifted-ir exists
if echo "$TASK_LIST" | grep -q "optimize-lifted-ir"; then
    pass "optimize-lifted-ir task exists"
else
    fail "optimize-lifted-ir task exists" "Task not found"
fi

# ==============================================================================
section "6. Binary Injection Tasks"
# ==============================================================================

# Test 6.1: install-injection-tools exists
if echo "$TASK_LIST" | grep -q "install-injection-tools"; then
    pass "install-injection-tools task exists"
else
    fail "install-injection-tools task exists" "Task not found"
fi

# Test 6.2: create-injection-payload-c exists
if echo "$TASK_LIST" | grep -q "create-injection-payload-c"; then
    pass "create-injection-payload-c task exists"
else
    fail "create-injection-payload-c task exists" "Task not found"
fi

# Test 6.3: analyze-injection-target exists
if echo "$TASK_LIST" | grep -q "analyze-injection-target"; then
    pass "analyze-injection-target task exists"
else
    fail "analyze-injection-target task exists" "Task not found"
fi

# Test 6.4: inject-preload exists
if echo "$TASK_LIST" | grep -q "inject-preload"; then
    pass "inject-preload task exists"
else
    fail "inject-preload task exists" "Task not found"
fi

# ==============================================================================
section "7. ROP Exploitation Tasks"
# ==============================================================================

# Test 7.1: rop-build exists
if echo "$TASK_LIST" | grep -q "rop-build"; then
    pass "rop-build task exists"
else
    fail "rop-build task exists" "Task not found"
fi

# Test 7.2: rop-check exists
if echo "$TASK_LIST" | grep -q "rop-check"; then
    pass "rop-check task exists"
else
    fail "rop-check task exists" "Task not found"
fi

# Test 7.3: rop-gadgets exists
if echo "$TASK_LIST" | grep -q "rop-gadgets"; then
    pass "rop-gadgets task exists"
else
    fail "rop-gadgets task exists" "Task not found"
fi

# Test 7.4: rop-exploit exists
if echo "$TASK_LIST" | grep -q "rop-exploit"; then
    pass "rop-exploit task exists"
else
    fail "rop-exploit task exists" "Task not found"
fi

# Test 7.5: rop-demo exists
if echo "$TASK_LIST" | grep -q "rop-demo"; then
    pass "rop-demo task exists"
else
    fail "rop-demo task exists" "Task not found"
fi

# ==============================================================================
section "8. Exploit Development Tasks (pwntools)"
# ==============================================================================

# Test 8.1: install-pwntools exists
if echo "$TASK_LIST" | grep -q "install-pwntools"; then
    pass "install-pwntools task exists"
else
    fail "install-pwntools task exists" "Task not found"
fi

# Test 8.2: pwn-template exists
if echo "$TASK_LIST" | grep -q "pwn-template"; then
    pass "pwn-template task exists"
else
    fail "pwn-template task exists" "Task not found"
fi

# Test 8.3: pwn-cyclic exists
if echo "$TASK_LIST" | grep -q "pwn-cyclic"; then
    pass "pwn-cyclic task exists"
else
    fail "pwn-cyclic task exists" "Task not found"
fi

# Test 8.4: pwn-shellcode exists
if echo "$TASK_LIST" | grep -q "pwn-shellcode"; then
    pass "pwn-shellcode task exists"
else
    fail "pwn-shellcode task exists" "Task not found"
fi

# ==============================================================================
section "9. ROPgadget Tasks"
# ==============================================================================

# Test 9.1: install-ropgadget exists
if echo "$TASK_LIST" | grep -q "install-ropgadget"; then
    pass "install-ropgadget task exists"
else
    fail "install-ropgadget task exists" "Task not found"
fi

# Test 9.2: rop-find-gadgets exists
if echo "$TASK_LIST" | grep -q "rop-find-gadgets"; then
    pass "rop-find-gadgets task exists"
else
    fail "rop-find-gadgets task exists" "Task not found"
fi

# Test 9.3: rop-search exists
if echo "$TASK_LIST" | grep -q "rop-search"; then
    pass "rop-search task exists"
else
    fail "rop-search task exists" "Task not found"
fi

# Test 9.4: rop-chain-build exists
if echo "$TASK_LIST" | grep -q "rop-chain-build"; then
    pass "rop-chain-build task exists"
else
    fail "rop-chain-build task exists" "Task not found"
fi

# ==============================================================================
section "10. TUI Tasks"
# ==============================================================================

# Test 10.1: tui exists
if echo "$TASK_LIST" | grep -q "tui"; then
    pass "tui task exists"
else
    fail "tui task exists" "Task not found"
fi

# Test 10.2: tui-with-file exists
if echo "$TASK_LIST" | grep -q "tui-with-file"; then
    pass "tui-with-file task exists"
else
    fail "tui-with-file task exists" "Task not found"
fi

# Test 10.3: install-tui-deps exists
if echo "$TASK_LIST" | grep -q "install-tui-deps"; then
    pass "install-tui-deps task exists"
else
    fail "install-tui-deps task exists" "Task not found"
fi

# Test 10.4: tui-help exists
if echo "$TASK_LIST" | grep -q "tui-help"; then
    pass "tui-help task exists"
else
    fail "tui-help task exists" "Task not found"
fi

# ==============================================================================
section "11. Git Cleanup Tasks"
# ==============================================================================

# Test 11.1: git-cleanup exists
if echo "$TASK_LIST" | grep -q "git-cleanup"; then
    pass "git-cleanup task exists"
else
    fail "git-cleanup task exists" "Task not found"
fi

# Test 11.2: git-analyze-large-files exists
if echo "$TASK_LIST" | grep -q "git-analyze-large-files"; then
    pass "git-analyze-large-files task exists"
else
    fail "git-analyze-large-files task exists" "Task not found"
fi

# Test 11.3: git-repo-size exists
if echo "$TASK_LIST" | grep -q "git-repo-size"; then
    pass "git-repo-size task exists"
else
    fail "git-repo-size task exists" "Task not found"
fi

# ==============================================================================
section "12. Debugging Tools Installation"
# ==============================================================================

# Test 12.1: install-oryx exists
if echo "$TASK_LIST" | grep -q "install-oryx"; then
    pass "install-oryx task exists"
else
    fail "install-oryx task exists" "Task not found"
fi

# Test 12.2: install-binsider exists
if echo "$TASK_LIST" | grep -q "install-binsider"; then
    pass "install-binsider task exists"
else
    fail "install-binsider task exists" "Task not found"
fi

# Test 12.3: install-radare2 exists
if echo "$TASK_LIST" | grep -q "install-radare2"; then
    pass "install-radare2 task exists"
else
    fail "install-radare2 task exists" "Task not found"
fi

# Test 12.4: install-ghidra exists
if echo "$TASK_LIST" | grep -q "install-ghidra"; then
    pass "install-ghidra task exists"
else
    fail "install-ghidra task exists" "Task not found"
fi

# Test 12.5: install-snowman exists
if echo "$TASK_LIST" | grep -q "install-snowman"; then
    pass "install-snowman task exists"
else
    fail "install-snowman task exists" "Task not found"
fi

# Test 12.6: install-all-debug-tools exists
if echo "$TASK_LIST" | grep -q "install-all-debug-tools"; then
    pass "install-all-debug-tools task exists"
else
    fail "install-all-debug-tools task exists" "Task not found"
fi

# Test 12.7: check-debug-tools exists
if echo "$TASK_LIST" | grep -q "check-debug-tools"; then
    pass "check-debug-tools task exists"
else
    fail "check-debug-tools task exists" "Task not found"
fi

# ==============================================================================
section "13. Documentation Exists"
# ==============================================================================

# Test 13.1: Debugging documentation exists
if [ -f "$REPO_ROOT/docs/KERNEL-DEBUGGING.md" ]; then
    pass "Kernel debugging documentation exists"
else
    fail "Kernel debugging documentation exists" "docs/KERNEL-DEBUGGING.md not found"
fi

# Test 13.2: Binary injection documentation exists
if [ -f "$REPO_ROOT/docs/BINARY-INJECTION.md" ]; then
    pass "Binary injection documentation exists"
else
    fail "Binary injection documentation exists" "docs/BINARY-INJECTION.md not found"
fi

# Test 13.3: LLVM lifting documentation exists
if [ -f "$REPO_ROOT/docs/LLVM-LIFTING.md" ]; then
    pass "LLVM lifting documentation exists"
else
    fail "LLVM lifting documentation exists" "docs/LLVM-LIFTING.md not found"
fi

# Test 13.4: TUI documentation exists
if [ -f "$REPO_ROOT/docs/TUI.md" ]; then
    pass "TUI documentation exists"
else
    fail "TUI documentation exists" "docs/TUI.md not found"
fi

# Test 13.5: Security testing documentation exists
if [ -f "$REPO_ROOT/docs/SECURITY-TESTING.md" ]; then
    pass "Security testing documentation exists"
else
    fail "Security testing documentation exists" "docs/SECURITY-TESTING.md not found"
fi

# ==============================================================================
section "14. Help Tasks"
# ==============================================================================

# Test 14.1: debug-help exists
if echo "$TASK_LIST" | grep -q "debug-help"; then
    pass "debug-help task exists"
else
    fail "debug-help task exists" "Task not found"
fi

# Test 14.2: security-help exists
if echo "$TASK_LIST" | grep -q "security-help"; then
    pass "security-help task exists"
else
    fail "security-help task exists" "Task not found"
fi

# Test 14.3: rop-help exists
if echo "$TASK_LIST" | grep -q "rop-help"; then
    pass "rop-help task exists"
else
    fail "rop-help task exists" "Task not found"
fi

# Test 14.4: injection-help exists
if echo "$TASK_LIST" | grep -q "injection-help"; then
    pass "injection-help task exists"
else
    fail "injection-help task exists" "Task not found"
fi

# Test 14.5: lifting-help exists
if echo "$TASK_LIST" | grep -q "lifting-help"; then
    pass "lifting-help task exists"
else
    fail "lifting-help task exists" "Task not found"
fi

# ==============================================================================
# Summary
# ==============================================================================

echo ""
echo "========================================"
echo -e "${BLUE}Debugging Features Test Summary${NC}"
echo "========================================"
echo -e "${GREEN}Passed:${NC}  $PASSED"
echo -e "${RED}Failed:${NC}  $FAILED"
echo -e "${YELLOW}Skipped:${NC} $SKIPPED"
echo "========================================"

TOTAL=$((PASSED + FAILED))
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All $TOTAL tests passed!${NC}"
    exit 0
else
    echo -e "${RED}$FAILED test(s) failed out of $TOTAL${NC}"
    exit 1
fi
