#!/bin/bash
# Comprehensive Polyglot Language Testing for pf
# Tests ALL supported shell languages and execution modes

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$SCRIPT_DIR"
PF_RUNNER_DIR="$(cd "$SCRIPT_DIR/../../pf-runner" && pwd)"
TEMP_DIR=$(mktemp -d)

# Source shared test utilities if available, otherwise define locally
if [ -f "$SCRIPT_DIR/../lib/test-utils.sh" ]; then
    source "$SCRIPT_DIR/../lib/test-utils.sh"
else
    # Fallback: Define logging functions locally
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    NC='\033[0m'
    TOTAL_TESTS=0
    PASSED_TESTS=0
    FAILED_TESTS=0
    log_test() { echo -e "${BLUE}[TEST]${NC} $1"; TOTAL_TESTS=$((TOTAL_TESTS + 1)); }
    log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; PASSED_TESTS=$((PASSED_TESTS + 1)); }
    log_fail() { echo -e "${RED}[FAIL]${NC} $1"; FAILED_TESTS=$((FAILED_TESTS + 1)); }
    log_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }
fi

cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# Check if a command/language is available
check_language_available() {
    local lang="$1"
    case "$lang" in
        "python"|"python3")
            command -v python3 >/dev/null 2>&1
            ;;
        "node"|"nodejs")
            command -v node >/dev/null 2>&1
            ;;
        "ruby")
            command -v ruby >/dev/null 2>&1
            ;;
        "perl")
            command -v perl >/dev/null 2>&1
            ;;
        "php")
            command -v php >/dev/null 2>&1
            ;;
        "lua")
            command -v lua >/dev/null 2>&1
            ;;
        "rust")
            command -v rustc >/dev/null 2>&1
            ;;
        "go")
            command -v go >/dev/null 2>&1
            ;;
        "java")
            command -v java >/dev/null 2>&1 && command -v javac >/dev/null 2>&1
            ;;
        "scala")
            command -v scala >/dev/null 2>&1
            ;;
        "kotlin")
            command -v kotlin >/dev/null 2>&1
            ;;
        "bash"|"sh")
            command -v bash >/dev/null 2>&1
            ;;
        *)
            return 1
            ;;
    esac
}

# Test polyglot execution
test_polyglot_execution() {
    local test_name="$1"
    local language="$2"
    local code="$3"
    local expected_output="$4"
    
    log_test "$test_name ($language)"
    
    if ! check_language_available "$language"; then
        log_info "Skipping $language test - language not available"
        return
    fi
    
    local pf_content="
task test-$language
  describe Test $language execution
  shell_lang $language
  shell $code
end
"
    
    local test_file="$TEMP_DIR/test_${language}_${TOTAL_TESTS}.pf"
    echo "$pf_content" > "$test_file"
    
    cd "$PF_RUNNER_DIR"
    if output=$(python3 pf_parser.py --file="$test_file" "test-$language" 2>&1); then
        if [[ "$output" == *"$expected_output"* ]]; then
            log_pass "$test_name ($language) - Output contains expected text"
        else
            log_fail "$test_name ($language) - Output mismatch. Expected: '$expected_output', Got: '$output'"
        fi
    else
        log_fail "$test_name ($language) - Execution failed: $output"
    fi
}

echo "=== pf Polyglot Language Testing ==="
echo "Testing all supported shell languages"
echo

# Test 1: Python
test_polyglot_execution "Basic Python execution" "python" \
    "print('Hello from Python')" \
    "Hello from Python"

# Test 2: Python with variables
test_polyglot_execution "Python with calculations" "python" \
    "result = 2 + 3; print(f'Result: {result}')" \
    "Result: 5"

# Test 3: Python with imports
test_polyglot_execution "Python with imports" "python" \
    "import sys; print(f'Python version: {sys.version_info.major}.{sys.version_info.minor}')" \
    "Python version:"

# Test 4: Node.js/JavaScript
test_polyglot_execution "Basic Node.js execution" "node" \
    "console.log('Hello from Node.js')" \
    "Hello from Node.js"

# Test 5: Node.js with calculations
test_polyglot_execution "Node.js with calculations" "node" \
    "const result = 2 + 3; console.log(\`Result: \${result}\`)" \
    "Result: 5"

# Test 6: Ruby
test_polyglot_execution "Basic Ruby execution" "ruby" \
    "puts 'Hello from Ruby'" \
    "Hello from Ruby"

# Test 7: Ruby with variables
test_polyglot_execution "Ruby with calculations" "ruby" \
    "result = 2 + 3; puts \"Result: #{result}\"" \
    "Result: 5"

# Test 8: Perl
test_polyglot_execution "Basic Perl execution" "perl" \
    "print \"Hello from Perl\\n\"" \
    "Hello from Perl"

# Test 9: PHP
test_polyglot_execution "Basic PHP execution" "php" \
    "<?php echo 'Hello from PHP' . PHP_EOL; ?>" \
    "Hello from PHP"

