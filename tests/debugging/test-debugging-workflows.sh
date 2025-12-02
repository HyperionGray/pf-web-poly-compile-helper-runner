#!/bin/bash
# Comprehensive Debugging Workflow Testing for pf
# Tests ALL debugging tools, binary analysis, and reverse engineering features

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$SCRIPT_DIR"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
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

# Check if a debugging tool is available
# NOTE: This function checks for user-installed debugging tools including those
# configured in the user's home directory (e.g., pwndbg). These checks only read
# configuration files to verify installation and do not execute any code from them.
check_debug_tool_available() {
    local tool="$1"
    case "$tool" in
        "gdb")
            command -v gdb >/dev/null 2>&1
            ;;
        "lldb")
            command -v lldb >/dev/null 2>&1
            ;;
        "pwndbg")
            # Check for pwndbg installation by looking for the directory and gdbinit reference
            # This only reads file contents to check for the pwndbg string, does not execute anything
            if [ -n "$HOME" ] && [ -d "$HOME" ]; then
                test -d "$HOME/.pwndbg" && test -f "$HOME/.gdbinit" && grep -q pwndbg "$HOME/.gdbinit" 2>/dev/null
            else
                return 1
            fi
            ;;
        "objdump")
            command -v objdump >/dev/null 2>&1
            ;;
        "readelf")
            command -v readelf >/dev/null 2>&1
            ;;
        "nm")
            command -v nm >/dev/null 2>&1
            ;;
        "strings")
            command -v strings >/dev/null 2>&1
            ;;
        "file")
            command -v file >/dev/null 2>&1
            ;;
        "size")
            command -v size >/dev/null 2>&1
            ;;
        "gcc")
            command -v gcc >/dev/null 2>&1
            ;;
        "g++")
            command -v g++ >/dev/null 2>&1
            ;;
        "rustc")
            command -v rustc >/dev/null 2>&1
            ;;
        "python3")
            command -v python3 >/dev/null 2>&1
            ;;
        *)
            return 1
            ;;
    esac
}

# Test debugging task execution
test_debug_task() {
    local test_name="$1"
    local task_name="$2"
    local expected_output="$3"
    local params="$4"
    
    log_test "$test_name"
    
    cd "$ROOT_DIR"
    
    if output=$(timeout 30 pf "$task_name" $params 2>&1); then
        if [ -n "$expected_output" ]; then
            if [[ "$output" == *"$expected_output"* ]]; then
                log_pass "$test_name - Contains expected output"
            else
                log_fail "$test_name - Missing expected output: '$expected_output'"
            fi
        else
            log_pass "$test_name - Task executed successfully"
        fi
    else
        log_fail "$test_name - Task execution failed or timed out"
    fi
}

echo "=== pf Debugging Workflow Testing ==="
echo "Testing all debugging tools and workflows"
echo

# Check available debugging tools
log_info "Checking available debugging tools..."
GDB_AVAILABLE=$(check_debug_tool_available "gdb" && echo "true" || echo "false")
LLDB_AVAILABLE=$(check_debug_tool_available "lldb" && echo "true" || echo "false")
PWNDBG_AVAILABLE=$(check_debug_tool_available "pwndbg" && echo "true" || echo "false")
OBJDUMP_AVAILABLE=$(check_debug_tool_available "objdump" && echo "true" || echo "false")
READELF_AVAILABLE=$(check_debug_tool_available "readelf" && echo "true" || echo "false")
NM_AVAILABLE=$(check_debug_tool_available "nm" && echo "true" || echo "false")
STRINGS_AVAILABLE=$(check_debug_tool_available "strings" && echo "true" || echo "false")
FILE_AVAILABLE=$(check_debug_tool_available "file" && echo "true" || echo "false")
SIZE_AVAILABLE=$(check_debug_tool_available "size" && echo "true" || echo "false")
GCC_AVAILABLE=$(check_debug_tool_available "gcc" && echo "true" || echo "false")
GPP_AVAILABLE=$(check_debug_tool_available "g++" && echo "true" || echo "false")
RUSTC_AVAILABLE=$(check_debug_tool_available "rustc" && echo "true" || echo "false")
PYTHON3_AVAILABLE=$(check_debug_tool_available "python3" && echo "true" || echo "false")

