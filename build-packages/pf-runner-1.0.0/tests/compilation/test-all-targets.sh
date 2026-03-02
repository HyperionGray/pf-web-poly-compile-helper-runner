#!/bin/bash
# Comprehensive Compilation Testing for pf
# Tests ALL compilation targets: WASM, LLVM IR, asm.js for all supported languages

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_DIR="$SCRIPT_DIR"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PF_RUNNER_DIR="$ROOT_DIR/pf-runner"
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

# Check if a tool is available
check_tool_available() {
    local tool="$1"
    case "$tool" in
        "rust")
            command -v rustc >/dev/null 2>&1 && command -v wasm-pack >/dev/null 2>&1
            ;;
        "emscripten")
            command -v emcc >/dev/null 2>&1
            ;;
        "fortran")
            command -v lfortran >/dev/null 2>&1
            ;;
        "wabt")
            command -v wat2wasm >/dev/null 2>&1
            ;;
        "llvm")
            command -v clang >/dev/null 2>&1 && command -v opt >/dev/null 2>&1
            ;;
        "node")
            command -v node >/dev/null 2>&1
            ;;
        *)
            return 1
            ;;
    esac
}

# Test compilation task
test_compilation() {
    local test_name="$1"
    local task_name="$2"
    local expected_output_file="$3"
    local params="$4"
    
    log_test "$test_name"
    
    cd "$ROOT_DIR"
    
    if output=$(pf "$task_name" $params 2>&1); then
        if [ -n "$expected_output_file" ] && [ -f "$expected_output_file" ]; then
            log_pass "$test_name - Output file created: $expected_output_file"
        elif [ -z "$expected_output_file" ]; then
            log_pass "$test_name - Task executed successfully"
        else
            log_fail "$test_name - Expected output file not found: $expected_output_file"
        fi
    else
        log_fail "$test_name - Compilation failed: $output"
    fi
}

echo "=== pf Compilation Testing ==="
echo "Testing all compilation targets for all supported languages"
echo

# Check available tools
log_info "Checking available compilation tools..."
RUST_AVAILABLE=$(check_tool_available "rust" && echo "true" || echo "false")
EMSCRIPTEN_AVAILABLE=$(check_tool_available "emscripten" && echo "true" || echo "false")
FORTRAN_AVAILABLE=$(check_tool_available "fortran" && echo "true" || echo "false")
WABT_AVAILABLE=$(check_tool_available "wabt" && echo "true" || echo "false")
LLVM_AVAILABLE=$(check_tool_available "llvm" && echo "true" || echo "false")
NODE_AVAILABLE=$(check_tool_available "node" && echo "true" || echo "false")

echo "Tool availability:"
echo "  Rust/wasm-pack: $RUST_AVAILABLE"
echo "  Emscripten: $EMSCRIPTEN_AVAILABLE"
echo "  LFortran: $FORTRAN_AVAILABLE"
echo "  WABT: $WABT_AVAILABLE"
echo "  LLVM: $LLVM_AVAILABLE"
echo "  Node.js: $NODE_AVAILABLE"
echo

# RUST COMPILATION TESTS

if [ "$RUST_AVAILABLE" = "true" ]; then
    # Test 1: Rust to WASM
    test_compilation "Rust to WASM" "web-build-rust-wasm" \
        "demos/pf-web-polyglot-demo-plus-c/web/wasm/rust/pkg/rust_demo.wasm" ""
    
    # Test 2: Rust to LLVM IR
    if [ "$LLVM_AVAILABLE" = "true" ]; then
        test_compilation "Rust to LLVM IR" "web-build-rust-llvm" \
            "demos/pf-web-polyglot-demo-plus-c/web/llvm/rust/lib.ll" ""
        
        # Test 3: Rust to LLVM IR with optimization
        test_compilation "Rust to LLVM IR O2" "web-build-rust-llvm" \
            "demos/pf-web-polyglot-demo-plus-c/web/llvm/rust/lib.ll" "opt_level=2"
    else
        log_info "Skipping Rust LLVM tests - LLVM not available"
    fi
else
    log_info "Skipping Rust tests - Rust/wasm-pack not available"
fi

# C COMPILATION TESTS

