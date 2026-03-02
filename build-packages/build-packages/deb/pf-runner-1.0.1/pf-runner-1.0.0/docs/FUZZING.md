# Fuzzing and Sanitizer Integration

This document describes the comprehensive fuzzing and sanitizer capabilities integrated into the pf task runner, enabling turnkey security testing and vulnerability discovery.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Sanitizers](#sanitizers)
- [libfuzzer Integration](#libfuzzer-integration)
- [AFL++ Integration](#aflplusplus-integration)
- [Binary Lifting + Fuzzing](#binary-lifting--fuzzing)
- [Examples](#examples)
- [Best Practices](#best-practices)

## Overview

The pf task runner now provides integrated support for:

1. **Sanitizers**: ASan, MSan, UBSan, TSan for detecting memory errors, undefined behavior, and race conditions
2. **libfuzzer**: LLVM's in-process, coverage-guided fuzzing engine
3. **AFL++**: Advanced fuzzing with LLVM instrumentation
4. **Binary Lifting**: Lift compiled binaries to LLVM IR, instrument them, and fuzz black-box binaries

This integration makes it trivial to add security testing to any project with minimal configuration.

## Features

### ✨ Key Capabilities

- **🛡️ Turnkey Sanitizer Support**: Build with ASan, MSan, UBSan, or TSan with a single command
- **🎯 libfuzzer Integration**: In-process fuzzing with coverage-guided mutation
- **⚡ AFL++ Support**: Industry-standard fuzzer with LLVM instrumentation
- **🔬 Binary Lifting**: Fuzz black-box binaries by lifting to LLVM IR (via RetDec)
- **📊 Corpus Management**: Automated corpus minimization and crash analysis
- **🚀 One-Command Fuzzing**: `pf afl-fuzz` for complete fuzzing workflows

### 🎪 "Good Luck With That" Achievement Unlocked

As mentioned in the AFL++ documentation about instrumenting lifted binaries:
> "Good luck with that"

**Challenge accepted!** We successfully combined:
- RetDec for binary-to-LLVM lifting (since 1998... approximately)
- AFL++ LLVM instrumentation passes
- Comprehensive fuzzing infrastructure

Result: You can now fuzz closed-source/black-box binaries by lifting them to LLVM IR and instrumenting them extensively! 🎉

## Installation

### Install All Tools

```bash
pf install-fuzzing-tools
```

This installs:
- LLVM sanitizer libraries
- libfuzzer development files
- AFL++ with LLVM support

### Install Individual Components

```bash
# Just sanitizers
pf install-sanitizers

# Just libfuzzer
pf install-libfuzzer

# Just AFL++
pf install-aflplusplus
```

## Sanitizers

Sanitizers are instrumentation-based tools that detect bugs at runtime. They're incredibly effective for finding memory safety issues and undefined behavior.

### Available Sanitizers

#### AddressSanitizer (ASan)
Detects:
- Buffer overflows (stack and heap)
- Use-after-free
- Double-free
- Memory leaks (with LeakSanitizer)

```bash
pf build-with-asan source=myprogram.c
```

#### MemorySanitizer (MSan)
Detects:
- Use of uninitialized memory
- Reading from uninitialized variables

```bash
pf build-with-msan source=myprogram.c
```

#### UndefinedBehaviorSanitizer (UBSan)
Detects:
- Integer overflow
- Null pointer dereference
- Invalid type casts
- Array bounds violations

```bash
pf build-with-ubsan source=myprogram.c
```

#### ThreadSanitizer (TSan)
Detects:
- Data races in multithreaded programs
- Deadlocks

```bash
pf build-with-tsan source=myprogram.c
```

### Build with Multiple Sanitizers

```bash
# Build separate binaries with each sanitizer
pf build-with-all-sanitizers source=myprogram.c

# Creates:
# - myprogram_asan
# - myprogram_msan
# - myprogram_ubsan
# - myprogram_tsan
```

### Running Sanitizer-Instrumented Binaries

```bash
# Run with default settings
./myprogram_asan

# Run with custom options
ASAN_OPTIONS=detect_leaks=1:strict_string_checks=1 ./myprogram_asan

# Common options
ASAN_OPTIONS=detect_leaks=1:halt_on_error=0:log_path=asan.log ./myprogram_asan
MSAN_OPTIONS=poison_in_dtor=1:print_stacktrace=1 ./myprogram_msan
UBSAN_OPTIONS=print_stacktrace=1:halt_on_error=0 ./myprogram_ubsan
```

## libfuzzer Integration

libfuzzer is a coverage-guided fuzzing engine that runs in-process with your code. It's extremely fast and effective for finding bugs.

### Creating a Fuzzing Harness

Generate a template:

```bash
pf generate-libfuzzer-template output=fuzz_target.c
```

This creates a template like:

```c
#include <stdint.h>
#include <stddef.h>

int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size == 0) return 0;
    
    // Call your target function with the fuzzer-provided data
    // target_function(data, size);
    
    return 0;
}
```

### Building a Fuzzer

```bash
# Build with ASan (recommended)
pf build-libfuzzer-target source=fuzz_target.c output=fuzzer

# The build command is equivalent to:
# clang -fsanitize=fuzzer,address -g fuzz_target.c -o fuzzer
```

### Running libfuzzer

```bash
# Run for 60 seconds
pf run-libfuzzer target=fuzzer time=60

# Run with custom corpus
pf run-libfuzzer target=fuzzer corpus=./my_corpus time=300

# Direct execution with options
./fuzzer -max_total_time=60 -print_final_stats=1 ./corpus
```

### libfuzzer Options

Common options you can pass directly:
- `-max_total_time=N`: Run for N seconds
- `-max_len=N`: Maximum input length
- `-dict=file.dict`: Use a dictionary for mutations
- `-jobs=N`: Parallel fuzzing jobs
- `-fork=N`: Fork N processes
- `-print_final_stats=1`: Show statistics at end

## AFL++ Integration

AFL++ is a powerful, battle-tested fuzzer with extensive instrumentation capabilities.

### Building AFL++ Targets

```bash
# Standard AFL++ build
pf build-afl-target source=target.c output=target_afl

# LLVM LTO mode (faster, better coverage)
pf build-afl-llvm-target source=target.c output=target_afl_lto
```

### Running AFL++

```bash
# Basic fuzzing (60 minutes)
pf afl-fuzz target=target_afl time=60m

# Custom input/output directories
pf afl-fuzz target=target_afl input=./seeds output=./results time=2h

# Parallel fuzzing (run multiple instances)
afl-fuzz -i seeds -o out -M fuzzer1 -- ./target_afl &
afl-fuzz -i seeds -o out -S fuzzer2 -- ./target_afl &
afl-fuzz -i seeds -o out -S fuzzer3 -- ./target_afl &
```

### Analyzing Results

```bash
# Analyze crashes
pf afl-analyze-crashes crashes=./fuzzing/out/default/crashes

# Minimize corpus for faster fuzzing
pf afl-minimize-corpus input=./out/default/queue output=./minimized

# Reproduce a crash
./target_afl < ./out/default/crashes/id:000000,sig:11,*
```

### AFL++ Advanced Features

#### Persistent Mode
For even faster fuzzing, use AFL++'s persistent mode:

```c
__AFL_FUZZ_INIT();

int main(int argc, char **argv) {
  #ifdef __AFL_HAVE_MANUAL_CONTROL
    __AFL_INIT();
  #endif

  unsigned char *buf = __AFL_FUZZ_TESTCASE_BUF;

  while (__AFL_LOOP(10000)) {
    int len = __AFL_FUZZ_TESTCASE_LEN;
    
    // Your target function
    target_function(buf, len);
  }

  return 0;
}
```

## Binary Lifting + Fuzzing

This is where things get really interesting. We can fuzz closed-source binaries by lifting them to LLVM IR!

### The Workflow

1. **Lift**: Convert binary → LLVM IR using RetDec
2. **Instrument**: Add AFL++ instrumentation to the LLVM IR
3. **Compile**: Generate an instrumented binary
4. **Fuzz**: Run AFL++ on the instrumented binary

### One-Command Lifting + Fuzzing

```bash
# Lift binary, instrument, and prepare for fuzzing
pf lift-and-instrument-binary binary=/path/to/binary output=binary_fuzzable
```

This command:
1. Uses RetDec to lift the binary to LLVM IR
2. Applies AFL++ LLVM instrumentation passes
3. Compiles to an instrumented binary
4. Saves intermediate IR for inspection

### Manual Workflow

```bash
# Step 1: Lift binary to LLVM IR (using existing lifting tasks)
pf lift-binary-retdec binary=/bin/target

# Step 2: Instrument the LLVM IR
pf instrument-llvm-ir-afl input=/tmp/lifting/target.ll output=target_instrumented

# Step 3: Fuzz the instrumented binary
pf afl-fuzz target=target_instrumented time=1h
```

### Inspecting Lifted IR

```bash
# View the lifted LLVM IR
cat /tmp/fuzzing-lift/binary.ll

# Optimize the lifted IR before fuzzing
opt -O2 /tmp/fuzzing-lift/binary.ll -o /tmp/fuzzing-lift/binary_opt.ll

# Compare instrumented vs non-instrumented
diff /tmp/fuzzing-lift/binary.ll /tmp/fuzzing-lift/binary_instrumented.ll
```

## Examples

### Complete Demonstration

Run a full fuzzing demonstration:

```bash
pf demo-fuzzing
```

This creates a deliberately vulnerable example program and demonstrates:
- Building with sanitizers
- Creating a libfuzzer harness
- Building an AFL++ target
- Running fuzzing campaigns

### Example: Fuzzing a Parsing Function

Create `parse_fuzzer.c`:

```c
#include <stdint.h>
#include <string.h>

// Your vulnerable parser
int parse_protocol(const uint8_t *data, size_t len) {
    char buffer[256];
    if (len > 4 && data[0] == 'M' && data[1] == 'A' && data[2] == 'G' && data[3] == 'I' && data[4] == 'C') {
        // Vulnerable: no bounds check
        memcpy(buffer, data + 5, len - 5);
    }
    return 0;
}

// libfuzzer harness
int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    parse_protocol(data, size);
    return 0;
}
```

Build and fuzz:

```bash
# Build with ASan
pf build-libfuzzer-target source=parse_fuzzer.c output=parse_fuzzer

# Run fuzzing
pf run-libfuzzer target=parse_fuzzer time=120

# Crashes will be in ./crash-* files
```

### Example: Fuzzing a Closed-Source Binary

```bash
# 1. Get the binary (for demo purposes, use a system binary)
cp /usr/bin/some-utility ./target_binary

# 2. Lift and instrument
pf lift-and-instrument-binary binary=./target_binary output=target_fuzzable

# 3. Create input seeds
mkdir -p ./seeds
echo "test input" > ./seeds/seed1
echo "another test" > ./seeds/seed2

# 4. Fuzz!
pf afl-fuzz target=target_fuzzable input=./seeds time=30m

# 5. Analyze results
pf afl-analyze-crashes crashes=./fuzzing/out/default/crashes
```

## Best Practices

### 1. Always Use Sanitizers

Combine fuzzing with sanitizers for maximum bug detection:

```bash
# libfuzzer automatically includes ASan
pf build-libfuzzer-target source=target.c

# For AFL++, add sanitizers explicitly
afl-clang-fast -fsanitize=address,undefined target.c -o target_afl
```

### 2. Start with Good Seeds

Quality input corpus significantly improves fuzzing efficiency:

```bash
# Collect real-world inputs
mkdir -p ./corpus
cp /path/to/valid/inputs/* ./corpus/

# Or use afl-cmin to minimize
pf afl-minimize-corpus input=./raw_corpus output=./corpus
```

### 3. Use Dictionaries

Dictionaries help fuzzers discover complex formats:

```bash
# Create a dictionary
cat > protocol.dict << EOF
header="MAGIC"
cmd_1="CMD1"
cmd_2="CMD2"
EOF

# Use with libfuzzer
./fuzzer -dict=protocol.dict ./corpus

# Use with AFL++
afl-fuzz -x protocol.dict -i seeds -o out -- ./target
```

### 4. Monitor Coverage

```bash
# AFL++ shows coverage in the UI
afl-fuzz -i in -o out -M main -- ./target

# For deeper analysis, use llvm-cov
clang -fprofile-instr-generate -fcoverage-mapping target.c -o target
./target < input
llvm-profdata merge default.profraw -o default.profdata
llvm-cov show ./target -instr-profile=default.profdata
```

### 5. Parallel Fuzzing

Run multiple AFL++ instances for better coverage:

```bash
# Terminal 1: Master
afl-fuzz -i seeds -o out -M master -- ./target

# Terminal 2-N: Slaves
afl-fuzz -i seeds -o out -S slave1 -- ./target
afl-fuzz -i seeds -o out -S slave2 -- ./target
```

### 6. Triage Crashes Systematically

```bash
# 1. Collect all crashes
pf afl-analyze-crashes

# 2. Deduplicate (AFL++ does this automatically)
ls fuzzing/out/default/crashes/

# 3. Reproduce with sanitizers
./target_asan < fuzzing/out/default/crashes/id:000000*

# 4. Debug with GDB/LLDB
gdb ./target_asan
(gdb) run < fuzzing/out/default/crashes/id:000000*
```

## Integration with Existing Workflows

### CI/CD Integration

Add fuzzing to your CI pipeline:

```yaml
# .github/workflows/fuzzing.yml
name: Continuous Fuzzing

on:
  schedule:
    - cron: '0 0 * * *'  # Daily

jobs:
  fuzz:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install fuzzing tools
        run: pf install-fuzzing-tools
      
      - name: Build fuzzing target
        run: pf build-libfuzzer-target source=fuzz_target.c
      
      - name: Run fuzzing (5 minutes)
        run: pf run-libfuzzer target=fuzzer time=300
      
      - name: Upload crashes
        if: failure()
        uses: actions/upload-artifact@v2
        with:
          name: crashes
          path: crash-*
```

### Pre-commit Hooks

```bash
# .git/hooks/pre-commit
#!/bin/bash
pf build-with-asan source=mylib.c
./mylib_asan --run-tests
```

## Troubleshooting

### libfuzzer not finding bugs

- Increase fuzzing time: `time=3600` (1 hour)
- Improve seed corpus quality
- Add a dictionary for the input format
- Use `-reduce_inputs=1` to simplify corpus

### AFL++ hangs or no paths

- Check if target reads from stdin: `./target < seed`
- Verify instrumentation: `afl-showmap -o /dev/null -- ./target < seed`
- Try different AFL++ modes: `afl-clang-lto` vs `afl-clang-fast`

### Sanitizer false positives

- Review ASAN/MSAN options to suppress known issues
- Use sanitizer blacklists: `-fsanitize-blacklist=ignorelist.txt`

### Binary lifting fails

- Ensure RetDec is installed: `pf install-retdec`
- Try simpler binaries first (statically linked, no obfuscation)
- Check lifted IR manually: `cat /tmp/fuzzing-lift/binary.ll`

## Resources

- [LLVM libfuzzer documentation](https://llvm.org/docs/LibFuzzer.html)
- [AFL++ documentation](https://aflplus.plus/)
- [AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html)
- [MemorySanitizer](https://clang.llvm.org/docs/MemorySanitizer.html)
- [UndefinedBehaviorSanitizer](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html)
- [ThreadSanitizer](https://clang.llvm.org/docs/ThreadSanitizer.html)

## Quick Reference

```bash
# Installation
pf install-fuzzing-tools

# Sanitizers
pf build-with-asan source=file.c
pf build-with-msan source=file.c
pf build-with-ubsan source=file.c
pf build-with-tsan source=file.c

# libfuzzer
pf generate-libfuzzer-template
pf build-libfuzzer-target source=fuzz.c
pf run-libfuzzer target=fuzzer time=60

# AFL++
pf build-afl-target source=target.c
pf afl-fuzz target=target_afl time=1h
pf afl-analyze-crashes

# Binary Lifting + Fuzzing
pf lift-and-instrument-binary binary=/path/to/bin
pf afl-fuzz target=bin_afl_lifted time=30m

# Help
pf fuzzing-help
```

---

**Happy Fuzzing! May your crashes be plentiful and your bugs be swiftly squashed! 🐛🔨**
