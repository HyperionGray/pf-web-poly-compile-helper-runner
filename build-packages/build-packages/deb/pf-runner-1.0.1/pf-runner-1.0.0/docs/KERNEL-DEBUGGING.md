# Advanced Kernel-Mode Debugging Guide

This guide covers advanced low-level debugging features for kernel drivers, firmware analysis, and system-level code, with integration for LLDB, radare2, and Ghidra.

## Overview

The debugging framework provides comprehensive tools for:

- **🎯 Automagic Parse Function Detection**: Automatically identify parse functions for vulnerability research
- **📊 Complexity Analysis**: Detect functions with many if/else statements and high complexity
- **⚡ In-Memory Fuzzing**: Blazing fast fuzzing with loop-back capability for maximum speed
- **IOCTL Discovery & Fuzzing**: Discover and test kernel driver IOCTLs
- **Firmware Analysis**: Extract, analyze, and flash firmware images
- **Reversing Automation**: Automated debugging with LLDB, radare2, and Ghidra
- **Vulnerability Detection**: Heuristic-based security analysis
- **Fast Fuzzing**: High-speed fuzzing with crash detection
- **MicroVM Swarms**: Parallel fuzzing with VMKit integration
- **Plugin Development**: Create radare2 and Binary Ninja plugins

## Quick Start

### Installation

Install all debugging tools:

```bash
pf install-debug-tools
```

Or install components individually:

```bash
pf install-radare2        # radare2 + r2pipe
pf install-lldb           # LLDB debugger
pf install-ghidra         # Ghidra helper scripts
pf install-firmware-tools # binwalk, flashrom
pf install-fuzzing-tools  # Syzkaller, AFL++
```

### Basic Usage

Run a complete debugging workflow:

```bash
pf debug-workflow-full binary=/path/to/binary
```

**NEW: Automagic Analysis** 🎯

Run comprehensive automatic analysis to find parse functions, complex code, and vulnerability hotspots:

```bash
# Complete automagic analysis
pf kernel-automagic-analysis binary=/path/to/binary

# Individual tools
pf kernel-parse-detect binary=/path/to/binary
pf kernel-complexity-analyze binary=/path/to/binary
pf kernel-fuzz-in-memory binary=/path/to/binary function=parse_input
```

Or use individual tools:

```bash
# Discover IOCTLs in a driver
pf ioctl-discover binary=/path/to/driver.ko

# Analyze firmware
pf firmware-analyze image=/path/to/firmware.bin

# Automated reversing with radare2
pf reverse-radare2 binary=/path/to/binary

# Fast fuzzing
pf fuzz-basic binary=/path/to/binary iterations=10000
```

## IOCTL Discovery and Analysis

### Discovering IOCTLs

The IOCTL discovery tool analyzes kernel drivers to find IOCTL command codes:

```bash
pf ioctl-discover binary=/path/to/driver.ko
```

This tool:
- Extracts strings containing IOCTL patterns
- Disassembles the binary to find IOCTL handlers
- Uses radare2 for deep analysis (if available)
- Exports results as JSON

**Output**: `output/driver_ioctls.json`

### Analyzing IOCTL Structure

Analyze IOCTL handlers to understand parameter structures:

```bash
pf ioctl-analyze binary=/path/to/driver.ko
```

This identifies:
- Potential structure sizes
- Input validation checks
- IOCTL implementation patterns (switch, if-else, function tables)

### Fuzzing IOCTLs

Fuzz discovered IOCTLs to find vulnerabilities:

```bash
# Basic fuzzing
pf ioctl-fuzz driver=/dev/mydriver iterations=10000

# With discovered IOCTL list
pf ioctl-discover binary=/path/to/driver.ko
pf ioctl-fuzz driver=/dev/mydriver ioctl_list=./output/driver_ioctls.json
```

**Note**: IOCTL fuzzing requires the driver to be loaded and accessible via `/dev/`.

## 🎯 Automagic Parse Function Detection

Parse functions are goldmines for vulnerability research because they:
- Handle untrusted input from various sources
- Often contain complex logic with edge cases  
- May lack proper bounds checking
- Can contain buffer overflows, integer overflows, format string bugs

### Automatic Detection

The parse function detector automatically identifies:

**String Parsing Functions:**
- `strto*`, `atoi`, `atol`, `atof` family
- `sscanf`, `fscanf`, `scanf` and variants
- Custom parsing functions with "parse" or "tokenize" in the name

**Data Deserialization:**
- JSON, XML, YAML parsers
- Protocol buffer handlers
- Custom deserializers

**Input Handling:**
- `read`, `recv`, `fread`, `fgets`, `gets`
- Network input functions
- File reading functions

**Buffer Manipulation:**
- `memcpy`, `strcpy`, `sprintf` and unsafe variants
- Buffer operations often paired with parsing

### Usage

```bash
# Detect parse functions in binary
pf kernel-parse-detect binary=/path/to/binary

# Save results to JSON for further analysis
pf kernel-parse-detect binary=/path/to/binary output=parse_results.json

# Without radare2 (faster, less detail)
python3 tools/debugging/vulnerability/parse_function_detector.py /path/to/binary --no-r2
```

### Output

The detector provides:

1. **High-priority functions**: Parse functions that handle direct input
2. **Medium-priority functions**: Buffer manipulation and support functions
3. **Vulnerability patterns**: Dangerous combinations detected
4. **Fuzzing recommendations**: Specific targets and commands

Example output:
```
HIGH PRIORITY (5) functions detected:
  - parse_user_input (string_parsing, input_handling)
  - parse_command (string_parsing)
  - deserialize_packet (data_deserialization, protocol_parsing)
  
VULNERABLE PATTERNS:
  - Input parsing pipeline (CRITICAL)
  - Parse + buffer manipulation (HIGH)
  - Dangerous functions: strcpy, sprintf, gets
  
FUZZING RECOMMENDATIONS:
  Target: parse_user_input
  Command: pf fuzz-in-memory binary=/path/to/binary
```

## 📊 Complexity Analysis

Complex functions are bug magnets. This analyzer detects:

### Detection Criteria

**Functions That "Go On Forever":**
- Very large functions (>2000 bytes = large, >5000 bytes = extreme)
- Many basic blocks indicating complex control flow
- High cyclomatic complexity

**Many If/Else Statements:**
- Functions with 30+ conditional jumps
- Complex branching logic
- Switch statements with many cases

**Other Indicators:**
- High number of function calls (>50)
- Many nested loops
- Complex state machines

### Usage

```bash
# Analyze function complexity
pf kernel-complexity-analyze binary=/path/to/binary

# Save detailed report
pf kernel-complexity-analyze binary=/path/to/binary output=complexity.json
```

### Thresholds

The analyzer uses these thresholds to flag functions:

| Metric | Large | Extreme |
|--------|-------|---------|
| Function Size | 2000 bytes | 5000 bytes |
| Basic Blocks | 30 blocks | 50 blocks |
| Cyclomatic Complexity | 20 | 40 |
| Conditional Jumps | 30 | - |
| Function Calls | 50 | - |

### Risk Scoring

Each function gets a risk score (0-100) based on:
- Size: Larger functions have more bugs
- Complexity: More paths = more edge cases
- Branches: More if/else = more bugs
- Calls: Complex interactions

Functions are ranked by risk score, with top hotspots prioritized for fuzzing.

### Example Output

```
TOP VULNERABILITY HOTSPOTS:

1. parse_config
   Risk Score: 47.91/100
   Size: 408 bytes
   Basic Blocks: 23
   Cyclomatic Complexity: 23
   Conditional Jumps: 22
   Indicators: high_complexity

2. process_data  
   Risk Score: 44.43/100
   Size: 732 bytes
   Basic Blocks: 22
   Indicators: high_complexity, large_function
```

## ⚡ In-Memory Fuzzing

Traditional fuzzing spawns new processes for each test case. In-memory fuzzing is **100-1000x faster** by:

1. Setting breakpoint at function return
2. Mutating input data in memory
3. Jumping back to function start (or earlier)
4. Repeating thousands of iterations in-process

### Key Features

**Blazing Fast:**
- No process creation overhead
- No file I/O overhead
- Thousands of iterations per second

**Loop-Back Capability:**
- Jump back to current function (depth=0)
- Jump back to caller (depth=1)
- Jump back multiple frames (depth=2+)
- Test entire call chains with single run