if [ "$EMSCRIPTEN_AVAILABLE" = "true" ]; then
    # Test 4: C to WASM
    test_compilation "C to WASM" "web-build-c-wasm" \
        "demos/pf-web-polyglot-demo-plus-c/web/wasm/c/c_trap.js" ""
    
    # Test 5: C to asm.js
    test_compilation "C to asm.js" "web-build-c-asm" \
        "demos/pf-web-polyglot-demo-plus-c/web/asm/c/c_trap_asm.js" ""
    
    # Test 6: C to LLVM IR
    if [ "$LLVM_AVAILABLE" = "true" ]; then
        test_compilation "C to LLVM IR" "web-build-c-llvm" \
            "demos/pf-web-polyglot-demo-plus-c/web/llvm/c/c_trap.ll" ""
        
        # Test 7: C to LLVM IR with optimization
        test_compilation "C to LLVM IR O3" "web-build-c-llvm" \
            "demos/pf-web-polyglot-demo-plus-c/web/llvm/c/c_trap.ll" "opt_level=3"
        
        # Test 8: C to LLVM IR with OpenMP
        test_compilation "C to LLVM IR OpenMP" "web-build-c-llvm" \
            "demos/pf-web-polyglot-demo-plus-c/web/llvm/c/c_trap.ll" "parallel=true"
        
        # Test 9: C to LLVM IR with custom optimization passes
        test_compilation "C to LLVM IR custom passes" "web-build-c-llvm-opt" \
            "demos/pf-web-polyglot-demo-plus-c/web/llvm/c/c_trap.ll" "passes=mem2reg,instcombine"
    else
        log_info "Skipping C LLVM tests - LLVM not available"
    fi
else
    log_info "Skipping C tests - Emscripten not available"
fi

# FORTRAN COMPILATION TESTS

if [ "$FORTRAN_AVAILABLE" = "true" ]; then
    # Test 10: Fortran to WASM
    test_compilation "Fortran to WASM" "web-build-fortran-wasm" \
        "demos/pf-web-polyglot-demo-plus-c/web/wasm/fortran/fortran.wasm" ""
    
    # Test 11: Fortran to LLVM IR
    if [ "$LLVM_AVAILABLE" = "true" ]; then
        test_compilation "Fortran to LLVM IR" "web-build-fortran-llvm" \
            "demos/pf-web-polyglot-demo-plus-c/web/llvm/fortran/hello.ll" ""
        
        # Test 12: Fortran to LLVM IR with optimization
        test_compilation "Fortran to LLVM IR O2" "web-build-fortran-llvm" \
            "demos/pf-web-polyglot-demo-plus-c/web/llvm/fortran/hello.ll" "opt_level=2"
    else
        log_info "Skipping Fortran LLVM tests - LLVM not available"
    fi
else
    log_info "Skipping Fortran tests - LFortran not available"
fi

# WAT (WebAssembly Text) COMPILATION TESTS

if [ "$WABT_AVAILABLE" = "true" ]; then
    # Test 13: WAT to WASM
    test_compilation "WAT to WASM" "web-build-wat-wasm" \
        "demos/pf-web-polyglot-demo-plus-c/web/wasm/asm/mini.wasm" ""
else
    log_info "Skipping WAT tests - WABT not available"
fi

# BATCH COMPILATION TESTS

# Test 14: Build all WASM targets
if [ "$RUST_AVAILABLE" = "true" ] && [ "$EMSCRIPTEN_AVAILABLE" = "true" ] && [ "$FORTRAN_AVAILABLE" = "true" ] && [ "$WABT_AVAILABLE" = "true" ]; then
    test_compilation "Build all WASM" "web-build-all-wasm" "" ""
else
    log_info "Skipping build all WASM - some tools not available"
fi

# Test 15: Build all asm.js targets
if [ "$EMSCRIPTEN_AVAILABLE" = "true" ]; then
    test_compilation "Build all asm.js" "web-build-all-asm" "" ""
else
    log_info "Skipping build all asm.js - Emscripten not available"
fi

# Test 16: Build all LLVM targets
if [ "$RUST_AVAILABLE" = "true" ] && [ "$EMSCRIPTEN_AVAILABLE" = "true" ] && [ "$FORTRAN_AVAILABLE" = "true" ] && [ "$LLVM_AVAILABLE" = "true" ]; then
    test_compilation "Build all LLVM" "web-build-all-llvm" "" ""
    
    # Test 17: Build all LLVM with custom optimization
    test_compilation "Build all LLVM O2" "web-build-all-llvm" "" "opt_level=2"
    
    # Test 18: Build all LLVM with parallel
    test_compilation "Build all LLVM parallel" "web-build-all-llvm" "" "parallel=true"
else
    log_info "Skipping build all LLVM - some tools not available"
fi

# COMPILATION VERIFICATION TESTS

# Test 19: Verify WASM file validity
if [ "$WABT_AVAILABLE" = "true" ] && [ -f "demos/pf-web-polyglot-demo-plus-c/web/wasm/rust/pkg/rust_demo.wasm" ]; then
    log_test "WASM file validation"
    if wasm-validate "demos/pf-web-polyglot-demo-plus-c/web/wasm/rust/pkg/rust_demo.wasm" 2>/dev/null; then
        log_pass "WASM file validation - Rust WASM is valid"
    else
        log_fail "WASM file validation - Rust WASM is invalid"
    fi
