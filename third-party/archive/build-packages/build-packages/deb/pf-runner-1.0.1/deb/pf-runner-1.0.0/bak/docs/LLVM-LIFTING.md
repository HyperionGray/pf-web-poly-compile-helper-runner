# LLVM Lifting Guide

This guide covers the various approaches to "lifting" - converting compiled binary executables into LLVM Intermediate Representation (IR) for analysis, optimization, and transformation.

## What is LLVM Lifting?

LLVM lifting (also called binary lifting or decompilation to IR) is the process of converting compiled machine code back into LLVM's intermediate representation. This enables:

- **Program Analysis**: Static analysis, vulnerability detection, code auditing
- **Binary Rewriting**: Modify and recompile existing binaries
- **Cross-compilation**: Retarget binaries to different architectures
- **Optimization**: Apply LLVM optimization passes to legacy code
- **Reverse Engineering**: Understand proprietary or legacy software
- **Fuzzing**: Instrument binaries for security testing

## Types of Lifting Supported

### 1. Source-to-LLVM IR (Already Implemented)

The simplest form of "lifting" - compile source code directly to LLVM IR:

```bash
# Rust to LLVM IR
pf web-build-rust-llvm

# C to LLVM IR  
pf web-build-c-llvm

# Fortran to LLVM IR
pf web-build-fortran-llvm

# Build all with custom optimization
pf web-build-all-llvm opt_level=2
```

These tasks use native compiler flags to emit LLVM IR:
- **Rust**: `rustc --emit=llvm-ir`
- **C/C++**: `clang -S -emit-llvm`
- **Fortran**: `lfortran --show-llvm`

### 2. Binary-to-LLVM IR (New in this PR)

True binary lifting - convert compiled executables to LLVM IR:

```bash
# Lift a binary using RetDec
pf lift-binary-retdec binary=./my_program

# Lift using LLVM tools workflow
pf lift-binary-simple binary=./my_program

# Lift with McSema (requires CFG extraction with Ghidra/radare2/angr)
pf lift-binary-mcsema binary=./my_program
```

## Available Lifting Tools

### Tool Comparison

| Tool | Binary→IR | IR→C | Architectures | Dependencies | Reliability |
|------|-----------|------|---------------|--------------|-------------|
| **RetDec** | ✅ | ✅ | x86, x86_64, ARM, MIPS, PowerPC | LLVM, CMake | ⭐⭐⭐⭐ High |
| **McSema** | ✅ | ❌ | x86, x86_64, AArch64, SPARC | Remill, CFG tool (Ghidra/radare2/angr) | ⭐⭐⭐⭐⭐ Very High |
| **Remill** | ✅ (lib) | ❌ | x86, x86_64, AArch64, SPARC | LLVM | ⭐⭐⭐⭐⭐ Very High |
| **LLVM Tools** | Partial | ❌ | All LLVM targets | LLVM only | ⭐⭐⭐ Medium |

### 1. RetDec (Recommended)

**Best for**: Automatic, hands-off binary lifting with minimal setup.

RetDec is an open-source retargetable decompiler that lifts binaries to LLVM IR and can optionally convert to C code.

**Installation:**
```bash
pf install-retdec
```

**Usage:**
```bash
# Basic lifting to LLVM IR
pf lift-binary-retdec binary=./my_program

# Lift to both IR and C
pf lift-binary-retdec binary=./my_program output_c=true

# Specify architecture (if auto-detection fails)
pf lift-binary-retdec binary=./my_program arch=x86_64
```

**Output:**
- `output/my_program.ll` - LLVM IR
- `output/my_program.c` - Decompiled C (if requested)
- `output/my_program.dsm` - Disassembly

**Pros:**
- Fully automatic
- Multi-architecture support
- Open source
- Produces both IR and C

**Cons:**
- IR quality varies by binary complexity
- Large/complex binaries may take time
- Limited symbol recovery for stripped binaries

### 2. McSema + Remill (Most Accurate)

