# Kernel Debugging Tools Demo

This example demonstrates the advanced kernel-mode debugging features on a test binary.

## Test Binary

The `test_binary.c` contains:
- A vulnerable function using `strcpy()` (buffer overflow)
- A safe function using `strncpy()`
- Command-line argument parsing

## Building

```bash
cd demos/kernel-debugging/examples
gcc -o test_binary test_binary.c -g
```

## Demonstrations

### 1. Automatic Breakpoint Generation

Generate LLDB breakpoint script for dangerous functions:

```bash
$ python3 tools/debugging/reversing/auto_breakpoints.py demos/kernel-debugging/examples/test_binary

[*] Generating automatic breakpoints for demos/kernel-debugging/examples/test_binary
[+] Targeting 11 functions

[+] Breakpoint script saved to: test_binary_breakpoints.lldb
```

The generated script sets breakpoints on:
- Memory allocation: `malloc`, `free`, `realloc`, `calloc`
- String operations: `strcpy`, `strcat`, `sprintf`, `gets`
- Memory operations: `memcpy`, `memmove`, `strncpy`

### 2. LLDB Automation

Run automated LLDB session (requires LLDB installed):

```bash
python3 tools/debugging/reversing/lldb_automation.py demos/kernel-debugging/examples/test_binary
```

This will:
- Load the binary in LLDB
- Set breakpoints on dangerous functions
- Run the program
- Print stack traces on breakpoint hits

### 3. Radare2 Analysis

Analyze with radare2 (requires r2pipe installed):

```bash
# Install r2pipe first
pip3 install r2pipe

# Run analysis
python3 tools/debugging/reversing/r2_automation.py demos/kernel-debugging/examples/test_binary
```

Output includes:
- Binary information (architecture, OS, etc.)
- Function list
- Dangerous function imports (strcpy detected!)
- String analysis
- Control flow graph

Example output:
```
=== Binary Information ===
Architecture: x86
Bits: 64
OS: linux

[+] Found 3 functions:
    main                                     @ 0x00001149 (size: 123)
    vulnerable_function                      @ 0x000010c9 (size: 45)
    safe_function                           @ 0x000010f6 (size: 67)

[!] Found 1 potentially dangerous functions:
    strcpy @ 0x1030
```

### 4. Vulnerability Scanning

Scan for common vulnerability patterns:

```bash
python3 tools/debugging/vulnerability/scan_vulnerabilities.py demos/kernel-debugging/examples/test_binary
```

This would identify:
- Use of dangerous `strcpy()` function
- Potential buffer overflow in `vulnerable_function()`
- Recommendations to use safe alternatives

### 5. Fast Fuzzing

Fuzz the binary to find crashes:

```bash
# Basic fuzzing - 100 iterations for demo
python3 tools/debugging/fuzzing/fast_fuzzer.py demos/kernel-debugging/examples/test_binary 100 1
```

The fuzzer will:
- Generate various input payloads
- Feed them to the binary
- Detect crashes and hangs
- Report any issues found

### 6. Create Custom Plugin

Create a radare2 plugin for custom analysis:

```bash
python3 tools/debugging/plugins/create_r2_plugin.py buffer_overflow_checker ./plugins
```

This generates a plugin template that can be extended to perform custom analysis.

## Expected Results

Running these tools on `test_binary` should:

✅ **Auto Breakpoints**: Generate LLDB script with 11 breakpoints on dangerous functions
✅ **LLDB Automation**: Break on `strcpy()` when vulnerable_function() is called
✅ **Radare2**: Identify `strcpy` in imports, show 3 functions, extract strings
✅ **Vuln Scan**: Flag dangerous use of `strcpy()` function
✅ **Fuzzing**: Potentially trigger buffer overflow with long inputs

## Complete Workflow

Run all tools in sequence:

```bash
#!/bin/bash
BINARY="demos/kernel-debugging/examples/test_binary"

echo "1. Building binary..."
cd demos/kernel-debugging/examples
gcc -o test_binary test_binary.c -g
cd ../../..

echo "2. Generating breakpoints..."
python3 tools/debugging/reversing/auto_breakpoints.py $BINARY

echo "3. Vulnerability scan..."
python3 tools/debugging/vulnerability/scan_vulnerabilities.py $BINARY

echo "4. Quick fuzz test..."
python3 tools/debugging/fuzzing/fast_fuzzer.py $BINARY 50 1

echo "Done!"
```

## Safety Note

This test binary is intentionally vulnerable for demonstration purposes. Never use vulnerable code in production!

## Next Steps

- Try the same tools on real kernel drivers
- Use IOCTL discovery tools on loaded kernel modules
- Analyze firmware images with firmware tools
- Deploy fuzzing campaigns to microVM swarms

See [`docs/KERNEL-DEBUGGING.md`](../../docs/KERNEL-DEBUGGING.md) for comprehensive documentation.
