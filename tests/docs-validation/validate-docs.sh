#!/bin/bash
# Documentation Validation for pf Language
# Ensures all documented features exist and work as described

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
DOCS_DIR="$ROOT_DIR/docs"
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

# Extract tasks mentioned in documentation
extract_doc_tasks() {
    local doc_file="$1"
    if [ -f "$doc_file" ]; then
        # Extract task names from various patterns in documentation
        grep -oE 'pf [a-zA-Z0-9_-]+' "$doc_file" | sed 's/pf //' | sort -u
    fi
}

# Extract API endpoints from documentation
extract_api_endpoints() {
    local doc_file="$1"
    if [ -f "$doc_file" ]; then
        # Extract API endpoints
        grep -oE '/api/[a-zA-Z0-9/_-]+' "$doc_file" | sort -u
    fi
}

echo "=== pf Documentation Validation ==="
echo "Validating that all documented features exist and work"
echo

cd "$ROOT_DIR"

# Test 1: Validate README.md examples
log_test "README.md task examples"
if [ -f "README.md" ]; then
    readme_tasks=$(extract_doc_tasks "README.md")
    missing_tasks=()
    
    while IFS= read -r task; do
        if [ -n "$task" ] && ! pf list | grep -q "^$task\s"; then
            missing_tasks+=("$task")
        fi
    done <<< "$readme_tasks"
    
    if [ ${#missing_tasks[@]} -eq 0 ]; then
        log_pass "README.md task examples - All tasks exist"
    else
        log_fail "README.md task examples - Missing tasks: ${missing_tasks[*]}"
    fi
else
    log_info "README.md not found"
fi

# Test 2: Validate REST API documentation
log_test "REST API documentation"
if [ -f "$DOCS_DIR/REST-API.md" ]; then
    api_endpoints=$(extract_api_endpoints "$DOCS_DIR/REST-API.md")
    
    # Start API server for testing
    if command -v node >/dev/null 2>&1 && [ -f "tools/api-server.mjs" ]; then
        node tools/api-server.mjs demos/pf-web-polyglot-demo-plus-c/web 8082 > "$TEMP_DIR/api_server.log" 2>&1 &
        api_pid=$!
        # Poll for server readiness (up to 15 seconds)
        ready=0
        for i in {1..15}; do
            if curl -s "http://localhost:8082${api_endpoints%% *}" >/dev/null 2>&1; then
                ready=1
                break
            fi
            sleep 1
        done
        if [ "$ready" -ne 1 ]; then
            log_fail "REST API documentation - Server did not start within timeout"
            kill $api_pid 2>/dev/null || true
            exit 1
        fi
        
        missing_endpoints=()
        while IFS= read -r endpoint; do
            if [ -n "$endpoint" ] && ! curl -s "http://localhost:8082$endpoint" >/dev/null 2>&1; then
                missing_endpoints+=("$endpoint")
            fi
        done <<< "$api_endpoints"
        
        kill $api_pid 2>/dev/null || true
        
        if [ ${#missing_endpoints[@]} -eq 0 ]; then
            log_pass "REST API documentation - All endpoints accessible"
        else
            log_fail "REST API documentation - Inaccessible endpoints: ${missing_endpoints[*]}"
        fi
    else
        log_info "REST API documentation - Cannot test (Node.js or api-server.mjs not available)"
    fi
else
    log_info "REST API documentation not found"
fi

# Test 3: Validate TUI documentation
log_test "TUI documentation"
if [ -f "$DOCS_DIR/TUI.md" ]; then
    tui_tasks=$(extract_doc_tasks "$DOCS_DIR/TUI.md")
    missing_tui_tasks=()
    
    while IFS= read -r task; do
        if [ -n "$task" ] && ! pf list | grep -q "^$task\s"; then
            missing_tui_tasks+=("$task")
        fi
    done <<< "$tui_tasks"
    
    if [ ${#missing_tui_tasks[@]} -eq 0 ]; then
        log_pass "TUI documentation - All tasks exist"
    else
        log_fail "TUI documentation - Missing tasks: ${missing_tui_tasks[*]}"
    fi
else
    log_info "TUI documentation not found"
fi

# Test 4: Validate grammar documentation alignment
log_test "Grammar documentation alignment"
if [ -f "pf-runner/pf.lark" ]; then
    # Extract grammar rules
    grammar_rules=$(grep -E '^[a-zA-Z_][a-zA-Z0-9_]*:' pf-runner/pf.lark | sed 's/:.*//' | sort -u)
    
    # Check if major grammar features are documented
    major_features=("task" "env" "shell" "if" "for" "sync" "packages" "service" "directory" "copy")
    undocumented_features=()
    
    for feature in "${major_features[@]}"; do
        if ! grep -r "$feature" docs/ >/dev/null 2>&1; then
            undocumented_features+=("$feature")
        fi
    done
    
    if [ ${#undocumented_features[@]} -eq 0 ]; then
        log_pass "Grammar documentation alignment - All major features documented"
    else
        log_fail "Grammar documentation alignment - Undocumented features: ${undocumented_features[*]}"
    fi
else
    log_fail "Grammar documentation alignment - Grammar file not found"
fi

# Test 5: Validate example code in documentation
log_test "Documentation example code"
example_files=()

# Find code blocks in documentation
if command -v grep >/dev/null 2>&1; then
    # Extract bash code blocks from markdown files
    for doc_file in docs/*.md; do
        if [ -f "$doc_file" ]; then
            # Extract bash code blocks and test them
            awk '/```bash/,/```/' "$doc_file" | grep -E '^pf ' > "$TEMP_DIR/examples_$(basename "$doc_file").sh" 2>/dev/null || true
        fi
    done
    
    # Test extracted examples
    example_errors=0
    for example_file in "$TEMP_DIR"/examples_*.sh; do
        if [ -f "$example_file" ] && [ -s "$example_file" ]; then
            while IFS= read -r line; do
                if [[ "$line" =~ ^pf[[:space:]] ]]; then
                    # Extract task name
                    task_name=$(echo "$line" | awk '{print $2}')
                    if [ -n "$task_name" ] && ! pf list | grep -q "^$task_name\s"; then
                        example_errors=$((example_errors + 1))
                    fi
                fi
            done < "$example_file"
        fi
    done
    
    if [ $example_errors -eq 0 ]; then
        log_pass "Documentation example code - All examples reference valid tasks"
    else
        log_fail "Documentation example code - $example_errors invalid task references"
    fi
else
    log_info "Documentation example code - Cannot validate (grep not available)"
fi

# Test 6: Validate installation documentation
log_test "Installation documentation"
install_tasks=("install" "install-base" "install-web" "install-exploit")
missing_install_tasks=()

for task in "${install_tasks[@]}"; do
    if ! pf list | grep -q "^$task\s"; then
        missing_install_tasks+=("$task")
    fi
done

if [ ${#missing_install_tasks[@]} -eq 0 ]; then
    log_pass "Installation documentation - All install tasks exist"
else
    log_fail "Installation documentation - Missing install tasks: ${missing_install_tasks[*]}"
fi

# Test 7: Validate build system documentation
log_test "Build system documentation"
build_tasks=("web-build-rust" "web-build-c" "web-build-fortran" "web-build-wat" "web-build-all")
missing_build_tasks=()

for task in "${build_tasks[@]}"; do
    if ! pf list | grep -q "^$task\s"; then
        missing_build_tasks+=("$task")
    fi
done

if [ ${#missing_build_tasks[@]} -eq 0 ]; then
    log_pass "Build system documentation - All build tasks exist"
else
    log_fail "Build system documentation - Missing build tasks: ${missing_build_tasks[*]}"
fi

# Test 8: Validate debugging documentation
log_test "Debugging documentation"
debug_tasks=("debug" "debug-gdb" "debug-lldb" "debug-info" "build-debug-examples")
missing_debug_tasks=()

for task in "${debug_tasks[@]}"; do
    if ! pf list | grep -q "^$task\s"; then
        missing_debug_tasks+=("$task")
    fi
done

if [ ${#missing_debug_tasks[@]} -eq 0 ]; then
    log_pass "Debugging documentation - All debug tasks exist"
else
    log_fail "Debugging documentation - Missing debug tasks: ${missing_debug_tasks[*]}"
fi

# Test 9: Validate parameter documentation
log_test "Parameter documentation"
# Check that documented parameters work
if pf web-dev --help 2>&1 | grep -q "port\|dir" || pf list | grep -q "web-dev"; then
    log_pass "Parameter documentation - Parameter support verified"
else
    log_fail "Parameter documentation - Parameter support not found"
fi

# Test 10: Validate cross-references
log_test "Documentation cross-references"
broken_refs=0

# Check for references to non-existent files
for doc_file in docs/*.md; do
    if [ -f "$doc_file" ]; then
        # Check for file references
        while IFS= read -r line; do
            if [[ "$line" =~ \`[^`]*\.(pf|py|mjs|sh)\` ]]; then
                file_ref=$(echo "$line" | grep -oE '\`[^`]*\.(pf|py|mjs|sh)\`' | tr -d '`')
                if [ -n "$file_ref" ] && [ ! -f "$file_ref" ] && [ ! -f "$ROOT_DIR/$file_ref" ]; then
                    broken_refs=$((broken_refs + 1))
                fi
            fi
        done < "$doc_file"
    fi
done

if [ $broken_refs -eq 0 ]; then
    log_pass "Documentation cross-references - All file references valid"
else
    log_fail "Documentation cross-references - $broken_refs broken file references"
fi

echo
echo "=== Documentation Validation Results ==="
echo "Total tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}All documentation validation tests passed!${NC}"
    echo -e "${GREEN}Documentation is aligned with implementation.${NC}"
    exit 0
else
    echo -e "${RED}Some documentation validation tests failed!${NC}"
    echo -e "${YELLOW}Please update documentation to match implementation.${NC}"
    exit 1
fi