**Best for**: High-fidelity lifting when accuracy is critical.

McSema uses Trail of Bits' Remill library for instruction-level accuracy. Requires CFG (Control Flow Graph) recovery from open-source tools.

**CFG Recovery Options:**
- **Ghidra**: NSA's free tool with GUI and scripting API
- **radare2**: Command-line tool with `agf` graph commands
- **angr**: Python framework with `CFGFast` for static CFG extraction

**Installation:**
```bash
pf install-mcsema
```

**Usage:**
```bash
# Two-step process
# 1. Generate CFG with Ghidra/radare2/angr
# 2. Lift to LLVM IR
pf lift-binary-mcsema binary=./my_program cfg=./my_program.cfg
```

**Pros:**
- Highest accuracy
- Well-maintained
- Good for security research
- Executable bitcode output
- Uses open-source CFG recovery

**Cons:**
- Two-step workflow (CFG extraction, then lifting)
- More complex setup
- Steeper learning curve

### 3. LLVM Native Tools (Simple Approach)

**Best for**: Quick disassembly and bitcode inspection.

Uses built-in LLVM tools for basic lifting operations.

**Available tools:**
- `llvm-dis` - Convert LLVM bitcode to IR
- `llvm-objdump` - Disassemble object files
- `llvm-objcopy` - Convert binary formats

**Usage:**
```bash
# Extract LLVM bitcode if embedded
pf lift-extract-bitcode binary=./my_program

# Disassemble to assembly
pf lift-disassemble binary=./my_program

# Simple binary inspection
pf lift-inspect binary=./my_program
```

**Pros:**
- No extra dependencies
- Fast
- Part of LLVM toolchain

**Cons:**
- Only works with LLVM bitcode or objects
- Can't lift arbitrary native binaries
- Limited functionality

## CFG Extraction Tools (for McSema)

If using McSema for high-fidelity lifting, you'll need to extract a Control Flow Graph (CFG) first. Here are free, open-source alternatives to commercial tools:

### Ghidra (Recommended)

**Best for:** GUI-based analysis with scripting capabilities

```bash
# Install Ghidra (requires Java)
wget https://github.com/NationalSecurityAgency/ghidra/releases/latest
# Extract and run ghidraRun

# Use Ghidra's GUI to:
# 1. Load your binary
# 2. Auto-analyze (Analysis → Auto Analyze)
# 3. Export CFG using scripts or plugins
```

**Features:**
- NSA's free reverse engineering tool
- Excellent GUI and visualization
- Python/Java scripting API
- Large community and plugin ecosystem
- Per-function and whole-program CFG extraction

### radare2

**Best for:** Command-line automation and scripting

```bash
# Install radare2
sudo apt-get install radare2

# Extract CFG
r2 -A your_binary
[0x00000000]> agfd > cfg.dot  # Export to Graphviz format
[0x00000000]> agfj > cfg.json # Export to JSON
```

**Features:**
- Powerful command-line interface
- Multiple export formats (dot, JSON, Mermaid)
- Scriptable with Python/JavaScript
- Fast and lightweight

### angr (Python)

**Best for:** Automated analysis and batch processing

```python
import angr
import networkx as nx

# Load binary
proj = angr.Project('your_binary', auto_load_libs=False)

# Generate CFG
cfg = proj.analyses.CFGFast()

# Export to various formats
nx.write_graphml(cfg.graph, 'cfg.graphml')
# Or convert to McSema format
```

**Features:**
- Pure Python framework
- Static and dynamic CFG generation
- NetworkX graph integration
- Excellent for automation

### Tool Comparison for CFG Extraction

| Tool | GUI | Scripting | Speed | Learning Curve | Export Formats |
|------|-----|-----------|-------|----------------|----------------|
| Ghidra | ✅ | Python/Java | Medium | Medium | Custom, Graphviz, JSON |
| radare2 | ❌ | Python/JS | Fast | Steep | Dot, JSON, Mermaid |
| angr | ❌ | Python | Slow | Medium | NetworkX, GraphML |

