# Debugging and Reverse Engineering Module

Advanced debugging support for ELF binaries (C/C++, Rust) with GDB/LLDB and pwndbg integration.

## Overview

This module provides:

1. **Debugger Installation**: Automated setup of GDB, LLDB, and pwndbg
2. **Interactive Debug Shell**: Simplified interface for debugging workflows
3. **Multi-Language Support**: C, C++, and Rust debugging examples
4. **Reverse Engineering Tools**: Binary analysis and disassembly tasks
5. **Practice Examples**: Vulnerable binaries for learning debugging techniques

## Features

### pwndebug - Interactive Debugger Shell

The `pwndebug.py` tool provides a simplified debugging interface:

- **Abstracted Commands**: Common debugging operations work across GDB/LLDB
- **Binary Information**: Quick inspection of ELF files
- **Easy Switching**: Toggle between GDB and LLDB seamlessly
- **pwndbg Integration**: Enhanced GDB experience with exploit development features

### Supported Debuggers

- **GDB** (GNU Debugger): Industry-standard debugger with pwndbg enhancements
- **LLDB**: Modern debugger from the LLVM project, excellent for Rust
- **pwndbg**: GDB plugin with exploit development and reverse engineering features

## Quick Start

### 1. Install Debuggers

```bash
pf install-debuggers
```

This installs:
- GDB and LLDB
- pwndbg (GDB enhancement)
- Required Python dependencies

Verify installation:
```bash
pf check-debuggers
```

### 2. Build Example Binaries

```bash
pf build-debug-examples
```

This creates debug binaries in `demos/debugging/examples/bin/`:
- `vulnerable` - C program with buffer overflow (for practice)
- `debug_cpp` - C++ program with classes and vectors
- `debug_rust` - Rust program with ownership examples

### 3. Start Debugging

#### Interactive Shell
```bash
pf debug binary=demos/debugging/examples/bin/vulnerable
```

In the interactive shell:
- `info` - Show binary information
- `start` - Start debugging with default debugger (GDB)
- `gdb` - Start GDB session
- `lldb` - Start LLDB session
- `help` - Show available commands
- `quit` - Exit shell

#### Direct Debugging
```bash
# Debug with GDB directly
pf debug-gdb binary=demos/debugging/examples/bin/vulnerable

# Debug with LLDB directly
pf debug-lldb binary=demos/debugging/examples/bin/debug_rust

# Show binary info without debugging
pf debug-info binary=demos/debugging/examples/bin/debug_cpp
```

## Usage Examples

### Debugging the C Vulnerable Example

```bash
# Build the example
pf build-debug-examples

# Start interactive debugger
pf debug-example-c

# Or debug directly with GDB
gdb demos/debugging/examples/bin/vulnerable
```

Inside GDB with pwndbg:
```gdb
# Set a breakpoint
break vulnerable_function

# Run with argument
run "test input"

# Examine the stack
stack 20

# Check for security mitigations
checksec

# Disassemble current function
disassemble

# Show registers
info registers

# Continue execution
continue
```

### Debugging C++ Programs

```bash
pf debug-example-cpp
```

Inside GDB:
```gdb
# Set breakpoint on class method
break Player::display

# Run the program
run

# Print C++ objects
print player
print players

# Step through code
next        # Next line (step over)
step        # Step into functions
finish      # Finish current function

# Show backtrace
backtrace
```

### Debugging Rust Programs

```bash
pf debug-example-rust
```

Rust is best debugged with LLDB:
```bash
pf debug-lldb binary=demos/debugging/examples/bin/debug_rust
```

Inside LLDB:
```lldb
# Set breakpoint
breakpoint set -n main

# Run with arguments
run arg1 arg2

# Show variables
frame variable

# Step through
next        # Next line
step        # Step into
finish      # Finish function

# Backtrace
thread backtrace
```

## Reverse Engineering Tasks

### Binary Analysis

```bash
# Show comprehensive binary information
pf binary-info binary=demos/debugging/examples/bin/vulnerable

# Extract strings from binary
pf strings-analysis binary=demos/debugging/examples/bin/vulnerable

# Disassemble binary
pf disassemble binary=demos/debugging/examples/bin/vulnerable
```

### Using pwndebug Tool Directly

The `pwndebug.py` tool can be used independently:

```bash
# Interactive shell
python3 tools/debugging/pwndebug.py <binary> [args...]

# With specific debugger
python3 tools/debugging/pwndebug.py --debugger lldb <binary>

# Direct debugging (skip shell)
python3 tools/debugging/pwndebug.py --direct <binary>

# Just show info
python3 tools/debugging/pwndebug.py --info <binary>
```

