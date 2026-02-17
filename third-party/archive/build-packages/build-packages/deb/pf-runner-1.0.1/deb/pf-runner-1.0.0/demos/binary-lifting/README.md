# Binary Lifting Demonstration

This directory contains examples and tools for demonstrating LLVM binary lifting capabilities.

## What's Here

- **examples/** - Sample C programs compiled to native binaries for lifting
- **output/** - Generated LLVM IR from lifted binaries (created by tasks)
- **scripts/** - Helper scripts for lifting workflows

## Quick Start

### 1. Build Example Binaries

```bash
pf build-lifting-examples
```

This creates native executables from the example programs in `examples/`.

### 2. Lift Binaries to LLVM IR

#### Using RetDec (Recommended - Most Reliable)

```bash
# Install RetDec first (if not already installed)
pf install-retdec

# Lift all example binaries
pf lift-examples-retdec

# Or lift a specific binary
pf lift-binary-retdec binary=./examples/bin/simple_math
```

#### Using Simple LLVM Tools

```bash
# Basic inspection and disassembly
pf lift-examples-simple

# Inspect a specific binary
pf lift-inspect binary=./examples/bin/simple_math
```

#### Using McSema (Most Accurate - Requires CFG Extraction)

```bash
# Install McSema
pf install-mcsema

# Extract CFG using Ghidra, radare2, or angr (see CFG Tools section)
# Then lift with McSema (two-step process)
pf lift-binary-mcsema binary=./examples/bin/simple_math cfg=./simple_math.cfg
```

### 3. Analyze and Optimize Lifted IR

```bash
# View the lifted LLVM IR
cat output/simple_math.ll

# Apply optimizations
opt-18 -S -O3 output/simple_math.ll -o output/simple_math_opt.ll

# Recompile the optimized IR
clang output/simple_math_opt.ll -o examples/bin/simple_math_recompiled

# Test the recompiled binary
./examples/bin/simple_math_recompiled
```

## Example Programs

### simple_math.c
Basic arithmetic operations (add, multiply, factorial). Good for testing:
- Function call lifting
- Recursive function handling
- Basic optimization preservation

### string_ops.c
String manipulation (length, reverse). Tests:
- Array/pointer handling
- Loop lifting
- String operations in lifted code

### loop_example.c
Array and loop operations. Demonstrates:
- Loop vectorization potential
- Array access patterns
- Iterative vs recursive approaches

## Lifting Workflow Comparison

### RetDec Workflow (Automatic)
```
Binary → RetDec → LLVM IR (+ optional C code)
       (single tool, fully automatic)
```

**Advantages:**
- One command
- No commercial tools needed
- Produces IR + C
- Multi-architecture

**Best for:** Quick lifting, automatic workflows, open-source requirements

### McSema Workflow (High Accuracy)
```
Binary → Ghidra/radare2/angr → CFG → McSema + Remill → LLVM IR
       (CFG recovery)                (lifting)
```

**Advantages:**
- Highest accuracy
- Better control flow recovery
- Executable bitcode
- Security research features
- Uses free, open-source CFG tools

**Best for:** Critical applications, security analysis, when accuracy matters most

### Simple LLVM Tools (Basic)
```
Binary → llvm-objdump → Assembly
Bitcode → llvm-dis → LLVM IR
```

**Advantages:**
- No installation needed
- Fast
- Part of LLVM

**Best for:** Quick inspection, bitcode files, simple disassembly

## Output Formats

### LLVM IR (.ll)
Human-readable LLVM intermediate representation:
```llvm
define i32 @add(i32 %a, i32 %b) {
entry:
  %add = add nsw i32 %a, %b
  ret i32 %add
}
```

### LLVM Bitcode (.bc)
Binary format of LLVM IR (compile with `llvm-as`):
```bash
llvm-as output/simple_math.ll -o output/simple_math.bc
```

### Decompiled C (.c)
RetDec can produce C code from the lifted IR:
```c
int32_t add(int32_t a1, int32_t a2) {
    return a1 + a2;
}
```

## Optimization Examples

### Apply Standard Optimizations
```bash
opt-18 -S -O3 output/simple_math.ll -o output/simple_math_o3.ll
```

### Custom Pass Pipeline
```bash
opt-18 -S -passes="mem2reg,instcombine,simplifycfg" \
  output/simple_math.ll -o output/simple_math_custom.ll
```

### View Statistics
```bash
opt-18 -stats output/simple_math.ll -o /dev/null 2>&1 | grep "statistics"
```

## Troubleshooting

### Build Failures
```bash
# Ensure you have gcc/clang
which gcc clang

# Install if needed
sudo apt-get install build-essential clang
```

### RetDec Not Found
```bash
# Install RetDec
pf install-retdec

# Or manually:
git clone https://github.com/avast/retdec
cd retdec && mkdir build && cd build
cmake .. && make -j$(nproc)
```

### Lifted IR Won't Compile
Some lifted IR may need manual fixes:
```bash
# Common issues:
# 1. Missing function declarations
# 2. Incorrect type casts
# 3. Platform-specific code

# Solution: Edit the .ll file or use -S flag with clang
clang -S output/problematic.ll
```

### CFG Extraction for McSema

McSema requires a Control Flow Graph (CFG). Here are free, open-source tools:

**Ghidra (Recommended):**
```bash
# Download from https://ghidra-sre.org/
# Load binary, auto-analyze, export CFG using scripts
```

**radare2:**
```bash
# Install: sudo apt-get install radare2
r2 -A your_binary
[0x00000000]> agfd > cfg.dot  # Export CFG to Graphviz
```

**angr (Python):**
```python
import angr
proj = angr.Project('your_binary')
cfg = proj.analyses.CFGFast()
# Convert to McSema format
```

**Alternative:** Use RetDec for fully automatic lifting without CFG extraction.

## Advanced Use Cases

### Cross-Architecture Retargeting
```bash
# Lift x86_64 binary
pf lift-binary-retdec binary=./x86_program

# Compile for ARM
clang --target=aarch64-linux-gnu output/x86_program.ll -o arm_program
```

### Security Hardening
```bash
# Lift binary
pf lift-binary-retdec binary=./vulnerable_app

# Recompile with sanitizers
clang -fsanitize=address,undefined output/vulnerable_app.ll -o safe_app
```

### Performance Analysis
```bash
# Lift and optimize
pf lift-binary-retdec binary=./slow_app
opt-18 -O3 output/slow_app.ll -o output/fast_app.ll
clang output/fast_app.ll -o fast_app

# Compare performance
time ./slow_app
time ./fast_app
```

## References

- [LLVM Lifting Guide](../../docs/LLVM-LIFTING.md) - Complete lifting documentation
- [RetDec Documentation](https://github.com/avast/retdec/wiki)
- [McSema Documentation](https://github.com/lifting-bits/mcsema/blob/master/docs/UsingMcSema.md)
- [LLVM Optimization Passes](https://llvm.org/docs/Passes.html)

## Contributing

To add new lifting examples:

1. Create a new C/C++ source file in `examples/`
2. Add compilation task to `Pfyfile.lifting.pf`
3. Test lifting with multiple tools
4. Document any special requirements

Example task:
```text
task build-my-example
  describe Build my example for lifting
  shell_lang bash
  shell gcc -O2 examples/my_example.c -o examples/bin/my_example
end
```