**Note:** While these tools can extract CFGs, you may need to write scripts to convert the output to McSema's expected CFG format. RetDec is recommended for users who want a simpler, fully-automated workflow without CFG extraction.

## Practical Examples

### Example 1: Lift and Optimize a Binary

```bash
# Compile a program
gcc -o myapp myapp.c

# Lift to LLVM IR
pf lift-binary-retdec binary=./myapp

# Apply LLVM optimizations
opt-18 -S -O3 output/myapp.ll -o output/myapp_opt.ll

# Recompile with new optimizations
clang output/myapp_opt.ll -o myapp_optimized
```

### Example 2: Cross-Architecture Translation

```bash
# Lift x86_64 binary to IR
pf lift-binary-retdec binary=./x86_app

# Compile IR for ARM
clang --target=aarch64-linux-gnu output/x86_app.ll -o arm_app
```

### Example 3: Security Analysis

```bash
# Lift a binary
pf lift-binary-retdec binary=./suspicious_binary

# Analyze the IR with LLVM passes
opt-18 -analyze -stats output/suspicious_binary.ll

# Check for vulnerabilities
clang -fsanitize=address,undefined output/suspicious_binary.ll -o safe_binary
```

## Demonstration Tasks

The repository includes demonstration tasks:

```bash
# Build example binaries for lifting
pf build-lifting-examples

# Lift all examples with RetDec
pf lift-examples-retdec

# Lift all examples with simple tools
pf lift-examples-simple

# Compare lifting outputs
pf compare-lifting-results
```

## Creating Custom Lifting Tasks

Add to your `Pfyfile.pf`:

```text
task lift-my-binary
  describe Lift my application binary to LLVM IR
  shell_lang bash
  shell retdec-decompiler.py --backend llvmir --no-memory-limit ./bin/myapp -o ./ir/myapp.ll
end

task analyze-lifted
  describe Run analysis passes on lifted IR
  shell_lang bash
  shell opt-18 -S -O3 -print-module-scope ./ir/myapp.ll -o ./ir/myapp_opt.ll
end
```

## Troubleshooting

### RetDec Issues

**Problem:** RetDec fails to detect architecture
```bash
# Solution: Specify manually
pf lift-binary-retdec binary=./myapp arch=x86_64
```

**Problem:** Long processing time
```bash
# RetDec can be slow on large binaries - be patient
# Or try lifting specific sections only
```

### LLVM Tools Issues

**Problem:** `llvm-dis` fails on binary
```bash
# llvm-dis only works with LLVM bitcode
# Use RetDec or McSema for native binaries
```

**Problem:** Missing symbols in lifted IR
```bash
# Stripped binaries lose symbol information
# Use with debug symbols when possible:
gcc -g -o myapp myapp.c
```

## Performance Considerations

- **Small binaries (<1MB)**: Lift in seconds
- **Medium binaries (1-10MB)**: Lift in minutes
- **Large binaries (>10MB)**: May take 10+ minutes
- **Optimization level**: Higher optimization = slower but better IR

## Best Practices

1. **Start with source-to-IR** if you have source code
2. **Use RetDec** for most binary lifting needs
3. **Keep debug symbols** when compiling for better lifting
4. **Validate lifted IR** by recompiling and testing
5. **Use optimization passes** to clean up lifted IR
6. **Compare tools** when accuracy is critical

## References

- [RetDec GitHub](https://github.com/avast/retdec)
- [McSema GitHub](https://github.com/lifting-bits/mcsema)
- [Remill GitHub](https://github.com/lifting-bits/remill)
- [LLVM Command Guide](https://llvm.org/docs/CommandGuide/)
- [Binary Lifting Blog Post](https://adalogics.com/blog/binary-to-llvm-comparison)

## See Also

- `BUILD-HELPERS.md` - Build system integration
- `LANGS.md` - Supported polyglot languages  
- Main `README.md` - Project overview
