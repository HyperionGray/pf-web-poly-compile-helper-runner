# Practice Binaries for Debugging, Exploitation, and Fuzzing

A comprehensive collection of deliberately vulnerable binaries for learning security testing, debugging, and exploitation techniques.

## 🎯 Overview

This collection includes practice binaries demonstrating common vulnerability classes:

- **Buffer Overflows** - Stack and heap-based overflows
- **Format String** - Format string vulnerabilities  
- **Heap Exploits** - Use-After-Free and Double-Free
- **Integer Overflow** - Integer arithmetic vulnerabilities
- **Race Conditions** - TOCTOU (Time-of-Check-Time-of-Use)
- **Command Injection** - Shell command injection

## ⚠️ Warning

These binaries contain **intentional security vulnerabilities** for educational purposes only. They are designed for:

- Learning security concepts
- Practicing debugging techniques
- Understanding exploitation methods
- Testing fuzzing tools

**DO NOT:**
- Deploy these in production environments
- Use them on systems with sensitive data
- Run them with elevated privileges unnecessarily
- Expose them to untrusted networks

## 🚀 Quick Start

### Build All Binaries

```bash
# Using pf task runner
pf build-practice-binaries

# Or using make directly
cd demos/practice-binaries
make all
```

### Build Specific Categories

```bash
make buffer-overflow
make format-string
make heap-exploits
make integer-overflow
make race-condition
make command-injection
```

### Clean Build Artifacts

```bash
make clean
```

## 📚 Practice Binaries

### Buffer Overflow

#### stack_overflow
**Path:** `buffer-overflow/stack_overflow`

Classic stack buffer overflow vulnerability.

**Vulnerability:** `strcpy()` without bounds checking allows overwriting return address.

**Usage:**
```bash
./buffer-overflow/stack_overflow "AAAA"
./buffer-overflow/stack_overflow $(python3 -c "print('A'*100)")
```

**Learning Objectives:**
- Understand stack layout
- Identify return address offset
- Craft exploitation payload
- Control program execution flow

**Debugging:**
```bash
gdb ./buffer-overflow/stack_overflow
# Set breakpoint at vulnerable_function
# Examine stack with 'x/20wx $rsp'
# Find offset with pattern_create/pattern_offset
```

#### heap_overflow
**Path:** `buffer-overflow/heap_overflow`

Heap buffer overflow that corrupts heap metadata.

**Vulnerability:** Heap `strcpy()` can overwrite function pointer.

**Usage:**
```bash
./buffer-overflow/heap_overflow "AAAA"
./buffer-overflow/heap_overflow $(python3 -c "print('A'*40 + 'BBBBBBBB')")
```

**Learning Objectives:**
- Understand heap memory layout
- Identify function pointer location
- Overwrite function pointers
- Redirect execution

### Format String

#### format_vuln
**Path:** `format-string/format_vuln`

Format string vulnerability for reading/writing memory.

**Vulnerability:** User input passed directly as format string to `printf()`.

**Usage:**
```bash
# Read stack values
./format-string/format_vuln "%x.%x.%x.%x"
./format-string/format_vuln "%p.%p.%p.%p"

# Read specific address
./format-string/format_vuln "%s"

# Write to memory with %n
./format-string/format_vuln "%1337d%n"
```

**Learning Objectives:**
- Read arbitrary memory
- Leak stack addresses
- Write to arbitrary memory
- Modify authentication flags

### Heap Exploits

#### use_after_free
**Path:** `heap-exploits/use_after_free`

Use-After-Free vulnerability for heap exploitation practice.

**Vulnerability:** Object used after being freed.

**Usage:**
```bash
# Normal flow
./heap-exploits/use_after_free create "DATA"
./heap-exploits/use_after_free delete
./heap-exploits/use_after_free use  # UAF here!

# Exploitation
./heap-exploits/use_after_free create "AAAA"
./heap-exploits/use_after_free delete
./heap-exploits/use_after_free evil "$(python3 -c 'import sys; sys.stdout.buffer.write(b"A"*32 + b"\x41\x42\x43\x44\x45\x46\x47\x48")')"
./heap-exploits/use_after_free use
```