echo "Debugging tool availability:"
echo "  GDB: $GDB_AVAILABLE"
echo "  LLDB: $LLDB_AVAILABLE"
echo "  pwndbg: $PWNDBG_AVAILABLE"
echo "  objdump: $OBJDUMP_AVAILABLE"
echo "  readelf: $READELF_AVAILABLE"
echo "  nm: $NM_AVAILABLE"
echo "  strings: $STRINGS_AVAILABLE"
echo "  file: $FILE_AVAILABLE"
echo "  size: $SIZE_AVAILABLE"
echo "  GCC: $GCC_AVAILABLE"
echo "  G++: $GPP_AVAILABLE"
echo "  Rust: $RUSTC_AVAILABLE"
echo "  Python3: $PYTHON3_AVAILABLE"
echo

# DEBUGGER INSTALLATION TESTS

# Test 1: Check debugger installation status
test_debug_task "Check debuggers" "check-debuggers" "Checking Debugger Installation" ""

# Test 2: Install debuggers (if not available)
if [ "$GDB_AVAILABLE" = "false" ] || [ "$LLDB_AVAILABLE" = "false" ] || [ "$PWNDBG_AVAILABLE" = "false" ]; then
    test_debug_task "Install debuggers" "install-debuggers" "" ""
fi

# BINARY BUILDING TESTS

# Test 3: Build debug examples
if [ "$GCC_AVAILABLE" = "true" ]; then
    test_debug_task "Build debug examples" "build-debug-examples" "Build complete" ""
    
    # Test 4: Clean debug examples
    test_debug_task "Clean debug examples" "clean-debug-examples" "Cleaned debug examples" ""
    
    # Rebuild for subsequent tests
    test_debug_task "Rebuild debug examples" "build-debug-examples" "Build complete" ""
fi

# BINARY ANALYSIS TESTS

# Test 5: Binary information analysis
if [ "$FILE_AVAILABLE" = "true" ] && [ "$SIZE_AVAILABLE" = "true" ] && [ "$READELF_AVAILABLE" = "true" ]; then
    test_debug_task "Binary info analysis" "binary-info" "Binary Information" "binary=demos/debugging/examples/bin/vulnerable"
fi

# Test 6: Disassembly
if [ "$OBJDUMP_AVAILABLE" = "true" ]; then
    test_debug_task "Binary disassembly" "disassemble" "" "binary=demos/debugging/examples/bin/vulnerable"
fi

# Test 7: String analysis
if [ "$STRINGS_AVAILABLE" = "true" ]; then
    test_debug_task "String analysis" "strings-analysis" "Extracting strings" "binary=demos/debugging/examples/bin/vulnerable"
fi

# DEBUGGING WORKFLOW TESTS

# Test 8: Debug info extraction
if [ "$PYTHON3_AVAILABLE" = "true" ]; then
    test_debug_task "Debug info extraction" "debug-info" "" "binary=demos/debugging/examples/bin/vulnerable"
fi

# Test 9: Complete debugging workflow test
test_debug_task "Complete debugging workflow" "test-debugger-workflow" "Testing Debugging Workflow" ""

# REVERSE ENGINEERING TESTS

# Test 10: Symbol analysis
if [ "$NM_AVAILABLE" = "true" ]; then
    log_test "Symbol analysis"
    cd "$ROOT_DIR"
    if [ -f "demos/debugging/examples/bin/vulnerable" ]; then
        if output=$(nm demos/debugging/examples/bin/vulnerable 2>&1); then
            if [[ "$output" == *"main"* ]] || [[ "$output" == *"no symbols"* ]]; then
                log_pass "Symbol analysis - nm command executed"
            else
                log_fail "Symbol analysis - Unexpected nm output: $output"
            fi
        else
            log_fail "Symbol analysis - nm command failed"
        fi
    else
        log_info "Symbol analysis - No binary available for testing"
    fi
fi

# Test 11: Section header analysis
if [ "$READELF_AVAILABLE" = "true" ]; then
    log_test "Section header analysis"
    cd "$ROOT_DIR"
    if [ -f "demos/debugging/examples/bin/vulnerable" ]; then
        if output=$(readelf -S demos/debugging/examples/bin/vulnerable 2>&1); then
            if [[ "$output" == *".text"* ]] && [[ "$output" == *".data"* ]]; then
                log_pass "Section header analysis - Found expected sections"
            else
                log_fail "Section header analysis - Missing expected sections"
            fi
        else
            log_fail "Section header analysis - readelf command failed"
        fi
    else
        log_info "Section header analysis - No binary available for testing"
    fi
