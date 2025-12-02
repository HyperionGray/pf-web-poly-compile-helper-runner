#!/bin/bash
# Comprehensive Feature Testing for pf Language
# Tests ALL DSL features through actual execution

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$SCRIPT_DIR"
PF_RUNNER_DIR="$(cd "$SCRIPT_DIR/../../pf-runner" && pwd)"
TEMP_DIR=$(mktemp -d)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    FAILED_TESTS=$((FAILED_TESTS + 1))
}

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Test helper function
test_pf_execution() {
    local test_name="$1"
    local pf_content="$2"
    local task_name="$3"
    local expected_output="$4"
    local params="$5"
    
    log_test "$test_name"
    
    local test_file="$TEMP_DIR/test_${TOTAL_TESTS}.pf"
    echo "$pf_content" > "$test_file"
    
    cd "$PF_RUNNER_DIR"
    if output=$(python3 pf_parser.py --file="$test_file" "$task_name" $params 2>&1); then
        if [[ "$output" == *"$expected_output"* ]]; then
            log_pass "$test_name - Output contains expected text"
        else
            log_fail "$test_name - Output mismatch. Expected: '$expected_output', Got: '$output'"
        fi
    else
        log_fail "$test_name - Execution failed: $output"
    fi
}

echo "=== pf Language Feature Testing ==="
echo "Testing all DSL features through execution"
echo

# Test 1: Basic shell command
test_pf_execution "Basic shell command" "
task hello
  describe Simple hello task
  shell echo \"Hello World\"
end
" "hello" "Hello World" ""

# Test 2: Parameter interpolation
test_pf_execution "Parameter interpolation" "
task greet name=\"Alice\"
  describe Greet with parameter
  shell echo \"Hello \$name\"
end
" "greet" "Hello Alice" ""

# Test 3: Parameter override
test_pf_execution "Parameter override" "
task greet name=\"Default\"
  describe Greet with parameter
  shell echo \"Hello \$name\"
end
" "greet" "Hello Bob" "name=Bob"

# Test 4: Environment variable usage
test_pf_execution "Environment variable usage" "
env PROJECT=\"TestProject\"

task show-project
  describe Show project name
  shell echo \"Project: \$PROJECT\"
end
" "show-project" "Project: TestProject" ""

# Test 5: Task-local environment
test_pf_execution "Task-local environment" "
task build-info
  describe Show build info
  env BUILD_TYPE=debug VERSION=1.0
  shell echo \"Build: \$BUILD_TYPE v\$VERSION\"
end
" "build-info" "Build: debug v1.0" ""

# Test 6: Multiple shell languages
test_pf_execution "Python shell language" "
task python-test
  describe Test Python execution
  shell_lang python
  shell print('Hello from Python')
end
" "python-test" "Hello from Python" ""

# Test 7: Conditional execution - true case
test_pf_execution "Conditional execution true" "
task conditional mode=\"dev\"
  describe Test if statement
  if \$mode == \"dev\"
    shell echo \"Development mode active\"
  else
    shell echo \"Production mode active\"
  end
end
" "conditional" "Development mode active" ""

# Test 8: Conditional execution - false case
test_pf_execution "Conditional execution false" "
task conditional mode=\"prod\"
  describe Test if statement
  if \$mode == \"dev\"
    shell echo \"Development mode active\"
  else
    shell echo \"Production mode active\"
  end
end
" "conditional" "Production mode active" ""

# Test 9: Variable existence check
test_pf_execution "Variable existence check" "
task check-debug debug=\"true\"
  describe Check if debug is set
  if \$debug
    shell echo \"Debug enabled\"
  end
end
" "check-debug" "Debug enabled" ""

# Test 10: Command success check
test_pf_execution "Command success check" "
task check-command
  describe Check command availability
  if \`echo test\`
    shell echo \"Command succeeded\"
  else
    shell echo \"Command failed\"
  end
end
" "check-command" "Command succeeded" ""

# Test 11: For loop with array
test_pf_execution "For loop with array" "
task process-items
  describe Process array items
  for item in [\"apple\", \"banana\", \"cherry\"]
    shell echo \"Processing \$item\"
  end
end
" "process-items" "Processing apple" ""

# Test 12: Directory operations
test_pf_execution "Directory operations" "
task create-dirs
  describe Create test directories
  directory $TEMP_DIR/test1
  directory $TEMP_DIR/test2 mode=0755
  shell ls -la $TEMP_DIR/test*
end
" "create-dirs" "test1" ""

# Test 13: Build system detection
test_pf_execution "Build system detection" "
task detect-build-system
  describe Detect available build systems
  build_detect
end
" "detect-build-system" "" ""

# Test 14: Makefile integration
test_pf_execution "Makefile integration" "
task makefile-test
  describe Test Makefile integration
  makefile --version
end
" "makefile-test" "" ""

# Test 15: Multiple parameters
test_pf_execution "Multiple parameters" "
task multi-param host=\"localhost\" port=\"8080\" ssl=\"false\"
  describe Test multiple parameters
  shell echo \"Server: \$host:\$port (SSL: \$ssl)\"
end
" "multi-param" "Server: localhost:8080 (SSL: false)" ""

# Test 16: Parameter override multiple
test_pf_execution "Multiple parameter override" "
task multi-param host=\"localhost\" port=\"8080\" ssl=\"false\"
  describe Test multiple parameters
  shell echo \"Server: \$host:\$port (SSL: \$ssl)\"
end
" "multi-param" "Server: example.com:443 (SSL: true)" "host=example.com port=443 ssl=true"

# Test 17: Nested conditionals
test_pf_execution "Nested conditionals" "
task nested-logic env=\"dev\" debug=\"true\"
  describe Test nested conditions
  if \$env == \"dev\"
    if \$debug == \"true\"
      shell echo \"Development with debug\"
    else
      shell echo \"Development without debug\"
    end
  else
    shell echo \"Production mode\"
  end
end
" "nested-logic" "Development with debug" ""

# Test 18: Complex variable interpolation
test_pf_execution "Complex variable interpolation" "
task complex-vars prefix=\"test\" suffix=\"log\"
  describe Test complex variable interpolation
  shell echo \"File: \${prefix}_output.\${suffix}\"
end
" "complex-vars" "File: test_output.log" ""

# Test 19: Environment variable inheritance
test_pf_execution "Environment inheritance" "
env GLOBAL_VAR=\"global_value\"

task env-inherit
  describe Test environment inheritance
  env LOCAL_VAR=\"local_value\"
  shell echo \"Global: \$GLOBAL_VAR, Local: \$LOCAL_VAR\"
end
" "env-inherit" "Global: global_value, Local: local_value" ""

# Test 20: Shell command chaining
test_pf_execution "Shell command chaining" "
task command-chain
  describe Test multiple shell commands
  shell echo \"First command\"
  shell echo \"Second command\"
  shell echo \"Third command\"
end
" "command-chain" "First command" ""

echo
echo "=== Feature Test Results ==="
echo "Total tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}All feature tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some feature tests failed!${NC}"
    exit 1
fi