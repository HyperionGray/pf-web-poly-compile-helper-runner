#!/bin/bash
# Comprehensive Grammar Testing for pf Language
# Tests every grammar rule defined in pf-runner/pf.lark

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

# Test helper function
test_pf_syntax() {
    local test_name="$1"
    local pf_content="$2"
    local should_pass="$3"  # true/false
    
    log_test "$test_name"
    
    local test_file="$TEMP_DIR/test_${TOTAL_TESTS}.pf"
    echo "$pf_content" > "$test_file"
    
    cd "$PF_RUNNER_DIR"
    if python3 pf_parser.py list --file="$test_file" >/dev/null 2>&1; then
        if [ "$should_pass" = "true" ]; then
            log_pass "$test_name - Valid syntax accepted"
        else
            log_fail "$test_name - Invalid syntax incorrectly accepted"
        fi
    else
        if [ "$should_pass" = "false" ]; then
            log_pass "$test_name - Invalid syntax correctly rejected"
        else
            log_fail "$test_name - Valid syntax incorrectly rejected"
        fi
    fi
}

echo "=== pf Language Grammar Testing ==="
echo "Testing all grammar rules from pf.lark"
echo

# Test 1: Basic task definition
test_pf_syntax "Basic task definition" "
task hello
  describe Simple hello task
  shell echo \"Hello World\"
end
" "true"

# Test 2: Task with parameters
test_pf_syntax "Task with parameters" "
task greet name=\"World\" greeting=\"Hello\"
  describe Greet someone
  shell echo \"\$greeting \$name\"
end
" "true"

# Test 3: Global environment variables
test_pf_syntax "Global environment variables" "
env PROJECT_NAME=\"MyProject\"
env VERSION=\"1.0.0\"

task show-env
  describe Show environment
  shell echo \"Project: \$PROJECT_NAME v\$VERSION\"
end
" "true"

# Test 4: Task-local environment variables
test_pf_syntax "Task-local environment variables" "
task build
  describe Build with custom env
  env CC=gcc CFLAGS=\"-O2 -Wall\"
  shell \$CC \$CFLAGS -o hello hello.c
end
" "true"

