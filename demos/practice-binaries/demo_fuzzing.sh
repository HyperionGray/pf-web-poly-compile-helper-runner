#!/bin/bash
# Demo: Fuzzing Practice Binaries
# This script demonstrates fuzzing techniques

DEMO_NAME="Fuzzing Practice Binaries"

echo "========================================"
echo "  $DEMO_NAME"
echo "========================================"
echo ""

echo "This demo shows how to fuzz the practice binaries"
echo "to discover vulnerabilities automatically."
echo ""

echo "Available Fuzzing Tools:"
echo "------------------------"
echo "  • AFL++ - American Fuzzy Lop"
echo "  • libFuzzer - LLVM fuzzing library"
echo "  • Radamsa - Test case generator"
echo "  • Honggfuzz - Coverage-guided fuzzer"
echo "  • pf kernel-fuzz - Fast in-memory fuzzing"
echo ""

echo "=== Demo 1: Basic Fuzzing Concept ==="
echo ""
echo "Fuzzing tests programs with random/mutated inputs"
echo "to find crashes and vulnerabilities."
echo ""
echo "Example: Fuzzing stack_overflow with random strings"
echo ""

BINARY="./buffer-overflow/stack_overflow"
if [ -f "$BINARY" ]; then
    echo "Generating random inputs:"
    for i in {1..5}; do
        LEN=$((RANDOM % 200 + 10))
        INPUT=$(python3 -c "import random, string; print(''.join(random.choices(string.ascii_letters + string.digits, k=$LEN)))")
        echo ""
        echo "Test $i: Length $LEN"
        echo "Running: $BINARY \"$INPUT\""
        $BINARY "$INPUT" 2>&1 | head -3 || echo "  → Crashed!"
    done
fi
echo ""

echo "=== Demo 2: AFL++ Fuzzing ==="
echo ""
echo "AFL++ is a powerful coverage-guided fuzzer."
echo ""
echo "Step 1: Compile with AFL instrumentation"
echo "  afl-gcc -o binary_fuzz source.c"
echo ""
echo "Step 2: Create seed corpus"
echo "  mkdir input output"
echo "  echo 'AAAA' > input/seed1"
echo "  echo 'test' > input/seed2"
echo ""
echo "Step 3: Run fuzzer"
echo "  afl-fuzz -i input -o output ./binary_fuzz @@"
echo ""
echo "AFL will mutate inputs and monitor code coverage"
echo "to find interesting test cases and crashes."
echo ""

echo "=== Demo 3: Simple Mutation Fuzzing ==="
echo ""
echo "Demonstrating basic mutation strategies:"
echo ""

if [ -f "./format-string/format_vuln" ]; then
    echo "Fuzzing format_vuln with format string mutations:"
    
    # Format string mutation fuzzing
    MUTATIONS=(
        "%x"
        "%s"
        "%p"
        "%n"
        "%x.%x.%x.%x"
        "%p.%p.%p.%p"
        "AAAA%x"
        "%1\$x"
        "%2147483647d%n"
    )
    
    for mut in "${MUTATIONS[@]}"; do
        echo ""
        echo "Testing: $mut"
        ./format-string/format_vuln "$mut" 2>&1 | head -5 || echo "  → Potential crash"
    done
fi
echo ""

echo "=== Demo 4: Length-Based Fuzzing ==="
echo ""
echo "Testing with incrementally increasing input lengths:"
echo ""

if [ -f "./buffer-overflow/stack_overflow" ]; then
    for len in 10 50 64 72 80 100 150; do
        input=$(python3 -c "print('A'*$len)")
        echo "Length $len:"
        ./buffer-overflow/stack_overflow "$input" 2>&1 | head -2 || echo "  → Crashed at length $len"
    done
fi
echo ""

echo "=== Demo 5: Structured Input Fuzzing ==="
echo ""
echo "Fuzzing command injection with various payloads:"
echo ""

