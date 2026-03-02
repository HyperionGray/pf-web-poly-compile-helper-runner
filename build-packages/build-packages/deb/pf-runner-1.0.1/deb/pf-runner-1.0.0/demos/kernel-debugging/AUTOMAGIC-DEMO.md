# Automagic Parse Function Detection Demo

This demo showcases the new automagic vulnerability detection features:
- Parse function detection
- Complexity analysis
- In-memory fuzzing

## Quick Start

```bash
# 1. Build the vulnerable test binary
make

# 2. Run comprehensive automagic analysis
pf kernel-automagic-analysis binary=./vulnerable_parser

# 3. Run individual tools
pf kernel-parse-detect binary=./vulnerable_parser
pf kernel-complexity-analyze binary=./vulnerable_parser
pf kernel-fuzz-in-memory binary=./vulnerable_parser function=parse_command
```

## What This Demo Shows

### Parse Function Detection
The test binary contains multiple types of parse functions:
- `parse_config` - String parsing with many if/else statements
- `parse_user_input` - File input handling
- `parse_command` - Vulnerable command parsing (buffer overflow)
- `process_data` - Long function with complex control flow

The detector automatically identifies these as high-priority targets.

### Complexity Analysis
The complexity analyzer identifies:
- `parse_config` - High complexity (23 conditional jumps)
- `process_data` - Large function with nested loops
- High risk scores for both functions

### Vulnerability Patterns
The scanner detects:
- Dangerous functions: `scanf`, `gets`
- Input→parsing pipeline (CRITICAL)
- Parse + buffer manipulation (HIGH)

### In-Memory Fuzzing
The fuzzer provides setup for blazing-fast fuzzing:
- LLDB/GDB configuration
- Mutation strategies
- Loop-back capability
- Crash monitoring

## Step-by-Step Walkthrough

### Step 1: Build the Test Binary

```bash
make
```

This creates `vulnerable_parser` with debug symbols.

### Step 2: Detect Parse Functions

```bash
pf kernel-parse-detect binary=./vulnerable_parser output=parse_results.json
```

**Expected output:**
- 5+ parse functions detected
- High priority: `parse_user_input`, `parse_command`
- CRITICAL vulnerability patterns

### Step 3: Analyze Complexity

```bash
pf kernel-complexity-analyze binary=./vulnerable_parser output=complexity.json
```

**Expected output:**
- `parse_config`: Risk score ~48/100
- `process_data`: Risk score ~44/100
- Both flagged for high complexity

### Step 4: Scan for Vulnerabilities

```bash
python3 ../../tools/debugging/vulnerability/scan_vulnerabilities.py ./vulnerable_parser
```

**Expected findings:**
- Dangerous functions: scanf (HIGH), gets (CRITICAL)
- Format string functions: printf
- Interesting strings in binary

### Step 5: Combined Analysis

```bash
pf kernel-automagic-analysis binary=./vulnerable_parser
```

This runs all tools in sequence and provides:
- Comprehensive JSON reports
- Prioritized target list
- Specific fuzzing recommendations

### Step 6: Set Up In-Memory Fuzzing

```bash
pf kernel-fuzz-in-memory binary=./vulnerable_parser function=parse_command
```

Follow the generated guide to set up fast fuzzing:

1. Start LLDB with target binary
2. Set breakpoints at function entry/exit
3. Configure mutation and loop-back
4. Run thousands of iterations in-process

## Expected Results

### Parse Function Detector
```
HIGH PRIORITY (5) functions:
  - parse_user_input (string_parsing, input_handling)
  - parse_command (string_parsing) ← VULNERABLE!
  - fgets@plt (input_handling)
  - __isoc99_sscanf@plt (string_parsing)
  - parse_config (string_parsing)

VULNERABLE PATTERNS:
  - Input parsing pipeline (CRITICAL)
  - Parse + buffer manipulation (HIGH)
  - Dangerous functions: gets, scanf
```

