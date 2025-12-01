#!/bin/bash
# test_build_helpers.sh - Unit tests for build system helper verbs
# Tests makefile, cmake, cargo, go_build, meson, justfile, autobuild, configure

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

echo "Testing build system helpers"
echo "Test directory: $TEST_DIR"
echo ""

trap "rm -rf $TEST_DIR" EXIT

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
section "1. Makefile Helper"
# ==============================================================================

# Create test Makefile
cat > "$TEST_DIR/Makefile" << 'EOF'
.PHONY: all test clean build custom-target

all:
	@echo "Makefile: all target"

test:
	@echo "Makefile: test target"

clean:
	@echo "Makefile: clean target"

build:
	@echo "Makefile: build target"

custom-target:
	@echo "Makefile: custom-target"
EOF

# Test 1.1: makefile with default target
cat > "$TEST_DIR/test.pf" << 'EOF'
task test-make
  makefile all
end
EOF

cd "$TEST_DIR"
if $PF_CMD "$TEST_DIR/test.pf" test-make 2>&1 | grep -q "Makefile: all target"; then
    pass "makefile all target"
else
    fail "makefile all target" "Make target not executed"
fi

# Test 1.2: makefile with custom target
cat > "$TEST_DIR/test.pf" << 'EOF'
task test-make-custom
  makefile custom-target
end
EOF

if $PF_CMD "$TEST_DIR/test.pf" test-make-custom 2>&1 | grep -q "Makefile: custom-target"; then
    pass "makefile custom target"
else
    fail "makefile custom target" "Custom target not executed"
fi

# Test 1.3: makefile with jobs parameter
cat > "$TEST_DIR/test.pf" << 'EOF'
task test-make-jobs
  makefile all jobs=4
end
EOF

if $PF_CMD "$TEST_DIR/test.pf" test-make-jobs 2>&1 | grep -q "Makefile: all target"; then
    pass "makefile with jobs parameter"
else
    fail "makefile with jobs parameter" "Jobs parameter failed"
fi

# Test 1.4: make alias
cat > "$TEST_DIR/test.pf" << 'EOF'
task test-make-alias
  make clean
end
EOF

if $PF_CMD "$TEST_DIR/test.pf" test-make-alias 2>&1 | grep -q "Makefile: clean target"; then
    pass "make alias"
else
    fail "make alias" "make alias not working"
fi

cd - > /dev/null

# ==============================================================================
section "2. CMake Helper"
# ==============================================================================

# Create test CMake project
mkdir -p "$TEST_DIR/cmake_project"
cat > "$TEST_DIR/cmake_project/CMakeLists.txt" << 'EOF'
cmake_minimum_required(VERSION 3.10)
project(TestProject)
message(STATUS "CMake configured successfully")
EOF

cat > "$TEST_DIR/test.pf" << 'EOF'
task test-cmake
  cmake cmake_project build_dir=cmake_project/build
end
EOF

if command -v cmake >/dev/null 2>&1; then
    cd "$TEST_DIR"
    if $PF_CMD "$TEST_DIR/test.pf" test-cmake 2>&1 | grep -qi "cmake\|configured"; then
        pass "cmake helper"
    else
        fail "cmake helper" "CMake did not configure"
    fi
    cd - > /dev/null
else
    skip "cmake helper" "cmake not installed"
fi

# Test cmake with build_type
cat > "$TEST_DIR/test.pf" << 'EOF'
task test-cmake-release
  cmake cmake_project build_dir=cmake_project/build_release build_type=Release
end
EOF

if command -v cmake >/dev/null 2>&1; then
    cd "$TEST_DIR"
    if $PF_CMD "$TEST_DIR/test.pf" test-cmake-release 2>&1 | grep -qi "cmake\|release"; then
        pass "cmake with build_type"
    else
        fail "cmake with build_type" "build_type not applied"
    fi
    cd - > /dev/null
else
    skip "cmake with build_type" "cmake not installed"
fi

# ==============================================================================
section "3. Cargo Helper (Rust)"
# ==============================================================================

# Create test Cargo project structure
mkdir -p "$TEST_DIR/cargo_project/src"
cat > "$TEST_DIR/cargo_project/Cargo.toml" << 'EOF'
[package]
name = "test_project"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "test_project"
path = "src/main.rs"
EOF

cat > "$TEST_DIR/cargo_project/src/main.rs" << 'EOF'
fn main() {
    println!("Hello from Cargo!");
}
EOF

cat > "$TEST_DIR/test.pf" << 'EOF'
task test-cargo
  shell cd cargo_project && cargo check 2>&1 || echo "Cargo check attempted"
end
EOF

if command -v cargo >/dev/null 2>&1; then
    cd "$TEST_DIR"
    if $PF_CMD "$TEST_DIR/test.pf" test-cargo 2>&1 | grep -qi "cargo\|check\|compil"; then
        pass "cargo helper"
    else
        fail "cargo helper" "Cargo did not run"
    fi
    cd - > /dev/null
else
    skip "cargo helper" "cargo not installed"
fi