if [ -f "./command-injection/cmd_injection" ]; then
    PAYLOADS=(
        "localhost"
        "localhost;"
        "localhost;id"
        "localhost&&id"
        "localhost|id"
        "localhost\`id\`"
        "localhost\$(id)"
        "localhost;cat /etc/passwd"
    )
    
    for payload in "${PAYLOADS[@]}"; do
        echo ""
        echo "Payload: $payload"
        ./command-injection/cmd_injection ping "$payload" 2>&1 | tail -3
    done
fi
echo ""

echo "=== Demo 6: Heap Fuzzing ==="
echo ""
echo "Fuzzing heap exploits with operation sequences:"
echo ""

if [ -f "./heap-exploits/double_free" ]; then
    echo "Testing double-free sequences:"
    echo ""
    
    # Sequence 1: Normal
    echo "Sequence: create, free"
    ./heap-exploits/double_free create "AAAA" 2>&1 | tail -1
    ./heap-exploits/double_free free 0 2>&1 | tail -1
    echo ""
    
    # Sequence 2: Double free (should work since state isn't persistent in this version)
    echo "Testing would involve multiple invocations with state tracking"
fi
echo ""

echo "=== Demo 7: Coverage-Guided Fuzzing Concept ==="
echo ""
echo "Coverage-guided fuzzing monitors which code paths"
echo "are executed and prioritizes inputs that explore"
echo "new code."
echo ""
echo "Benefits:"
echo "  • Finds deep bugs"
echo "  • More efficient than blind fuzzing"
echo "  • Discovers edge cases"
echo ""
echo "Tools that support this:"
echo "  • AFL++"
echo "  • libFuzzer"
echo "  • Honggfuzz"
echo ""

echo "=== Demo 8: Fuzzing Best Practices ==="
echo ""
echo "1. Start with valid inputs (seed corpus)"
echo "2. Monitor crashes and hangs"
echo "3. Use sanitizers (ASAN, UBSAN, MSAN)"
echo "4. Run for extended periods (hours/days)"
echo "5. Triage and analyze crashes"
echo "6. Minimize crashing inputs"
echo "7. Report and fix vulnerabilities"
echo ""

echo "=== Demo 9: Building Fuzzing Harness ==="
echo ""
echo "Example harness for libFuzzer:"
echo ""
echo "  #include <stdint.h>"
echo "  #include <stddef.h>"
echo "  "
echo "  extern void vulnerable_function(char *input);"
echo "  "
echo "  int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {"
echo "      if (size == 0) return 0;"
echo "      char *input = malloc(size + 1);"
echo "      memcpy(input, data, size);"
echo "      input[size] = '\\0';"
echo "      vulnerable_function(input);"
echo "      free(input);"
echo "      return 0;"
echo "  }"
echo ""
echo "Compile: clang -fsanitize=fuzzer,address harness.c vuln.c"
echo "Run: ./a.out"
echo ""

echo "=== Demo 10: Integration with pf ==="
echo ""
echo "Using pf task runner for fuzzing:"
echo ""
echo "  # Fast in-memory fuzzing"
echo "  pf kernel-fuzz-in-memory binary=./buffer-overflow/stack_overflow"
echo ""
echo "  # Complexity analysis (find interesting functions)"
echo "  pf kernel-complexity-analyze binary=./buffer-overflow/stack_overflow"
echo ""
echo "  # Parse function detection"
echo "  pf kernel-parse-detect binary=./format-string/format_vuln"
echo ""

echo "========================================"
echo "  Fuzzing Demo Complete!"
echo "========================================"
echo ""
echo "Next Steps:"
echo "  1. Install AFL++: apt-get install afl++"
echo "  2. Recompile binaries with instrumentation"
echo "  3. Create seed corpus"
echo "  4. Run fuzzer for extended period"
echo "  5. Analyze discovered crashes"
echo "  6. Write exploits for vulnerabilities"
