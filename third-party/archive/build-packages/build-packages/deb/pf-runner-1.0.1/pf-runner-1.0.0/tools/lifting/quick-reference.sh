#!/bin/bash
# Quick reference script for LLVM lifting operations

cat << 'EOF'
╔════════════════════════════════════════════════════════════════╗
║              LLVM Binary Lifting Quick Reference               ║
╚════════════════════════════════════════════════════════════════╝

INSTALLATION
────────────────────────────────────────────────────────────────
  pf install-retdec          Install RetDec (recommended)
  pf install-mcsema          Install McSema + Remill
  pf install-lifting-tools   Install all tools

BUILD EXAMPLES
────────────────────────────────────────────────────────────────
  pf build-lifting-examples  Build demo binaries
  pf clean-lifting-examples  Clean outputs

LIFT BINARIES (RetDec - Easiest)
────────────────────────────────────────────────────────────────
  pf lift-binary-retdec binary=./myprogram
  pf lift-binary-retdec binary=./myprogram output_c=true
  pf lift-examples-retdec

LIFT BINARIES (McSema - Most Accurate)
────────────────────────────────────────────────────────────────
  # Requires CFG extraction with Ghidra/radare2/angr
  pf lift-binary-mcsema binary=./myprogram cfg=./myprogram.cfg

INSPECT & ANALYZE
────────────────────────────────────────────────────────────────
  pf lift-inspect binary=./myprogram
  pf lift-disassemble binary=./myprogram
  pf lift-extract-bitcode binary=./myprogram
  pf analyze-lifted-ir input=./output.ll

OPTIMIZE & RECOMPILE
────────────────────────────────────────────────────────────────
  pf optimize-lifted-ir input=./output.ll opt_level=3
  pf recompile-lifted input=./output.ll

TESTING
────────────────────────────────────────────────────────────────
  pf test-lifting-workflow       Full workflow test
  pf compare-lifting-results     Compare original vs lifted

MANUAL LLVM COMMANDS
────────────────────────────────────────────────────────────────
  # Disassemble bitcode to IR
  llvm-dis program.bc -o program.ll

  # Optimize IR
  opt-18 -S -O3 program.ll -o program_opt.ll

  # Custom optimization passes
  opt-18 -S -passes="mem2reg,instcombine" program.ll -o out.ll

  # Compile IR to binary
  clang program.ll -o program

  # Disassemble binary
  llvm-objdump -d binary_file

  # Analyze IR statistics
  opt-18 -stats program.ll -o /dev/null

WORKFLOW EXAMPLES
────────────────────────────────────────────────────────────────
  Example 1: Basic Lifting
    gcc -O2 myapp.c -o myapp
    pf lift-binary-retdec binary=./myapp
    cat demos/binary-lifting/examples/output/myapp.ll

  Example 2: Lift, Optimize, Recompile
    pf lift-binary-retdec binary=./myapp
    pf optimize-lifted-ir input=./output/myapp.ll opt_level=3
    pf recompile-lifted input=./output/myapp_opt.ll
    ./output/myapp_opt_recompiled

  Example 3: Cross-Architecture
    pf lift-binary-retdec binary=./x86_app
    clang --target=aarch64-linux-gnu output/x86_app.ll -o arm_app

COMMON ISSUES
────────────────────────────────────────────────────────────────
  Q: RetDec takes too long
  A: Large binaries can take 10+ minutes. Be patient or use smaller examples.

  Q: llvm-dis fails on binary
  A: llvm-dis only works on LLVM bitcode. Use RetDec for native binaries.

  Q: Lifted IR won't compile
  A: Some manual fixes may be needed. Check for type mismatches or missing declarations.

  Q: How do I extract CFG for McSema?
  A: Use Ghidra (GUI), radare2 (CLI), or angr (Python) - all free and open-source.

DOCUMENTATION
────────────────────────────────────────────────────────────────
  docs/LLVM-LIFTING.md              Complete guide
  demos/binary-lifting/README.md    Examples & tutorials
  pf lifting-help                   This help text

TOOL COMPARISON
────────────────────────────────────────────────────────────────
  RetDec:  ⭐⭐⭐⭐   Open source, automatic, multi-arch
  McSema:  ⭐⭐⭐⭐⭐ Most accurate, uses Ghidra/radare2/angr
  LLVM:    ⭐⭐⭐     Basic tools, bitcode only

SUPPORTED ARCHITECTURES
────────────────────────────────────────────────────────────────
  RetDec:  x86, x86_64, ARM, MIPS, PowerPC
  McSema:  x86, x86_64, AArch64, SPARC
  LLVM:    All LLVM targets

For detailed documentation, see: docs/LLVM-LIFTING.md
EOF