**Mutation Strategies:**
- Bit flipping
- Byte flipping
- Arithmetic mutations
- Interesting values (boundary cases)
- Block deletion/duplication
- Random bytes

### Usage

```bash
# Generate fuzzing setup guide
pf kernel-fuzz-in-memory binary=/path/to/binary

# Target specific function
pf kernel-fuzz-in-memory binary=/path/to/binary function=parse_input

# Configure iterations and jump-back depth
pf kernel-fuzz-in-memory binary=/path/to/binary \
    function=parse_request \
    iterations=10000 \
    jump_back=2
```

### Setup Process

The tool generates a comprehensive guide for setting up in-memory fuzzing:

1. **LLDB Setup**: Start debugger and set breakpoints
2. **Find Return Address**: Locate return instruction
3. **Mutation Loop**: Manual or automated mutation
4. **Automated Fuzzing**: Python script for LLDB
5. **Crash Monitoring**: Detect and analyze crashes
6. **Jump-Back Configuration**: Set call chain depth

### Manual Fuzzing

```lldb
# Start LLDB
$ lldb /path/to/binary

# Set breakpoint at target function
(lldb) breakpoint set -n parse_input
(lldb) run

# Find return address
(lldb) disassemble -n parse_input

# Set breakpoint before return
(lldb) breakpoint set -a 0x401234

# At return breakpoint:
(lldb) memory read $rdi          # Read input buffer
(lldb) memory write $rdi 0xFF... # Write mutated data
(lldb) jump -a 0x401000          # Jump to function start
(lldb) continue                  # Run again
```

### Automated Fuzzing

The tool generates Python scripts for LLDB's scripting API:

```python
import lldb
import random

def fuzz_iteration(debugger, command, result, internal_dict):
    process = debugger.GetSelectedTarget().GetProcess()
    thread = process.GetSelectedThread()
    frame = thread.GetSelectedFrame()
    
    # Get input buffer
    buf_var = frame.FindVariable("input_buffer")
    buf_addr = buf_var.GetAddress()
    
    # Read and mutate
    data = process.ReadMemory(buf_addr, 1024, lldb.SBError())
    mutated = bytearray(data)
    mutated[random.randint(0, len(mutated)-1)] ^= 0xFF
    
    # Write back and jump
    process.WriteMemory(buf_addr, bytes(mutated), lldb.SBError())
    func_start = frame.GetFunction().GetStartAddress()
    thread.JumpToLine(func_start)
    process.Continue()
```

### GDB Alternative

For GDB users:

```bash
$ gdb /path/to/binary
(gdb) break parse_input
(gdb) run
(gdb) break *0x401234  # before return
(gdb) commands
  silent
  set {char[1024]}$buffer_addr = <mutated>
  jump *0x401000
  continue
end
```

### Performance Tips

- Disable output to maximize speed
- Use hardware breakpoints when possible
- Batch mutations (multiple bytes per iteration)
- Deduplicate crashes by address
- Monitor unique crashes only

## 🔬 Combined Automagic Analysis

Run all detection tools in sequence for comprehensive analysis:

```bash
pf kernel-automagic-analysis binary=/path/to/binary
```

This runs:
1. **Parse function detection** → Find input sources
2. **Complexity analysis** → Find vulnerability hotspots  
3. **Vulnerability scanning** → Detect known patterns
4. **Report generation** → Combined recommendations

Output includes:
- JSON files with detailed results
- Prioritized target list for fuzzing
- Specific fuzzing commands
- Risk assessment

### Workflow

```bash
# 1. Automagic analysis
pf kernel-automagic-analysis binary=/path/to/binary

# 2. Review results
cat parse_functions.json
cat complexity_analysis.json

# 3. Focus on high-priority targets
# From parse_functions.json: parse_user_input (HIGH)
# From complexity_analysis.json: process_data (risk: 44.43)

# 4. Run targeted in-memory fuzzing
pf kernel-fuzz-in-memory binary=/path/to/binary function=parse_user_input

# 5. Monitor for crashes and analyze
```

### Best Practices