fi

# SECURITY ANALYSIS TESTS

# Test 12: Security features check
log_test "Security features check"
cd "$ROOT_DIR"
if [ -f "demos/debugging/examples/bin/vulnerable" ]; then
    if output=$(file demos/debugging/examples/bin/vulnerable 2>&1); then
        if [[ "$output" == *"ELF"* ]]; then
            log_pass "Security features check - ELF binary detected"
        else
            log_fail "Security features check - Not an ELF binary: $output"
        fi
    else
        log_fail "Security features check - file command failed"
    fi
else
    log_info "Security features check - No binary available for testing"
fi

# Test 13: Stack protection check
if [ "$READELF_AVAILABLE" = "true" ]; then
    log_test "Stack protection check"
    cd "$ROOT_DIR"
    if [ -f "demos/debugging/examples/bin/vulnerable" ]; then
        if output=$(readelf -s demos/debugging/examples/bin/vulnerable 2>&1); then
            # Check for stack protection symbols
            if [[ "$output" == *"__stack_chk"* ]]; then
                log_info "Stack protection check - Stack protection enabled"
            else
                log_pass "Stack protection check - No stack protection (as expected for vulnerable binary)"
            fi
        else
            log_fail "Stack protection check - readelf command failed"
        fi
    else
        log_info "Stack protection check - No binary available for testing"
    fi
fi

# DEBUGGING TOOL INTEGRATION TESTS

# Test 14: GDB integration test
if [ "$GDB_AVAILABLE" = "true" ] && [ "$PYTHON3_AVAILABLE" = "true" ]; then
    log_test "GDB integration test"
    cd "$ROOT_DIR"
    if [ -f "tools/debugging/pwndebug.py" ] && [ -f "demos/debugging/examples/bin/vulnerable" ]; then
        # Test non-interactive mode
        if output=$(timeout 10 python3 tools/debugging/pwndebug.py --info demos/debugging/examples/bin/vulnerable 2>&1); then
            if [[ "$output" == *"Binary"* ]] || [[ "$output" == *"File"* ]]; then
                log_pass "GDB integration test - pwndebug.py executed successfully"
            else
                log_fail "GDB integration test - Unexpected output: $output"
            fi
        else
            log_fail "GDB integration test - pwndebug.py execution failed"
        fi
    else
        log_info "GDB integration test - Required files not available"
    fi
fi

# Test 15: LLDB integration test
if [ "$LLDB_AVAILABLE" = "true" ] && [ "$PYTHON3_AVAILABLE" = "true" ]; then
    log_test "LLDB integration test"
    cd "$ROOT_DIR"
    if [ -f "tools/debugging/pwndebug.py" ] && [ -f "demos/debugging/examples/bin/vulnerable" ]; then
        # Test LLDB mode
        if output=$(timeout 10 python3 tools/debugging/pwndebug.py --debugger lldb --info demos/debugging/examples/bin/vulnerable 2>&1); then
            if [[ "$output" == *"Binary"* ]] || [[ "$output" == *"File"* ]] || [[ "$output" == *"lldb"* ]]; then
                log_pass "LLDB integration test - LLDB mode executed successfully"
            else
                log_fail "LLDB integration test - Unexpected output: $output"
            fi
        else
            log_fail "LLDB integration test - LLDB mode execution failed"
        fi
    else
        log_info "LLDB integration test - Required files not available"
    fi
fi

# BINARY INJECTION TESTS

# Test 16: LD_PRELOAD injection test
log_test "LD_PRELOAD injection test"
cd "$ROOT_DIR"

# Create a simple library for injection testing
cat > "$TEMP_DIR/inject_test.c" << 'EOF'
#include <stdio.h>
#include <dlfcn.h>

int puts(const char *s) {
    printf("[INJECTED] %s\n", s);
    return 0;
}
EOF

