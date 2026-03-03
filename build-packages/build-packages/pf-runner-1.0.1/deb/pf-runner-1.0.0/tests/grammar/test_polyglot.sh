#!/bin/bash
# test_polyglot.sh - Unit tests for polyglot shell language support
# Tests documentation and configuration for all supported languages

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

TEST_DIR=$(mktemp -d)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PF_RUNNER="$REPO_ROOT/pf-runner"
PF_CMD="python3 $PF_RUNNER/pf_parser.py"

echo "Testing polyglot language documentation and configuration"
echo "Test directory: $TEST_DIR"
echo ""

trap 'rm -rf "$TEST_DIR"' EXIT

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

# ==============================================================================
section "1. Documentation Files Exist"
# ==============================================================================

# Test 1.1: LANGS.md exists
if [ -f "$REPO_ROOT/pf-runner/LANGS.md" ]; then
    pass "LANGS.md documentation exists"
else
    fail "LANGS.md documentation exists" "File not found"
fi

# Test 1.2: README documents polyglot support
if grep -q "polyglot\|shell_lang" "$REPO_ROOT/pf-runner/README.md" 2>/dev/null; then
    pass "README documents polyglot support"
else
    fail "README documents polyglot support" "Not found in README"
fi

# ==============================================================================
section "2. Shell Languages Documented"
# ==============================================================================

LANGS_FILE="$REPO_ROOT/pf-runner/LANGS.md"

# Test shells documented
for lang in bash sh dash zsh fish ksh tcsh pwsh; do
    if grep -qi "$lang" "$LANGS_FILE" 2>/dev/null; then
        pass "$lang documented in LANGS.md"
    else
        fail "$lang documented in LANGS.md" "Not found"
    fi
done

# ==============================================================================
section "3. Scripting Languages Documented"
# ==============================================================================

# Test scripting languages documented
for lang in python node perl ruby lua php; do
    if grep -qi "$lang" "$LANGS_FILE" 2>/dev/null; then
        pass "$lang documented in LANGS.md"
    else
        fail "$lang documented in LANGS.md" "Not found"
    fi
done

# ==============================================================================
section "4. Compiled Languages Documented"
# ==============================================================================

# Test compiled languages documented
for lang in c cpp rust go fortran; do
    if grep -qi "$lang" "$LANGS_FILE" 2>/dev/null; then
        pass "$lang documented in LANGS.md"
    else
        fail "$lang documented in LANGS.md" "Not found"
    fi
done

# ==============================================================================
section "5. LLVM IR Languages Documented"
# ==============================================================================

# Test LLVM variants documented
for lang in c-llvm cpp-llvm fortran-llvm; do
    if grep -qi "$lang" "$LANGS_FILE" 2>/dev/null; then
        pass "$lang documented in LANGS.md"
    else
        fail "$lang documented in LANGS.md" "Not found"
    fi
done

# ==============================================================================
section "6. Parser Has POLYGLOT_LANGS Dictionary"
# ==============================================================================

# Test parser has language definitions
if grep -q "POLYGLOT_LANGS" "$REPO_ROOT/pf-runner/pf_parser.py" 2>/dev/null; then
    pass "Parser defines POLYGLOT_LANGS dictionary"
else
    fail "Parser defines POLYGLOT_LANGS dictionary" "Not found"
fi

# Test parser has language aliases
if grep -q "POLYGLOT_ALIASES" "$REPO_ROOT/pf-runner/pf_parser.py" 2>/dev/null; then
    pass "Parser defines POLYGLOT_ALIASES dictionary"
else
    fail "Parser defines POLYGLOT_ALIASES dictionary" "Not found"
fi

# ==============================================================================
section "7. Basic Shell Command Works"
# ==============================================================================

# Test basic shell (always works)
cat > "$TEST_DIR/test.pf" << 'EOF'
task test-shell
  shell echo "Shell command works"
end
EOF

if $PF_CMD "$TEST_DIR/test.pf" test-shell 2>&1 | grep -q "Shell command works"; then
    pass "Basic shell command execution"
else
    fail "Basic shell command execution" "Shell failed"
fi

# ==============================================================================
section "8. Language Aliases Documented"
# ==============================================================================

# Test common aliases from README
README_FILE="$REPO_ROOT/pf-runner/README.md"

ALIASES=(
    "py→python"
    "js→node"
    "golang→go"
    "shell→bash"
)

echo "Checking language alias documentation..."
for alias_pair in "${ALIASES[@]}"; do
    ALIAS="${alias_pair%%→*}"
    if grep -qi "$ALIAS" "$README_FILE" 2>/dev/null; then
        pass "Alias '$ALIAS' documented"
    else
        skip "Alias '$ALIAS' documented" "May not be documented"
    fi
done

# ==============================================================================
section "9. Grammar File Exists and Documents Languages"
# ==============================================================================

# Test grammar file documents shell_lang
GRAMMAR_FILE="$REPO_ROOT/pf-runner/pf.lark"

if [ -f "$GRAMMAR_FILE" ]; then
    pass "Grammar file exists (pf.lark)"
    
    if grep -q "shell_lang" "$GRAMMAR_FILE"; then
        pass "Grammar documents shell_lang"
    else
        fail "Grammar documents shell_lang" "Not found in grammar"
    fi
    
    if grep -q "shell:" "$GRAMMAR_FILE"; then
        pass "Grammar documents shell command"
    else
        fail "Grammar documents shell command" "Not found in grammar"
    fi
else
    fail "Grammar file exists" "pf.lark not found"
fi

# ==============================================================================
# Summary
# ==============================================================================

echo ""
echo "========================================"
echo -e "${BLUE}Polyglot Test Summary${NC}"
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