1. **Start with automagic analysis** to identify targets
2. **Prioritize parse functions** handling direct input
3. **Focus on high-complexity functions** with many branches
4. **Use in-memory fuzzing** for maximum speed
5. **Combine with static analysis** (radare2, Ghidra)
6. **Iterate**: Re-run after code changes

## Vulnerability Detection

### Quick Vulnerability Scan

# With discovered IOCTL list
pf ioctl-discover binary=/path/to/driver.ko
pf ioctl-fuzz driver=/dev/mydriver ioctl_list=./output/driver_ioctls.json
```

**Note**: IOCTL fuzzing requires the driver to be loaded and accessible via `/dev/`.

## Firmware Analysis

### Extracting Firmware

Extract firmware filesystem and components:

```bash
pf firmware-extract image=/path/to/firmware.bin
```

Uses binwalk to:
- Identify filesystem types
- Extract embedded files
- Decompress compressed sections

### Analyzing Firmware Security

Scan firmware for vulnerabilities:

```bash
pf firmware-analyze image=/path/to/firmware.bin
```

This detects:
- Hardcoded credentials
- Debug interfaces (UART, JTAG)
- Cleartext secrets
- High/low entropy sections
- Interesting strings

### Flashing Firmware

**Warning**: Flashing firmware can brick devices. Always verify compatibility.

Read firmware from device:

```bash
pf firmware-read chip=MX25L3205D output=backup.bin
```

Flash firmware to device:

```bash
pf firmware-flash chip=MX25L3205D file=modified.bin verify=true
```

Supported programmers:
- `internal` - Internal hardware programmer
- `ft2232_spi` - FTDI-based SPI programmer
- `ch341a_spi` - CH341A USB programmer

See `flashrom -p help` for full list.

## Reversing Automation

### LLDB Automation

Automated debugging sessions with LLDB:

```bash
# Basic analysis
pf reverse-lldb binary=/path/to/binary

# With custom script
pf reverse-lldb binary=/path/to/binary script=/path/to/script.lldb

# With function breakpoints
LLDB_FUNCTIONS="malloc,free,strcpy" pf reverse-lldb binary=/path/to/binary

# With conditional breakpoints
LLDB_CONDITIONS="malloc:size>1024;strcpy:dst==0" pf reverse-lldb binary=/path/to/binary
```

The automation:
- Sets breakpoints on common functions (malloc, strcpy, etc.)
- Adds system call breakpoints
- Prints registers and stack on breakpoint hits
- Generates backtrace on crashes

### Radare2 Automation

Automated analysis with radare2 and r2pipe:

```bash
# Basic analysis
pf reverse-radare2 binary=/path/to/binary

# With custom commands
echo "aaa" > commands.txt
echo "pdf @ main" >> commands.txt
pf reverse-radare2 binary=/path/to/binary commands=commands.txt
```

The automation:
- Performs auto-analysis (aaa)
- Lists functions, imports, exports
- Extracts strings
- Identifies dangerous functions
- Generates control flow graphs

### Ghidra Headless Analysis

Run Ghidra analysis in headless mode:

```bash
pf reverse-ghidra binary=/path/to/binary script=/path/to/script.py
```

### Automatic Breakpoint Generation

Generate breakpoints with complex conditionals:

```bash
# Auto-generate for specific functions
pf reverse-auto-breakpoints binary=/path/to/binary functions="malloc,free,strcpy"

# With conditions
pf reverse-auto-breakpoints binary=/path/to/binary \
    functions="malloc" \
    conditions="size>1024"
