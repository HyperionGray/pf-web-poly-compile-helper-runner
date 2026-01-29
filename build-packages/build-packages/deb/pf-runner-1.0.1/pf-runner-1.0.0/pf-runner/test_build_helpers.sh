#!/bin/bash
# Test script for build helper verbs

set -e

# Determine the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PF_PARSER="${SCRIPT_DIR}/pf_parser.py"

echo "=== Testing Build Helper Verbs ==="
echo

# Create a temporary test directory
TEST_DIR=$(mktemp -d)
echo "Test directory: $TEST_DIR"
cd "$TEST_DIR"

# Test 1: build_detect on empty directory
echo "Test 1: build_detect on empty directory"
cat > test.pf << 'EOF'
task test-detect
  build_detect
end
EOF
python3 "${PF_PARSER}" test.pf test-detect
echo "✓ Test 1 passed"
echo

# Test 2: Makefile detection and build
echo "Test 2: Makefile build"
cat > hello.c << 'EOF'
#include <stdio.h>
int main() { printf("Hello Makefile!\n"); return 0; }
EOF

printf 'all: hello\n\nhello: hello.c\n\tclang -o hello hello.c\n\nclean:\n\trm -f hello\n' > Makefile

cat > test.pf << 'EOF'
task build
  makefile all
end
EOF
python3 "${PF_PARSER}" test.pf build
test -f hello || (echo "✗ Test 2 failed: hello binary not created"; exit 1)
./hello | grep -q "Hello Makefile" || (echo "✗ Test 2 failed: wrong output"; exit 1)
echo "✓ Test 2 passed"
echo

# Test 3: LLVM IR generation
echo "Test 3: LLVM IR generation"
cat > test.pf << 'EOF'
task test-llvm
  shell [lang:c-llvm] int main() { return 0; }
end
EOF
python3 "${PF_PARSER}" test.pf test-llvm | grep -q "ModuleID" || (echo "✗ Test 3 failed: no LLVM IR output"; exit 1)
echo "✓ Test 3 passed"
echo

# Test 4: CMake build
echo "Test 4: CMake build"
rm -rf *
cat > CMakeLists.txt << 'EOF'
cmake_minimum_required(VERSION 3.10)
project(TestCMake)
add_executable(hello_cmake hello.c)
EOF

cat > hello.c << 'EOF'
#include <stdio.h>
int main() { printf("Hello CMake!\n"); return 0; }
EOF

cat > test.pf << 'EOF'
task build
  cmake . build_dir=build
end
EOF
python3 "${PF_PARSER}" test.pf build
test -f build/hello_cmake || (echo "✗ Test 4 failed: cmake binary not created"; exit 1)
./build/hello_cmake | grep -q "Hello CMake" || (echo "✗ Test 4 failed: wrong output"; exit 1)
echo "✓ Test 4 passed"
echo

# Cleanup
cd /
rm -rf "$TEST_DIR"

echo "=== All tests passed! ==="