# Test 5: Shell language specification
test_pf_syntax "Shell language specification" "
task python-example
  describe Run Python code
  shell_lang python
  shell print(\"Hello from Python\")
  shell import sys; print(sys.version)
end
" "true"

# Test 6: Variable interpolation - simple
test_pf_syntax "Variable interpolation simple" "
task test-vars name=\"test\"
  describe Test variable interpolation
  shell echo \"Name is \$name\"
end
" "true"

# Test 7: Variable interpolation - braces
test_pf_syntax "Variable interpolation braces" "
task test-vars-braces prefix=\"test\"
  describe Test variable interpolation with braces
  shell echo \"File: \${prefix}_file.txt\"
end
" "true"

# Test 8: If statement - variable equals
test_pf_syntax "If statement variable equals" "
task conditional mode=\"dev\"
  describe Conditional execution
  if \$mode == \"dev\"
    shell echo \"Development mode\"
  else
    shell echo \"Production mode\"
  end
end
" "true"

# Test 9: If statement - variable exists
test_pf_syntax "If statement variable exists" "
task check-var debug=\"true\"
  describe Check if variable exists
  if \$debug
    shell echo \"Debug mode enabled\"
  end
end
" "true"

# Test 10: If statement - command succeeds
test_pf_syntax "If statement command succeeds" "
task check-command
  describe Check command success
  if \`which gcc\`
    shell echo \"GCC is available\"
  else
    shell echo \"GCC not found\"
  end
end
" "true"

# Test 11: For loop with array
test_pf_syntax "For loop with array" "
task process-files
  describe Process multiple files
  for file in [\"file1.txt\", \"file2.txt\", \"file3.txt\"]
    shell echo \"Processing \$file\"
  end
end
" "true"

# Test 12: For loop with variable
test_pf_syntax "For loop with variable" "
task process-list items=\"item1,item2,item3\"
  describe Process items from variable
  for item in \$items
    shell echo \"Item: \$item\"
  end
end
" "true"

# Test 13: Sync statement
test_pf_syntax "Sync statement" "
task sync-files
  describe Sync files with rsync
  sync src=\"/local/path\" dst=\"user@host:/remote/path\" verbose recursive
end
" "true"

# Test 14: Packages management
test_pf_syntax "Package management" "
task install-deps
  describe Install dependencies
  packages install gcc make cmake
end

task remove-deps
  describe Remove dependencies
  packages remove old-package
end
" "true"

# Test 15: Service management
test_pf_syntax "Service management" "
task manage-service
  describe Manage system service
  service start nginx
  service enable nginx
  service restart apache2
  service stop mysql
  service disable postgresql
end
" "true"

# Test 16: Directory creation
test_pf_syntax "Directory creation" "
task setup-dirs
  describe Create directories
  directory /tmp/build mode=0755
  directory /var/log/myapp
end
" "true"

# Test 17: File copy
test_pf_syntax "File copy" "
task copy-files
  describe Copy configuration files
  copy config.conf /etc/myapp/ mode=0644 user=root group=root
end
" "true"

# Test 18: Build system helpers - Makefile
test_pf_syntax "Makefile build helper" "
task build-make
  describe Build with Make
  makefile clean all
  make install PREFIX=/usr/local
end
" "true"

# Test 19: Build system helpers - CMake
test_pf_syntax "CMake build helper" "
task build-cmake
  describe Build with CMake
  cmake -DCMAKE_BUILD_TYPE=Release
end
" "true"

# Test 20: Build system helpers - Meson
test_pf_syntax "Meson build helper" "
task build-meson
  describe Build with Meson
  meson setup builddir
  ninja -C builddir
end
" "true"

# Test 21: Build system helpers - Cargo
test_pf_syntax "Cargo build helper" "
task build-rust
  describe Build Rust project
  cargo build --release
  cargo test
end
" "true"

# Test 22: Build system helpers - Go
test_pf_syntax "Go build helper" "
task build-go
  describe Build Go project
  go_build -o myapp main.go
  gobuild -ldflags=\"-s -w\"
end
" "true"

# Test 23: Build system helpers - Configure
test_pf_syntax "Configure build helper" "
task build-autotools
  describe Build with autotools
  configure --prefix=/usr/local --enable-shared
end
" "true"

# Test 24: Build system helpers - Justfile
test_pf_syntax "Justfile build helper" "
task build-just
  describe Build with Just
  justfile build
  just test
end
" "true"

# Test 25: Build system helpers - Autobuild
test_pf_syntax "Autobuild helper" "
task auto-build
  describe Auto-detect and build
  autobuild
  auto_build --verbose
end
" "true"

# Test 26: Build system helpers - Build detect
test_pf_syntax "Build detect helper" "
task detect-build
  describe Detect build system
  build_detect
  detect_build
end
" "true"

# Test 27: Comments
test_pf_syntax "Comments" "
# This is a comment
task example
  # Another comment
  describe Example task with comments
  shell echo \"Hello\" # Inline comment
end
# Final comment
" "true"

# Test 28: Include statements
test_pf_syntax "Include statements" "
# Include other task files
include other.pf
include tasks/web.pf

task main
  describe Main task
  shell echo \"Main task\"
end
" "true"

# Test 29: Complex parameter combinations
test_pf_syntax "Complex parameters" "
task complex-task host=\"localhost\" port=\"8080\" ssl=\"false\" workers=\"4\"
  describe Complex task with multiple parameters
  if \$ssl == \"true\"
    shell echo \"Starting HTTPS server on \$host:\$port with \$workers workers\"
  else
    shell echo \"Starting HTTP server on \$host:\$port with \$workers workers\"
  end
end
" "true"

# Test 30: Nested control flow
test_pf_syntax "Nested control flow" "
task nested-logic env=\"dev\" debug=\"true\"
  describe Nested if statements and loops
  if \$env == \"dev\"
    if \$debug == \"true\"
      for level in [\"info\", \"debug\", \"trace\"]
        shell echo \"Setting log level: \$level\"
      end
    else
      shell echo \"Development mode without debug\"
    end
  else
    shell echo \"Production mode\"
  end
end
" "true"

# NEGATIVE TESTS - These should fail

# Test 31: Invalid task syntax - missing end
test_pf_syntax "Invalid task - missing end" "
task broken
  describe This task is missing end
  shell echo \"broken\"
" "false"

# Test 32: Invalid parameter syntax
test_pf_syntax "Invalid parameter syntax" "
task bad-params invalid=param=value
  describe Bad parameter syntax
  shell echo \"bad\"
end
" "false"

# Test 33: Invalid if syntax
test_pf_syntax "Invalid if syntax" "
task bad-if
  describe Bad if statement
  if \$var === \"value\"  # Wrong operator
    shell echo \"bad\"
  end
end
" "false"

# Test 34: Invalid for loop syntax
test_pf_syntax "Invalid for loop syntax" "
task bad-for
  describe Bad for loop
  for item [\"a\", \"b\"]  # Missing 'in'
    shell echo \$item
  end
end
" "false"

# Test 35: Invalid variable syntax
test_pf_syntax "Invalid variable syntax" "
task bad-var
  describe Bad variable reference
  shell echo \$123invalid  # Variables can't start with numbers
end
" "false"

# Test 36: Invalid sync syntax
test_pf_syntax "Invalid sync syntax" "
task bad-sync
  describe Bad sync statement
  sync invalid-key=\"value\"  # Invalid sync parameter
end
" "false"

# Test 37: Invalid service action
test_pf_syntax "Invalid service action" "
task bad-service
  describe Bad service action
  service invalid-action nginx  # Invalid action
end
" "false"

# Test 38: Invalid package action
test_pf_syntax "Invalid package action" "
task bad-packages
  describe Bad package action
  packages invalid-action package-name  # Invalid action
end
" "false"

# Test 39: Unclosed string
test_pf_syntax "Unclosed string" "
task bad-string
  describe Unclosed string test
  shell echo \"unclosed string
end
" "false"

# Test 40: Invalid shell_lang
test_pf_syntax "Invalid shell_lang" "
task bad-shell-lang
  describe Invalid shell language
  shell_lang 123invalid  # Invalid identifier
  shell echo \"test\"
end
" "false"

echo
echo "=== Grammar Test Results ==="
echo "Total tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}All grammar tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some grammar tests failed!${NC}"
    exit 1
fi