```

### Control Flow Analysis

Extract and visualize control flow graphs:

```bash
pf reverse-control-flow binary=/path/to/binary
```

Outputs:
- Graphviz DOT files
- Function call graphs
- Basic block graphs

Convert to image:
```bash
dot -Tpng output.dot -o cfg.png
```

## Vulnerability Detection

### Quick Vulnerability Scan

Scan for common vulnerability patterns:

```bash
pf vuln-scan binary=/path/to/binary
```

Detects:
- Buffer overflow vulnerabilities
- Format string bugs
- Integer overflows
- Use-after-free patterns
- Dangerous function usage

### Heuristic Analysis

Advanced heuristic-based weakness detection:

```bash
pf vuln-heuristic binary=/path/to/binary
```

Uses multiple heuristics:
- Control flow complexity analysis
- Data flow tracking
- Memory safety checks
- API misuse detection

### Kernel Module Security Check

Specialized checks for kernel modules:

```bash
pf vuln-kernel-check module=/path/to/module.ko
```

Checks for:
- Missing capability checks
- Unsafe kernel API usage
- Race conditions
- Information leaks

## Fuzzing Infrastructure

### Basic Fast Fuzzer

High-speed fuzzing with crash detection:

```bash
pf fuzz-basic binary=/path/to/binary iterations=10000
```

Features:
- Multiple input generation strategies
- Crash and hang detection
- Progress reporting
- Execution statistics

### Kernel Fuzzing with Syzkaller

Syzkaller is a coverage-guided kernel fuzzer:

```bash
# Setup (one-time)
pf install-fuzzing-tools

# Create config
cat > syzkaller.cfg << EOF
{
  "target": "linux/amd64",
  "http": "127.0.0.1:56741",
  "workdir": "./workdir",
  "kernel_obj": "/path/to/kernel",
  "syzkaller": "/path/to/syzkaller"
}
EOF

# Run fuzzing
pf fuzz-kernel-syzkaller config=syzkaller.cfg duration=3600
```

### KFuzz Kernel Fuzzing

Lightweight kernel fuzzing:

```bash
pf fuzz-kfuzz module=/path/to/module.ko iterations=10000
```

### Parallel Fuzzing

Multi-core fuzzing for speed:

```bash
pf fuzz-parallel binary=/path/to/binary workers=8 iterations=100000
```

Uses all available CPU cores for maximum throughput.

## MicroVM Swarm Fuzzing

For massive parallel fuzzing campaigns using microVMs.

### Setup VMKit Environment

```bash
pf vmkit-setup
```

### Deploy Fuzzing Swarm

Launch fuzzing across multiple microVMs:

```bash
pf vmkit-deploy binary=/path/to/binary vms=20 duration=3600
```

This:
- Spawns 20 microVMs
- Distributes fuzzing workload
- Monitors for crashes
- Collects results automatically

### Monitor Swarm Progress

```bash
pf vmkit-monitor
```

Shows:
- Active VMs
- Executions per second
- Crashes found
- Coverage statistics

### Collect Results

```bash
pf vmkit-collect session_id=<id> output_dir=./results
```

Results include:
- Crash inputs
- Coverage reports
- Crash analysis
- Reproduction scripts

## Plugin Development

### Radare2 Plugins

Create a radare2 plugin template:

```bash
pf plugin-create-radare2 name=my_analyzer output_dir=./plugins
```

This generates:
- Plugin skeleton
- r2pipe integration
- Example commands
- Installation script

Install plugin:

```bash
pf plugin-radare2-install plugin=./plugins/my_analyzer.py
```

### Binary Ninja Plugins

Create a Binary Ninja plugin template:

```bash
pf plugin-create-binja name=my_analyzer output_dir=./plugins
```

Install plugin:

```bash
pf plugin-binja-install plugin=./plugins/my_analyzer.py
```

## Workflows

### Complete Driver Analysis

```bash
# 1. Discover IOCTLs
pf ioctl-discover binary=/path/to/driver.ko

# 2. Security check
pf vuln-kernel-check module=/path/to/driver.ko

# 3. Analyze structure
pf ioctl-analyze binary=/path/to/driver.ko

# 4. Fuzz IOCTLs (if driver loaded)
pf ioctl-fuzz driver=/dev/mydriver iterations=10000
```

### Firmware Security Audit

```bash
# 1. Analyze firmware
pf firmware-analyze image=firmware.bin

# 2. Extract filesystem
pf firmware-extract image=firmware.bin