### Complexity Analyzer
```
TOP HOTSPOTS:
  1. parse_config (Risk: 47.91/100)
     - 22 conditional jumps (many if/else)
     - High cyclomatic complexity
  
  2. process_data (Risk: 44.43/100)
     - Large function (732 bytes)
     - Complex nested loops
```

### Combined Recommendations
```
Priority targets for fuzzing:
  1. parse_command (HIGH + input handling + dangerous functions)
  2. parse_config (HIGH complexity + many branches)
  3. parse_user_input (input source + parsing)
  4. process_data (large + complex)
```

## Understanding the Vulnerabilities

### Buffer Overflow in parse_command()
```c
void parse_command(char *input) {
    char cmd[128];
    char arg[128];
    
    // VULNERABLE: No bounds checking!
    sscanf(input, "%s %s", cmd, arg);
    ...
}
```

**Why it's vulnerable:**
- Fixed-size buffers (128 bytes)
- `%s` format specifier has no width limit
- Input can overflow both `cmd` and `arg`

**How to exploit:**
```bash
# Create input larger than 128 bytes
python3 -c 'print("A" * 200)' > overflow.txt
./vulnerable_parser overflow.txt
```

### Complex Control Flow in parse_config()
```c
int parse_config(const char *input) {
    if (strcmp(input, "option1") == 0) {
        return 1;
    } else if (strcmp(input, "option2") == 0) {
        return 2;
    } else if ... // 10+ more branches
}
```

**Why it's a problem:**
- Many execution paths = many edge cases
- Easy to miss corner cases in testing
- High chance of logic bugs

### Long Function in process_data()
- 732 bytes of code
- Nested loops
- Complex transformations
- Many potential off-by-one errors

## Fuzzing the Vulnerable Binary

### Traditional Fuzzing (Slow)
```bash
# Using fast_fuzzer.py
python3 ../../tools/debugging/fuzzing/fast_fuzzer.py ./vulnerable_parser 10000
```

Expect: ~100-500 executions/second

### In-Memory Fuzzing (Fast)
Following the guide from `pf kernel-fuzz-in-memory`:

```lldb
# In LLDB
(lldb) target create ./vulnerable_parser
(lldb) breakpoint set -n parse_command
(lldb) run overflow.txt

# At breakpoint, get input buffer address
(lldb) register read rdi  # First argument (input pointer)

# Set return breakpoint
(lldb) disassemble -n parse_command
(lldb) breakpoint set -a <addr_before_ret>

# Mutation loop (manual or scripted)
# This is 100-1000x faster!
```

## Learning Objectives

After completing this demo, you should understand:

1. **Parse Function Detection**
   - How to automatically identify parse functions
   - Why parse functions are vulnerability hotspots
   - How to prioritize fuzzing targets

2. **Complexity Analysis**
   - What makes a function complex
   - How complexity relates to bugs
   - How to calculate risk scores

3. **In-Memory Fuzzing**
   - Why it's faster than traditional fuzzing
   - How to set up loop-back fuzzing
   - Mutation strategies for maximum coverage

4. **Vulnerability Patterns**
   - Input→parsing pipelines
   - Dangerous function combinations
   - Buffer operations with parsing

## Next Steps

1. **Modify the code** to fix vulnerabilities
2. **Re-run analysis** to verify fixes
3. **Add your own** parse functions to test
4. **Try different** mutation strategies
5. **Experiment with** jump-back depths

## Resources

- [KERNEL-DEBUGGING.md](../../docs/KERNEL-DEBUGGING.md) - Full documentation
- [parse_function_detector.py](../../tools/debugging/vulnerability/parse_function_detector.py)
- [complexity_analyzer.py](../../tools/debugging/vulnerability/complexity_analyzer.py)
- [in_memory_fuzzer.py](../../tools/debugging/fuzzing/in_memory_fuzzer.py)

## Troubleshooting

**radare2 not available:**
```bash
pip install r2pipe
sudo apt-get install radare2
```

**LLDB not found:**
```bash
sudo apt-get install lldb
```

**Binary not found:**
```bash
make clean && make
```

**Permission denied:**
```bash
chmod +x vulnerable_parser
```