**Learning Objectives:**
- Understand UAF vulnerabilities
- Control freed memory contents
- Hijack function pointers
- Execute arbitrary code

#### double_free
**Path:** `heap-exploits/double_free`

Double-Free vulnerability for heap corruption.

**Vulnerability:** Memory freed twice, corrupting heap metadata.

**Usage:**
```bash
# Create and demonstrate double-free
./heap-exploits/double_free create "AAAA"
./heap-exploits/double_free create "BBBB"
./heap-exploits/double_free free 0
./heap-exploits/double_free free 0  # Double free!

# Edit after free
./heap-exploits/double_free edit 0 "EVIL"
```

**Learning Objectives:**
- Understand double-free bugs
- Exploit heap metadata corruption
- Control heap allocations
- Achieve arbitrary write

### Integer Overflow

#### int_overflow
**Path:** `integer-overflow/int_overflow`

Integer overflow in size calculations.

**Vulnerability:** Integer overflow causes undersized allocations.

**Usage:**
```bash
# Normal allocation
./integer-overflow/int_overflow alloc 10 20

# Overflow: 0x40000000 * 4 = 0 (wraps around)
./integer-overflow/int_overflow alloc 0x40000000 4

# Copy overflow: 0xFFFFFFFF + 1 = 0
./integer-overflow/int_overflow copy 0xFFFFFFFF
```

**Learning Objectives:**
- Understand integer overflow
- Exploit size calculation bugs
- Cause heap corruption
- Trigger crashes and exploits

### Race Condition

#### toctou_race
**Path:** `race-condition/toctou_race`

Time-of-Check-Time-of-Use (TOCTOU) race condition.

**Vulnerability:** Race window between permission check and file access.

**Usage:**
```bash
# Setup test environment
./race-condition/toctou_race setup

# Manual exploitation (two terminals)
# Terminal 1:
./race-condition/toctou_race access

# Terminal 2 (while sleeping):
ln -sf /tmp/secret_file /tmp/race_target

# Automated exploitation
./race-condition/toctou_race exploit
```

**Learning Objectives:**
- Understand TOCTOU vulnerabilities
- Identify race windows
- Exploit race conditions
- Bypass access controls

### Command Injection

#### cmd_injection
**Path:** `command-injection/cmd_injection`

Shell command injection vulnerabilities.

**Vulnerability:** User input concatenated into system() calls.

**Usage:**
```bash
# Setup test file
./command-injection/cmd_injection setup

# Normal usage
./command-injection/cmd_injection ping "localhost"

# Command injection
./command-injection/cmd_injection ping "localhost; ls -la"
./command-injection/cmd_injection ping "localhost && cat /etc/passwd"
./command-injection/cmd_injection ping "localhost | whoami"

# Grep injection
./command-injection/cmd_injection grep "SECRET" "/tmp/test.txt; id"
```

**Learning Objectives:**
- Understand command injection
- Use shell metacharacters
- Chain multiple commands
- Establish reverse shells

## 🐛 Debugging Techniques

### Using GDB

```bash
# Basic debugging
gdb ./buffer-overflow/stack_overflow

# With pwndbg enhancement
gdb -q ./buffer-overflow/stack_overflow
break main
run AAAA
```

### Using LLDB

```bash
# Basic debugging
lldb ./buffer-overflow/stack_overflow

# Set breakpoint and run
b main
run AAAA
```

### Using pf tasks

```bash
# Start interactive debugger
pf debug binary=./buffer-overflow/stack_overflow

# Use specific debugger
pf debug-gdb binary=./buffer-overflow/stack_overflow
pf debug-lldb binary=./buffer-overflow/stack_overflow

# Get binary information
pf debug-info binary=./buffer-overflow/stack_overflow
```

## 🔨 Exploitation Examples

### Stack Buffer Overflow

```bash
# Find offset
gdb ./buffer-overflow/stack_overflow
pattern create 100
run <pattern>
# Note crash address
pattern offset <address>

# Craft exploit
python3 -c "print('A'*72 + '<win_addr>')" | ./buffer-overflow/stack_overflow
```

### Format String