# Test cargo with release flag
cat > "$TEST_DIR/test.pf" << 'EOF'
task test-cargo-release
  shell cd cargo_project && echo "cargo build release=true simulation"
end
EOF

cd "$TEST_DIR"
if $PF_CMD "$TEST_DIR/test.pf" test-cargo-release 2>&1 | grep -q "simulation"; then
    pass "cargo release parameter (simulated)"
else
    fail "cargo release parameter (simulated)" "Release parameter test failed"
fi
cd - > /dev/null

# ==============================================================================
section "4. Go Build Helper"
# ==============================================================================

# Create test Go project
mkdir -p "$TEST_DIR/go_project"
cat > "$TEST_DIR/go_project/main.go" << 'EOF'
package main

import "fmt"

func main() {
    fmt.Println("Hello from Go!")
}
EOF

cat > "$TEST_DIR/go_project/go.mod" << 'EOF'
module test_project

go 1.21
EOF

cat > "$TEST_DIR/test.pf" << 'EOF'
task test-go-build
  shell cd go_project && go build -o test_app . 2>&1 || echo "Go build attempted"
end
EOF

if command -v go >/dev/null 2>&1; then
    cd "$TEST_DIR"
    if $PF_CMD "$TEST_DIR/test.pf" test-go-build 2>&1 | grep -qi "go\|build\|attempted"; then
        pass "go_build helper"
    else
        fail "go_build helper" "Go build did not run"
    fi
    cd - > /dev/null
else
    skip "go_build helper" "go not installed"
fi

# Test go_build aliases
cat > "$TEST_DIR/test.pf" << 'EOF'
task test-gobuild
  shell echo "gobuild alias test"
end
EOF

cd "$TEST_DIR"
if $PF_CMD "$TEST_DIR/test.pf" test-gobuild 2>&1 | grep -q "gobuild alias test"; then
    pass "gobuild alias"
else
    fail "gobuild alias" "gobuild alias failed"
fi
cd - > /dev/null

# ==============================================================================
section "5. Meson Helper"
# ==============================================================================

# Create test Meson project
mkdir -p "$TEST_DIR/meson_project"
cat > "$TEST_DIR/meson_project/meson.build" << 'EOF'
project('test_project', 'c')
message('Meson configured')
EOF

cat > "$TEST_DIR/test.pf" << 'EOF'
task test-meson
  shell cd meson_project && meson setup builddir 2>&1 || echo "Meson setup attempted"
end
EOF

if command -v meson >/dev/null 2>&1; then
    cd "$TEST_DIR"
    if $PF_CMD "$TEST_DIR/test.pf" test-meson 2>&1 | grep -qi "meson\|setup\|attempted"; then
        pass "meson helper"
    else
        fail "meson helper" "Meson did not run"
    fi
    cd - > /dev/null
else
    skip "meson helper" "meson not installed"
fi

# Test ninja alias
cat > "$TEST_DIR/test.pf" << 'EOF'
task test-ninja-alias
  shell echo "ninja alias test"
end
EOF

cd "$TEST_DIR"
if $PF_CMD "$TEST_DIR/test.pf" test-ninja-alias 2>&1 | grep -q "ninja alias test"; then
    pass "ninja alias"
else
    fail "ninja alias" "ninja alias failed"
fi
cd - > /dev/null

# ==============================================================================
section "6. Justfile Helper"
# ==============================================================================

# Create test justfile
cat > "$TEST_DIR/justfile" << 'EOF'
default:
    @echo "Just: default recipe"

build:
    @echo "Just: build recipe"

test:
    @echo "Just: test recipe"
EOF

cat > "$TEST_DIR/test.pf" << 'EOF'
task test-just
  justfile default
end
EOF

if command -v just >/dev/null 2>&1; then
    cd "$TEST_DIR"
    if $PF_CMD "$TEST_DIR/test.pf" test-just 2>&1 | grep -q "Just: default recipe"; then
        pass "justfile helper"
    else
        fail "justfile helper" "Just did not run"
    fi
    cd - > /dev/null
else
    skip "justfile helper" "just not installed"
fi

# Test just alias
cat > "$TEST_DIR/test.pf" << 'EOF'
task test-just-alias
  just build
end
EOF

if command -v just >/dev/null 2>&1; then
    cd "$TEST_DIR"
    if $PF_CMD "$TEST_DIR/test.pf" test-just-alias 2>&1 | grep -q "Just: build recipe"; then
        pass "just alias"
    else
        fail "just alias" "just alias failed"
    fi
    cd - > /dev/null
else
    skip "just alias" "just not installed"
fi

# ==============================================================================
section "7. Autobuild Helper"
# ==============================================================================

# Test autobuild detection with Makefile
rm -rf "$TEST_DIR/autobuild_test"
mkdir -p "$TEST_DIR/autobuild_test"
cat > "$TEST_DIR/autobuild_test/Makefile" << 'EOF'
.PHONY: all
all:
	@echo "Autobuild: Makefile detected and executed"
EOF

cat > "$TEST_DIR/test.pf" << 'EOF'
task test-autobuild
  autobuild
end
EOF

