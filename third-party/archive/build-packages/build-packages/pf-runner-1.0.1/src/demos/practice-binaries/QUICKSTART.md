# Practice Binaries Quick Start Guide

Get started quickly with practice binaries for debugging, exploitation, and fuzzing!

## 🚀 Quick Start (3 Steps)

### 1. Build All Binaries

```bash
cd demos/practice-binaries
make all
```

This compiles all vulnerable binaries in about 5 seconds.

### 2. Run a Demo

```bash
./demo_command_injection.sh
```

Try any of these demos:
- `./demo_stack_overflow.sh` - Buffer overflow exploitation
- `./demo_format_string.sh` - Format string vulnerabilities
- `./demo_uaf.sh` - Use-after-free exploitation
- `./demo_command_injection.sh` - Command injection attacks
- `./demo_fuzzing.sh` - Fuzzing techniques

### 3. Start Practicing!

```bash
# Try buffer overflow
./buffer-overflow/stack_overflow "AAAA"
./buffer-overflow/stack_overflow $(python3 -c "print('A'*100)")

# Try format string
./format-string/format_vuln "%x.%x.%x.%x"

# Try command injection
./command-injection/cmd_injection ping "localhost; whoami"
```

## 📚 What's Included

### Vulnerability Categories

1. **Buffer Overflow** (`buffer-overflow/`)
   - Stack-based overflow
   - Heap-based overflow

2. **Format String** (`format-string/`)
   - Memory read/write primitives
   - Authentication bypass

3. **Heap Exploits** (`heap-exploits/`)
   - Use-After-Free (UAF)
   - Double-Free

4. **Integer Overflow** (`integer-overflow/`)
   - Size calculation bugs
   - Wrap-around exploits

5. **Race Conditions** (`race-condition/`)
   - TOCTOU (Time-of-Check-Time-of-Use)
   - File access races

6. **Command Injection** (`command-injection/`)
   - Shell metacharacter injection
   - Command chaining

## 🔧 Using pf Task Runner

If you have pf installed:

```bash
# Build all binaries
pf build-practice-binaries

# Run demos
pf demo-stack-overflow
pf demo-format-string
pf demo-command-injection

# Run individual binaries
pf run-stack-overflow input="AAAA"
pf run-format-vuln fmt="%x.%x"

# Fuzz binaries
pf fuzz-stack-overflow
pf fuzz-format-string
```

## 🐛 Debugging Examples

### Using GDB

```bash
# Debug stack overflow
gdb ./buffer-overflow/stack_overflow

# In GDB:
(gdb) break vulnerable_function
(gdb) run AAAA
(gdb) info frame
(gdb) x/20wx $rsp
```

### Using LLDB

```bash
# Debug with LLDB
lldb ./buffer-overflow/stack_overflow

# In LLDB:
(lldb) b vulnerable_function
(lldb) run AAAA
(lldb) frame info
(lldb) memory read -c20 $rsp
```

### Using pf debug

```bash
pf debug binary=./buffer-overflow/stack_overflow
```

## 💣 Exploitation Examples

### Stack Buffer Overflow

```bash
# Find crash point
./buffer-overflow/stack_overflow $(python3 -c "print('A'*100)")

# Debug to find offset
gdb ./buffer-overflow/stack_overflow
(gdb) run $(python3 -c "print('A'*100)")
# Note the crash address
```

### Format String

```bash
# Read stack
./format-string/format_vuln "%p.%p.%p.%p"

# Write to memory
./format-string/format_vuln "%1337d%7\$n"
```

### Command Injection

```bash
# Basic injection
./command-injection/cmd_injection ping "localhost; id"

# Chain commands
./command-injection/cmd_injection ping "localhost && cat /etc/passwd"
```

## 🌀 Fuzzing Examples

### Simple Fuzzing

```bash
# Fuzz with increasing lengths
for len in 10 50 64 80 100 150; do
    ./buffer-overflow/stack_overflow $(python3 -c "print('A'*$len)")
done
```

### AFL++ Fuzzing

```bash
# Install AFL++
sudo apt-get install afl++

# Compile with instrumentation
afl-gcc -o stack_fuzz buffer-overflow/stack_overflow.c

# Create seed corpus
mkdir input output
echo "AAAA" > input/seed1

# Fuzz
afl-fuzz -i input -o output ./stack_fuzz @@
```

### Using pf

```bash
pf fuzz-stack-overflow
pf fuzz-format-string
pf fuzz-cmd-injection
```

## 📖 Learning Path

### Beginner

1. Start with `demo_command_injection.sh`
2. Try `demo_stack_overflow.sh`
3. Experiment with `demo_format_string.sh`

### Intermediate

1. Debug binaries with GDB/LLDB
2. Calculate exact offsets
3. Craft working exploits

### Advanced

1. Try `demo_uaf.sh` for heap exploitation
2. Run `demo_fuzzing.sh` for automated discovery
3. Combine multiple vulnerabilities

## 🛡️ Security Note

⚠️ **Educational Use Only**

These binaries contain intentional vulnerabilities. Use only in:
- Isolated environments
- Virtual machines
- Containers
- Local test systems

Never deploy these on production systems or networks!

## 📝 Next Steps

1. **Read the Full README**: `cat README.md`
2. **Try All Demos**: Run each demo script
3. **Practice Debugging**: Use GDB/LLDB on each binary
4. **Write Exploits**: Create working exploit scripts
5. **Set Up Fuzzing**: Configure AFL++ or libFuzzer
6. **Study the Code**: Read the vulnerable source files

## 🆘 Getting Help

- **Full Documentation**: `demos/practice-binaries/README.md`
- **pf Tasks Help**: `pf practice-binaries-help`
- **Makefile Help**: `make help`
- **Demo Scripts**: Each `.sh` file is self-documenting

## ⚡ Common Commands

```bash
# Build
make all
make buffer-overflow
make clean

# Run
./buffer-overflow/stack_overflow "test"
./format-string/format_vuln "%x"
./command-injection/cmd_injection setup

# Debug
gdb ./buffer-overflow/stack_overflow
lldb ./format-string/format_vuln
pf debug binary=./heap-exploits/use_after_free

# Info
make info
file ./buffer-overflow/stack_overflow
checksec ./format-string/format_vuln
```

## 🎯 Practice Challenges

Try these challenges:

1. **Buffer Overflow**: Redirect execution to win() function
2. **Format String**: Modify auth_flag to 1337
3. **UAF**: Hijack function pointer to secret_handler
4. **Command Injection**: Spawn a shell
5. **Race Condition**: Read the secret file
6. **Integer Overflow**: Trigger heap corruption

Happy Hacking! 🚀