```bash
# Read stack
./format-string/format_vuln "%p.%p.%p.%p.%p.%p.%p.%p"

# Calculate offset to auth_flag
# Use %n to write 1337
./format-string/format_vuln "AAAA%7$n"
```

### Heap Exploitation

```bash
# UAF with controlled allocation
./heap-exploits/use_after_free create "TEST"
./heap-exploits/use_after_free delete
# Allocate with function pointer to secret_handler
./heap-exploits/use_after_free evil "$(python3 exploit.py)"
./heap-exploits/use_after_free use
```

## 🌀 Fuzzing Examples

### AFL++ Fuzzing

```bash
# Compile with AFL instrumentation
afl-gcc -o stack_overflow_fuzz buffer-overflow/stack_overflow.c

# Create input corpus
mkdir input output
echo "AAAA" > input/test1

# Fuzz
afl-fuzz -i input -o output ./stack_overflow_fuzz @@
```

### libFuzzer

```bash
# Compile with libFuzzer
clang -fsanitize=fuzzer,address -o format_fuzz format-string/format_vuln.c

# Fuzz
./format_fuzz
```

### Using pf kernel-fuzz

```bash
# Fast in-memory fuzzing
pf kernel-fuzz-in-memory binary=./buffer-overflow/stack_overflow function=vulnerable_function
```

## 🔍 Analysis Tools

### Static Analysis

```bash
# Check security features
checksec ./buffer-overflow/stack_overflow

# Disassemble
objdump -d ./buffer-overflow/stack_overflow
radare2 ./buffer-overflow/stack_overflow
```

### Dynamic Analysis

```bash
# Run with AddressSanitizer
gcc -fsanitize=address -g buffer-overflow/stack_overflow.c -o stack_overflow_asan
./stack_overflow_asan "AAAA"

# Valgrind
valgrind --leak-check=full ./heap-exploits/use_after_free create TEST
```

### Binary Analysis

```bash
# Using pf tasks
pf binary-info binary=./buffer-overflow/stack_overflow
pf disassemble binary=./buffer-overflow/stack_overflow
pf debug-info binary=./format-string/format_vuln
```

## 📖 Learning Resources

### Recommended Order

1. **Start with Buffer Overflows** - Foundation of exploitation
2. **Format Strings** - Memory read/write primitives
3. **Heap Exploits** - Modern exploitation techniques
4. **Integer Overflows** - Subtle vulnerability class
5. **Race Conditions** - Timing-based attacks
6. **Command Injection** - Application-level attacks

### Practice Workflow

1. **Read the code** - Understand the vulnerability
2. **Debug** - Step through with GDB/LLDB
3. **Analyze** - Identify exploitation primitives
4. **Exploit** - Craft working exploit
5. **Fuzz** - Discover edge cases

### Advanced Challenges

- Bypass ASLR using information leaks
- Exploit with NX enabled
- Chain multiple vulnerabilities
- Write exploits that work reliably
- Develop fuzzing harnesses

## 🛠️ Development

### Adding New Binaries

1. Create source file in appropriate category
2. Add to Makefile
3. Update this README
4. Test thoroughly

### Compilation Options

Binaries are compiled with:
- Debug symbols (`-g`)
- No stack protection (`-fno-stack-protector`)
- Executable stack (`-z execstack`)
- No PIE (`-no-pie`)

These settings make exploitation easier for learning purposes.

## 📝 License

These educational materials are provided for learning purposes only.

## 🤝 Contributing

Contributions welcome! Please:
- Add clear documentation
- Include learning objectives
- Test thoroughly
- Follow existing patterns

## ⚡ Quick Reference

```bash
# Build everything
make all

# Build specific category
make heap-exploits

# Clean
make clean

# Debug a binary
gdb ./buffer-overflow/stack_overflow

# Get info about binary
file ./heap-exploits/use_after_free
checksec ./format-string/format_vuln

# Run with fuzzer
afl-fuzz -i input -o output ./binary @@
```

## 🎓 Educational Use

These binaries are designed for:
- Security training courses
- CTF preparation
- Penetration testing practice
- Vulnerability research
- Exploit development learning

Always use in controlled, isolated environments.