fi

# Test 20: Verify LLVM IR syntax
if [ "$LLVM_AVAILABLE" = "true" ] && [ -f "demos/pf-web-polyglot-demo-plus-c/web/llvm/c/c_trap.ll" ]; then
    log_test "LLVM IR validation"
    if llvm-as "demos/pf-web-polyglot-demo-plus-c/web/llvm/c/c_trap.ll" -o /dev/null 2>/dev/null; then
        log_pass "LLVM IR validation - C LLVM IR is valid"
    else
        log_fail "LLVM IR validation - C LLVM IR is invalid"
    fi
fi

# Test 21: Verify JavaScript syntax for asm.js
if [ "$NODE_AVAILABLE" = "true" ] && [ -f "demos/pf-web-polyglot-demo-plus-c/web/asm/c/c_trap_asm.js" ]; then
    log_test "asm.js validation"
    if node -c "demos/pf-web-polyglot-demo-plus-c/web/asm/c/c_trap_asm.js" 2>/dev/null; then
        log_pass "asm.js validation - C asm.js is valid JavaScript"
    else
        log_fail "asm.js validation - C asm.js has syntax errors"
    fi
fi

# PERFORMANCE TESTS

# Test 22: Compilation time measurement
if [ "$EMSCRIPTEN_AVAILABLE" = "true" ]; then
    log_test "Compilation performance"
    start_time=$(date +%s%N)
    pf web-build-c-wasm >/dev/null 2>&1
    end_time=$(date +%s%N)
    duration=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
    
    if [ $duration -lt 30000 ]; then # Less than 30 seconds
        log_pass "Compilation performance - C to WASM in ${duration}ms"
    else
        log_fail "Compilation performance - C to WASM took ${duration}ms (>30s)"
    fi
fi

# ERROR HANDLING TESTS

# Test 23: Invalid optimization level
log_test "Invalid optimization level handling"
cd "$ROOT_DIR"
if output=$(pf web-build-c-llvm opt_level=invalid 2>&1); then
    log_fail "Invalid optimization level - Should have failed but succeeded"
else
    log_pass "Invalid optimization level - Correctly rejected"
fi

# Test 24: Missing source files
log_test "Missing source files handling"
# Temporarily rename source file
if [ -f "demos/pf-web-polyglot-demo-plus-c/c/c_trap.c" ]; then
    # Define cleanup function to restore the file
    cleanup_restore_c_trap() {
        if [ -f "demos/pf-web-polyglot-demo-plus-c/c/c_trap.c.bak" ]; then
            mv "demos/pf-web-polyglot-demo-plus-c/c/c_trap.c.bak" "demos/pf-web-polyglot-demo-plus-c/c/c_trap.c"
        fi
    }
    
    # Set trap to ensure file is restored even on failure
    trap cleanup_restore_c_trap EXIT
    
    mv "demos/pf-web-polyglot-demo-plus-c/c/c_trap.c" "demos/pf-web-polyglot-demo-plus-c/c/c_trap.c.bak"
    
    if output=$(pf web-build-c-wasm 2>&1); then
        log_fail "Missing source files - Should have failed but succeeded"
    else
        log_pass "Missing source files - Correctly detected missing file"
    fi
    
    # Restore source file and remove trap
    cleanup_restore_c_trap
    trap - EXIT
fi

# CROSS-COMPILATION TESTS

# Test 25: Multiple target compilation
if [ "$EMSCRIPTEN_AVAILABLE" = "true" ] && [ "$LLVM_AVAILABLE" = "true" ]; then
    log_test "Multiple target compilation"
    
    # Clean previous outputs
    rm -f demos/pf-web-polyglot-demo-plus-c/web/wasm/c/c_trap.js
    rm -f demos/pf-web-polyglot-demo-plus-c/web/llvm/c/c_trap.ll
    
    # Build both targets
    pf web-build-c-wasm >/dev/null 2>&1
    pf web-build-c-llvm >/dev/null 2>&1
    
    if [ -f "demos/pf-web-polyglot-demo-plus-c/web/wasm/c/c_trap.js" ] && [ -f "demos/pf-web-polyglot-demo-plus-c/web/llvm/c/c_trap.ll" ]; then
        log_pass "Multiple target compilation - Both WASM and LLVM outputs created"
    else
        log_fail "Multiple target compilation - Missing output files"
    fi
fi

echo
echo "=== Compilation Test Results ==="
echo "Total tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}All compilation tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some compilation tests failed!${NC}"
    exit 1
fi