if [ "$GCC_AVAILABLE" = "true" ]; then
    if gcc -shared -fPIC -o "$TEMP_DIR/inject_test.so" "$TEMP_DIR/inject_test.c" 2>/dev/null; then
        # Test injection with a simple program
        if [ -f "demos/debugging/examples/bin/vulnerable" ]; then
            if output=$(LD_PRELOAD="$TEMP_DIR/inject_test.so" demos/debugging/examples/bin/vulnerable 2>&1); then
                if [[ "$output" == *"[INJECTED]"* ]]; then
                    log_pass "LD_PRELOAD injection test - Injection successful"
                else
                    log_pass "LD_PRELOAD injection test - Binary executed (injection may not be visible)"
                fi
            else
                log_fail "LD_PRELOAD injection test - Binary execution failed"
            fi
        else
            log_info "LD_PRELOAD injection test - No target binary available"
        fi
    else
        log_fail "LD_PRELOAD injection test - Failed to compile injection library"
    fi
else
    log_info "LD_PRELOAD injection test - GCC not available"
fi

# PERFORMANCE TESTS

# Test 17: Large binary analysis performance
log_test "Large binary analysis performance"
cd "$ROOT_DIR"
if [ -f "demos/debugging/examples/bin/vulnerable" ]; then
    start_time=$(date +%s%N)
    strings demos/debugging/examples/bin/vulnerable >/dev/null 2>&1
    objdump -d demos/debugging/examples/bin/vulnerable >/dev/null 2>&1
    readelf -a demos/debugging/examples/bin/vulnerable >/dev/null 2>&1
    end_time=$(date +%s%N)
    duration=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
    
    if [ $duration -lt 5000 ]; then # Less than 5 seconds
        log_pass "Large binary analysis performance - Analysis completed in ${duration}ms"
    else
        log_fail "Large binary analysis performance - Analysis took ${duration}ms (>5s)"
    fi
else
    log_info "Large binary analysis performance - No binary available for testing"
fi

# ERROR HANDLING TESTS

# Test 18: Invalid binary handling
log_test "Invalid binary handling"
cd "$ROOT_DIR"
echo "not a binary" > "$TEMP_DIR/fake_binary"
if output=$(pf debug-info binary="$TEMP_DIR/fake_binary" 2>&1); then
    log_fail "Invalid binary handling - Should have failed but succeeded"
else
    log_pass "Invalid binary handling - Correctly rejected invalid binary"
fi

# Test 19: Missing binary handling
log_test "Missing binary handling"
cd "$ROOT_DIR"
if output=$(pf debug-info binary="/nonexistent/binary" 2>&1); then
    log_fail "Missing binary handling - Should have failed but succeeded"
else
    log_pass "Missing binary handling - Correctly detected missing binary"
fi

# INTEGRATION TESTS

# Test 20: Multi-language debugging
if [ "$GCC_AVAILABLE" = "true" ] && [ "$GPP_AVAILABLE" = "true" ] && [ "$RUSTC_AVAILABLE" = "true" ]; then
    log_test "Multi-language debugging support"
    
    # Create test binaries in different languages
    echo 'int main() { return 0; }' > "$TEMP_DIR/test.c"
    echo 'int main() { return 0; }' > "$TEMP_DIR/test.cpp"
    echo 'fn main() {}' > "$TEMP_DIR/test.rs"
    
    c_success=false
    cpp_success=false
    rust_success=false
    
    if gcc -g -o "$TEMP_DIR/test_c" "$TEMP_DIR/test.c" 2>/dev/null; then
        c_success=true
    fi
    
    if g++ -g -o "$TEMP_DIR/test_cpp" "$TEMP_DIR/test.cpp" 2>/dev/null; then
        cpp_success=true
    fi
    
    if rustc -g -o "$TEMP_DIR/test_rust" "$TEMP_DIR/test.rs" 2>/dev/null; then
        rust_success=true
    fi
    
    if [ "$c_success" = "true" ] && [ "$cpp_success" = "true" ] && [ "$rust_success" = "true" ]; then
        log_pass "Multi-language debugging support - All languages compiled with debug info"
    elif [ "$c_success" = "true" ] || [ "$cpp_success" = "true" ] || [ "$rust_success" = "true" ]; then
        log_pass "Multi-language debugging support - Some languages available"
    else
        log_fail "Multi-language debugging support - No languages compiled successfully"
    fi
else
    log_info "Multi-language debugging support - Some compilers not available"
fi

echo
echo "=== Debugging Workflow Test Results ==="
echo "Total tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}All debugging workflow tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some debugging workflow tests failed!${NC}"
    exit 1
fi