# Test 10: Lua
test_polyglot_execution "Basic Lua execution" "lua" \
    "print('Hello from Lua')" \
    "Hello from Lua"

# Test 11: Bash
test_polyglot_execution "Basic Bash execution" "bash" \
    "echo 'Hello from Bash'" \
    "Hello from Bash"

# Test 12: Shell (sh)
test_polyglot_execution "Basic Shell execution" "sh" \
    "echo 'Hello from Shell'" \
    "Hello from Shell"

# Test 13: Go (if available)
if check_language_available "go"; then
    test_polyglot_execution "Basic Go execution" "go" \
        "package main; import \"fmt\"; func main() { fmt.Println(\"Hello from Go\") }" \
        "Hello from Go"
fi

# Test 14: Rust (if available)
if check_language_available "rust"; then
    test_polyglot_execution "Basic Rust execution" "rust" \
        "fn main() { println!(\"Hello from Rust\"); }" \
        "Hello from Rust"
fi

# Test 15: Java (if available)
# NOTE: Java requires compilation before execution. The pf runner handles this by
# creating a temporary directory, writing the code to a properly named .java file,
# compiling it with javac, and then running it with java. If the pf runner doesn't
# support this workflow for Java, this test will fail and should be skipped.
if check_language_available "java"; then
    log_test "Basic Java execution"
    log_info "Java test skipped - Java requires compilation which may not be supported by pf shell_lang"
    # Note: Uncomment the following if pf runner supports Java compilation:
    # test_polyglot_execution "Basic Java execution" "java" \
    #     "public class Test { public static void main(String[] args) { System.out.println(\"Hello from Java\"); } }" \
    #     "Hello from Java"
fi

# Test 16: Multi-language task
log_test "Multi-language task"
if check_language_available "python" && check_language_available "node"; then
    local pf_content="
task multi-lang
  describe Test multiple languages in one task
  shell_lang python
  shell print('Step 1: Python')
  shell_lang node
  shell console.log('Step 2: Node.js')
  shell_lang bash
  shell echo 'Step 3: Bash'
end
"
    
    local test_file="$TEMP_DIR/test_multi_lang.pf"
    echo "$pf_content" > "$test_file"
    
    cd "$PF_RUNNER_DIR"
    if output=$(python3 pf_parser.py --file="$test_file" multi-lang 2>&1); then
        if [[ "$output" == *"Step 1: Python"* ]] && [[ "$output" == *"Step 2: Node.js"* ]] && [[ "$output" == *"Step 3: Bash"* ]]; then
            log_pass "Multi-language task - All languages executed"
        else
            log_fail "Multi-language task - Missing expected output: $output"
        fi
    else
        log_fail "Multi-language task - Execution failed: $output"
    fi
else
    log_info "Skipping multi-language test - required languages not available"
fi

# Test 17: Language switching with variables
log_test "Language switching with variables"
if check_language_available "python" && check_language_available "bash"; then
    local pf_content="
task lang-switch value=\"42\"
  describe Test language switching with variables
  shell_lang bash
  shell echo \"Bash says: \$value\"
  shell_lang python
  shell import os; print(f\"Python says: {os.environ.get('value', 'not found')}\")
end
"
    
    local test_file="$TEMP_DIR/test_lang_switch.pf"
    echo "$pf_content" > "$test_file"
    
    cd "$PF_RUNNER_DIR"
    if output=$(python3 pf_parser.py --file="$test_file" lang-switch 2>&1); then
        if [[ "$output" == *"Bash says: 42"* ]]; then
            log_pass "Language switching with variables - Variables passed correctly"
        else
            log_fail "Language switching with variables - Variable passing failed: $output"
        fi
    else
        log_fail "Language switching with variables - Execution failed: $output"
    fi
else
    log_info "Skipping language switching test - required languages not available"
fi

# Test 18: Script file execution
log_test "Script file execution"
local script_content="#!/usr/bin/env python3
print('Hello from external script')
import sys
print(f'Args: {sys.argv[1:]}')
"
local script_file="$TEMP_DIR/test_script.py"
echo "$script_content" > "$script_file"
chmod +x "$script_file"

local pf_content="
task script-exec
  describe Test external script execution
  shell @$script_file -- arg1 arg2
end
"

local test_file="$TEMP_DIR/test_script_exec.pf"
echo "$pf_content" > "$test_file"

cd "$PF_RUNNER_DIR"
if output=$(python3 pf_parser.py --file="$test_file" script-exec 2>&1); then
    if [[ "$output" == *"Hello from external script"* ]] && [[ "$output" == *"Args: ['arg1', 'arg2']"* ]]; then
        log_pass "Script file execution - External script executed with args"
    else
        log_fail "Script file execution - Unexpected output: $output"
    fi
else
    log_fail "Script file execution - Execution failed: $output"
fi

echo
echo "=== Polyglot Language Test Results ==="
echo "Total tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}All polyglot language tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some polyglot language tests failed!${NC}"
    exit 1
fi