# 3. Scan extracted binaries
for binary in firmware_extracted/_*.extracted/bin/*; do
    pf vuln-scan binary=$binary
done
```

### Binary Reversing Workflow

```bash
# 1. Initial analysis with radare2
pf reverse-radare2 binary=/path/to/binary

# 2. Find vulnerabilities
pf vuln-scan binary=/path/to/binary

# 3. Generate CFG
pf reverse-control-flow binary=/path/to/binary

# 4. Debug with LLDB
pf reverse-lldb binary=/path/to/binary

# 5. Fuzz for crashes
pf fuzz-basic binary=/path/to/binary iterations=10000
```

## Platform-Specific Notes

### Linux

All features fully supported on Linux with:
- Ubuntu 20.04+ (recommended)
- Debian 11+
- Fedora 35+
- Arch Linux

Required packages:
```bash
sudo apt-get install lldb radare2 binwalk flashrom gdb strace
```

### macOS

Supported with limitations:
- LLDB fully supported
- radare2 fully supported
- flashrom may have limited hardware support
- Some kernel fuzzing features unavailable

Install via Homebrew:
```bash
brew install lldb radare2 binwalk
```

### Windows (WSL)

Use Windows Subsystem for Linux (WSL2) for full support.

## Security Considerations

**Warning**: These tools are powerful and can:
- Crash systems
- Corrupt data
- Brick devices (firmware flashing)
- Expose security vulnerabilities

**Best Practices**:
1. Always test on non-production systems
2. Use virtual machines when possible
3. Back up before flashing firmware
4. Verify firmware compatibility
5. Understand legal implications of security research
6. Follow responsible disclosure practices

## Troubleshooting

### LLDB Issues

**Problem**: LLDB not found
```bash
sudo apt-get install lldb
# or
brew install lldb
```

**Problem**: Breakpoints not hitting
- Ensure binary has debug symbols (`-g` flag)
- Check if binary is stripped: `file binary`

### Radare2 Issues

**Problem**: r2pipe import error
```bash
pip3 install --user r2pipe
```

**Problem**: Analysis hangs
- Use timeout in scripts
- Try simpler analysis commands first

### Firmware Issues

**Problem**: Flashrom can't detect chip
- Check hardware connections
- Verify chip model
- Try different programmer: `-p ch341a_spi`

**Problem**: Binwalk extraction fails
- Firmware may be encrypted
- Try manual extraction based on `binwalk -e` output

### Fuzzing Issues

**Problem**: No crashes found
- Increase iterations
- Try different input strategies
- Check if binary has protections (ASLR, canaries)

**Problem**: Fuzzer too slow
- Use parallel fuzzing
- Deploy to microVM swarm
- Optimize timeout value

## Advanced Topics

### Custom IOCTL Definitions

Create custom IOCTL definitions for fuzzing:

```python
# custom_ioctls.json
{
  "ioctls": [
    {"code": "0x8001", "name": "IOCTL_CUSTOM_CMD1"},
    {"code": "0x8002", "name": "IOCTL_CUSTOM_CMD2"}
  ]
}
```

### Writing LLDB Scripts

Create advanced LLDB automation scripts:

```lldb
# advanced.lldb
target create /path/to/binary

# Breakpoint with Python callback
break set -n malloc
break command add -s python
import lldb
frame = lldb.thread.GetSelectedFrame()
size_arg = frame.FindVariable("size")
print(f"malloc({size_arg.GetValue()})")
DONE

run
```

### Creating Syzkaller Descriptions

Define syscall interfaces for Syzkaller:

```text
# my_driver.txt
include <linux/ioctl.h>

ioctl$MYDRIVER(fd fd, cmd const[IOCTL_CMD], arg ptr[in, my_struct])

my_struct {
    field1  int32
    field2  array[int8, 64]
}
```

## References

- [LLDB Documentation](https://lldb.llvm.org/)
- [Radare2 Book](https://book.rada.re/)
- [Ghidra Documentation](https://ghidra-sre.org/)
- [Syzkaller Documentation](https://github.com/google/syzkaller)
- [Flashrom Manual](https://www.flashrom.org/Flashrom)
- [Binwalk Wiki](https://github.com/ReFirmLabs/binwalk/wiki)

## See Also

- [`LLVM-LIFTING.md`](LLVM-LIFTING.md) - Binary lifting guide
- [`../demos/kernel-debugging/README.md`](../demos/kernel-debugging/README.md) - Example workflows
- Main [`README.md`](../README.md) - Project overview

## Getting Help

For debugging help:

```bash
pf debug-help
```

For list of all debugging tasks:

```bash
pf list | grep -E "(ioctl|firmware|reverse|vuln|fuzz|vmkit|plugin)"
```