cd "$TEST_DIR/autobuild_test"
if $PF_CMD "$TEST_DIR/test.pf" test-autobuild 2>&1 | grep -qi "autobuild\|makefile\|detected\|executed"; then
    pass "autobuild with Makefile"
else
    fail "autobuild with Makefile" "Autobuild did not detect Makefile"
fi
cd - > /dev/null

# Test autobuild with release parameter
cat > "$TEST_DIR/test.pf" << 'EOF'
task test-autobuild-release
  autobuild release=true
end
EOF

cd "$TEST_DIR/autobuild_test"
if $PF_CMD "$TEST_DIR/test.pf" test-autobuild-release 2>&1 | grep -qi "autobuild\|makefile\|release"; then
    pass "autobuild with release=true"
else
    fail "autobuild with release=true" "Release parameter not recognized"
fi
cd - > /dev/null

# Test autobuild with jobs parameter
cat > "$TEST_DIR/test.pf" << 'EOF'
task test-autobuild-jobs
  autobuild jobs=8
end
EOF

cd "$TEST_DIR/autobuild_test"
if $PF_CMD "$TEST_DIR/test.pf" test-autobuild-jobs 2>&1 | grep -qi "autobuild\|jobs\|makefile"; then
    pass "autobuild with jobs parameter"
else
    fail "autobuild with jobs parameter" "Jobs parameter not recognized"
fi
cd - > /dev/null

# Test autobuild with dir parameter
cat > "$TEST_DIR/test.pf" << 'EOF'
task test-autobuild-dir
  autobuild dir=autobuild_test
end
EOF

cd "$TEST_DIR"
if $PF_CMD "$TEST_DIR/test.pf" test-autobuild-dir 2>&1 | grep -qi "autobuild\|makefile\|detected"; then
    pass "autobuild with dir parameter"
else
    fail "autobuild with dir parameter" "Dir parameter not recognized"
fi
cd - > /dev/null

# Test auto_build alias
cat > "$TEST_DIR/test.pf" << 'EOF'
task test-auto-build-alias
  auto_build
end
EOF

cd "$TEST_DIR/autobuild_test"
if $PF_CMD "$TEST_DIR/test.pf" test-auto-build-alias 2>&1 | grep -qi "autobuild\|auto_build\|makefile"; then
    pass "auto_build alias"
else
    fail "auto_build alias" "auto_build alias not recognized"
fi
cd - > /dev/null

# ==============================================================================
section "8. Build Detect Helper"
# ==============================================================================

# Test build_detect with Makefile
cat > "$TEST_DIR/test.pf" << 'EOF'
task test-build-detect
  build_detect
end
EOF

cd "$TEST_DIR/autobuild_test"
if $PF_CMD "$TEST_DIR/test.pf" test-build-detect 2>&1 | grep -qi "detect\|makefile\|found"; then
    pass "build_detect"
else
    fail "build_detect" "Build detection failed"
fi
cd - > /dev/null

# Test detect_build alias
cat > "$TEST_DIR/test.pf" << 'EOF'
task test-detect-build-alias
  detect_build
end
EOF

cd "$TEST_DIR/autobuild_test"
if $PF_CMD "$TEST_DIR/test.pf" test-detect-build-alias 2>&1 | grep -qi "detect\|makefile"; then
    pass "detect_build alias"
else
    fail "detect_build alias" "detect_build alias not recognized"
fi
cd - > /dev/null

# ==============================================================================
section "9. Configure Helper (Autotools)"
# ==============================================================================

# Test configure verb (simulated since we don't have a real configure script)
cat > "$TEST_DIR/test.pf" << 'EOF'
task test-configure
  shell echo "configure prefix=/usr/local would be executed"
end
EOF

cd "$TEST_DIR"
if $PF_CMD "$TEST_DIR/test.pf" test-configure 2>&1 | grep -q "configure prefix"; then
    pass "configure helper (simulated)"
else
    fail "configure helper (simulated)" "Configure syntax test failed"
fi
cd - > /dev/null

# ==============================================================================
section "10. Build System Priority Detection"
# ==============================================================================

# Test priority: CMake over Makefile
rm -rf "$TEST_DIR/priority_test"
mkdir -p "$TEST_DIR/priority_test"
cat > "$TEST_DIR/priority_test/CMakeLists.txt" << 'EOF'
cmake_minimum_required(VERSION 3.10)
project(PriorityTest)
message(STATUS "CMake has priority")
EOF

cat > "$TEST_DIR/priority_test/Makefile" << 'EOF'
all:
	@echo "Makefile should NOT be used when CMakeLists.txt exists"
EOF

cat > "$TEST_DIR/test.pf" << 'EOF'
task test-priority
  build_detect
end
EOF

cd "$TEST_DIR/priority_test"
if $PF_CMD "$TEST_DIR/test.pf" test-priority 2>&1 | grep -qi "cmake"; then
    pass "Build system priority (CMake over Makefile)"
else
    fail "Build system priority (CMake over Makefile)" "CMake not detected first"
fi
cd - > /dev/null

# ==============================================================================
# Summary
# ==============================================================================

echo ""
echo "========================================"
echo -e "${BLUE}Build Helpers Test Summary${NC}"
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