## Example Binaries

### vulnerable.c - Buffer Overflow Practice

A deliberately vulnerable C program for learning:
- Buffer overflow exploitation
- Stack analysis
- Return address manipulation
- Function pointer analysis

Built with security features disabled for educational purposes:
- No stack protection (`-fno-stack-protector`)
- Executable stack (`-z execstack`)
- No PIE (`-no-pie`)

### debug_cpp.cpp - C++ Debugging

Demonstrates C++ debugging scenarios:
- Class instances and methods
- STL containers (vectors, strings)
- Smart pointers
- Recursive functions

### debug_rust.rs - Rust Debugging

Shows Rust-specific debugging:
- Ownership and borrowing
- Vector manipulation
- Structs and traits
- Recursive fibonacci

## pwndbg Features

When using GDB with pwndbg, you get enhanced features:

### Memory Analysis
```gdb
vmmap           # Show memory mappings
search <value>  # Search memory for value
hexdump <addr>  # Hexdump at address
telescope <addr> # Recursively dereference pointers
```

### Exploitation Features
```gdb
rop             # ROP gadget finder
ropgadget       # Alternative ROP search
checksec        # Check binary security features
cyclic 100      # Generate cyclic pattern
cyclic -l <val> # Find offset in cyclic pattern
```

### Code Analysis
```gdb
nearpc          # Show assembly near PC
context         # Show full context (regs, code, stack)
pdisass         # Enhanced disassembly
```

## Available pf Commands

### Installation
- `pf install-debuggers` - Install GDB, LLDB, and pwndbg
- `pf check-debuggers` - Verify debugger installation

### Building Examples
- `pf build-debug-examples` - Build all example binaries
- `pf clean-debug-examples` - Clean built binaries

### Interactive Debugging
- `pf debug binary=<path>` - Interactive debugger shell
- `pf debug-gdb binary=<path>` - Direct GDB debugging
- `pf debug-lldb binary=<path>` - Direct LLDB debugging
- `pf debug-info binary=<path>` - Show binary information

### Example Sessions
- `pf debug-example-c` - Debug C vulnerable example
- `pf debug-example-cpp` - Debug C++ example
- `pf debug-example-rust` - Debug Rust example

### Reverse Engineering
- `pf disassemble binary=<path>` - Disassemble binary
- `pf strings-analysis binary=<path>` - Extract strings
- `pf binary-info binary=<path>` - Detailed binary info

### Testing
- `pf test-debugger-workflow` - Test debugging setup
- `pf debug-help` - Show help for all commands

## Integration with LLVM Lifting

This debugging module integrates with the existing LLVM binary lifting features:

```bash
# Lift a binary to LLVM IR
pf lift-binary-retdec binary=demos/debugging/examples/bin/vulnerable

# Debug the lifted LLVM IR
lldb demos/debugging/examples/bin/vulnerable

# Optimize and recompile
pf optimize-lifted-ir input=output/vulnerable.ll
pf recompile-lifted input=output/vulnerable_opt.ll
```

## Security Note

The vulnerable example (`vulnerable.c`) is intentionally insecure for educational purposes:
- Contains buffer overflow vulnerability
- Compiled with security features disabled
- Should only be run in controlled environments
- Never use these patterns in production code

## Troubleshooting

### GDB not finding pwndbg
```bash
# Check if pwndbg is installed
ls -la ~/.pwndbg

# Check .gdbinit
cat ~/.gdbinit

# Reinstall pwndbg
pf install-debuggers
```

### LLDB not working with Rust
```bash
# Install Rust debugging tools
rustup component add lldb-preview

# Use rust-lldb wrapper
rust-lldb demos/debugging/examples/bin/debug_rust
```

### Symbols not found
```bash
# Build with debug symbols
gcc -g -O0 program.c -o program

# For Rust
rustc -g program.rs -o program
```

## References

- [GDB Documentation](https://sourceware.org/gdb/documentation/)
- [LLDB Tutorial](https://lldb.llvm.org/use/tutorial.html)
- [pwndbg Repository](https://github.com/pwndbg/pwndbg)
- [Debugging Rust with LLDB](https://rust-lang.github.io/rustc-dev-guide/debugging-support-in-rustc.html)

## Contributing

To add more debugging examples or features:

1. Add example source files to `demos/debugging/examples/`
2. Update `Pfyfile.debugging.pf` with build tasks
3. Enhance `pwndebug.py` with new features
4. Update this README with documentation

---

**Quick Reference:**
```bash
pf install-debuggers           # Setup
pf build-debug-examples        # Build examples
pf debug binary=<path>         # Debug interactively
pf debug-help                  # Show all commands
```
