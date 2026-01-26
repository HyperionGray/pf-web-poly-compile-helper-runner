#!/usr/bin/env bash
# Test script to validate all .pf files involved in installation
# This script systematically tests each .pf file that contains install tasks

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Test result tracking
test_passed() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    PASSED_TESTS=$((PASSED_TESTS + 1))
    log_success "$1"
}

test_failed() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    FAILED_TESTS=$((FAILED_TESTS + 1))
    log_error "$1"
}

test_skipped() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
    log_warning "$1"
}

# Test if a .pf file is parseable
test_pf_syntax() {
    local pf_file="$1"
    log_info "Testing syntax: $pf_file"
    
    if [[ ! -f "$pf_file" ]]; then
        test_failed "$pf_file: File not found"
        return 1
    fi
    
    # Try basic syntax checks using grep patterns
    # Check for matching task/end pairs
    local task_count=$(grep -c "^task " "$pf_file" || echo "0")
    local end_count=$(grep -c "^end" "$pf_file" || echo "0")
    
    if [[ $task_count -ne $end_count ]]; then
        test_failed "$pf_file: Mismatched task/end pairs (tasks: $task_count, ends: $end_count)"
        return 1
    fi
    
    # Check for basic syntax issues
    if grep -q "^task.*\$" "$pf_file" && ! grep -q "describe\|shell\|env" "$pf_file"; then
        test_failed "$pf_file: Empty tasks detected"
        return 1
    fi
    
    test_passed "$pf_file: Basic syntax valid (tasks: $task_count, ends: $end_count)"
    return 0
}

# Test if install tasks are present and listed
test_install_tasks_present() {
    local pf_file="$1"
    log_info "Testing install tasks: $pf_file"
    
    if [[ ! -f "$pf_file" ]]; then
        test_skipped "$pf_file: File not found"
        return 1
    fi
    
    # Check if file has install tasks
    if grep -q "^task.*install" "$pf_file"; then
        local task_count=$(grep -c "^task.*install" "$pf_file" || echo "0")
        test_passed "$pf_file: Found $task_count install task(s)"
        return 0
    else
        test_skipped "$pf_file: No install tasks found"
        return 1
    fi
}

# Test if a specific task can be listed
test_task_exists() {
    local pf_file="$1"
    local task_name="$2"
    log_info "Testing task exists: $task_name in $pf_file"
    
    if grep -q "^task $task_name" "$pf_file"; then
        test_passed "$task_name: Task definition found"
        return 0
    else
        test_failed "$task_name: Task not found in file"
        return 1
    fi
}

# Test if a task has proper description
test_task_description() {
    local pf_file="$1"
    local task_name="$2"
    log_info "Testing task description: $task_name"
    
    if grep -A 1 "^task $task_name" "$pf_file" | grep -q "describe"; then
        test_passed "$task_name: Has description"
        return 0
    else
        test_warning "$task_name: Missing description"
        return 1
    fi
}

# Main test suite
main() {
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║     Testing .pf Files Involved in Installation            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Get repository root
    REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$REPO_ROOT"
    
    log_info "Repository root: $REPO_ROOT"
    echo ""
    
    # Test Group 1: Core Installation Files
    echo "═══════════════════════════════════════════════════════════"
    echo "TEST GROUP 1: Core Installation Files"
    echo "═══════════════════════════════════════════════════════════"
    test_pf_syntax "Pfyfile.always-available.pf"
    test_install_tasks_present "Pfyfile.always-available.pf"
    test_pf_syntax "Pfyfile.pf"
    test_install_tasks_present "Pfyfile.pf"
    echo ""
    
    # Test Group 2: Always-On Installation Files
    echo "═══════════════════════════════════════════════════════════"
    echo "TEST GROUP 2: Always-On Installation Files"
    echo "═══════════════════════════════════════════════════════════"
    test_pf_syntax "pf-runner/Pfyfile.always-on-packages.pf"
    test_install_tasks_present "pf-runner/Pfyfile.always-on-packages.pf"
    test_pf_syntax "pf-runner/Pfyfile.always-on-debug.pf"
    test_install_tasks_present "pf-runner/Pfyfile.always-on-debug.pf"
    test_pf_syntax "pf-runner/Pfyfile.always-on-exploit.pf"
    test_install_tasks_present "pf-runner/Pfyfile.always-on-exploit.pf"
    test_pf_syntax "pf-runner/Pfyfile.always-on-tui.pf"
    test_install_tasks_present "pf-runner/Pfyfile.always-on-tui.pf"
    echo ""
    
    # Test Group 3: Tool Installation Files
    echo "═══════════════════════════════════════════════════════════"
    echo "TEST GROUP 3: Tool Installation Files"
    echo "═══════════════════════════════════════════════════════════"
    test_pf_syntax "Pfyfile.debug-tools.pf"
    test_install_tasks_present "Pfyfile.debug-tools.pf"
    test_pf_syntax "Pfyfile.exploit.pf"
    test_install_tasks_present "Pfyfile.exploit.pf"
    test_pf_syntax "Pfyfile.fuzzing.pf"
    test_install_tasks_present "Pfyfile.fuzzing.pf"
    test_pf_syntax "Pfyfile.debugging.pf"
    test_install_tasks_present "Pfyfile.debugging.pf"
    echo ""
    
    # Test Group 4: Package Manager and Container Files
    echo "═══════════════════════════════════════════════════════════"
    echo "TEST GROUP 4: Package Manager and Container Files"
    echo "═══════════════════════════════════════════════════════════"
    test_pf_syntax "Pfyfile.package-manager.pf"
    test_install_tasks_present "Pfyfile.package-manager.pf"
    test_pf_syntax "Pfyfile.containers.pf"
    test_install_tasks_present "Pfyfile.containers.pf"
    test_pf_syntax "Pfyfile.distro-switch.pf"
    test_install_tasks_present "Pfyfile.distro-switch.pf"
    echo ""
    
    # Test Group 5: Security and Additional Tool Files
    echo "═══════════════════════════════════════════════════════════"
    echo "TEST GROUP 5: Security and Additional Tool Files"
    echo "═══════════════════════════════════════════════════════════"
    test_pf_syntax "Pfyfile.security.pf"
    test_install_tasks_present "Pfyfile.security.pf"
    test_pf_syntax "Pfyfile.tui.pf"
    test_install_tasks_present "Pfyfile.tui.pf"
    test_pf_syntax "Pfyfile.git-cleanup.pf"
    test_install_tasks_present "Pfyfile.git-cleanup.pf"
    test_pf_syntax "Pfyfile.lifting.pf"
    test_install_tasks_present "Pfyfile.lifting.pf"
    test_pf_syntax "Pfyfile.injection.pf"
    test_install_tasks_present "Pfyfile.injection.pf"
    echo ""
    
    # Print summary
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                    TEST SUMMARY                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Total Tests:   $TOTAL_TESTS"
    echo -e "Passed:        ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed:        ${RED}$FAILED_TESTS${NC}"
    echo -e "Skipped:       ${YELLOW}$SKIPPED_TESTS${NC}"
    echo ""
    
    if [[ $FAILED_TESTS -eq 0 ]]; then
        log_success "All tests passed! ✓"
        exit 0
    else
        log_error "$FAILED_TESTS test(s) failed"
        exit 1
    fi
}

# Run main test suite
main "$@"
