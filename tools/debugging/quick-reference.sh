#!/bin/bash
# Quick reference for debugging commands

cat << 'EOF'
=== Debugging and Reverse Engineering Commands ===

Installation:
  pf install-debuggers          - Install GDB, LLDB, and pwndbg
  pf check-debuggers            - Check debugger installation

Building Examples:
  pf build-debug-examples       - Build C/C++/Rust debug examples
  pf clean-debug-examples       - Clean built examples

Interactive Debugging:
  pf debug binary=PATH          - Start interactive debugger shell
  pf debug-gdb binary=PATH      - Debug directly with GDB
  pf debug-lldb binary=PATH     - Debug directly with LLDB
  pf debug-info binary=PATH     - Show binary information

Example Sessions:
  pf debug-example-c            - Debug C vulnerable example
  pf debug-example-cpp          - Debug C++ example
  pf debug-example-rust         - Debug Rust example

Reverse Engineering:
  pf disassemble binary=PATH    - Disassemble binary
  pf strings-analysis binary=PATH - Extract strings
  pf binary-info binary=PATH    - Show detailed info

Testing:
  pf test-debugger-workflow     - Test debugging setup
  pf debug-help                 - Show this help

Examples:
  # Install debuggers
  pf install-debuggers

  # Build example binaries
  pf build-debug-examples

  # Start interactive debugging
  pf debug binary=demos/debugging/examples/bin/vulnerable

  # Debug directly with GDB
  pf debug-gdb binary=demos/debugging/examples/bin/vulnerable

  # Show binary information
  pf debug-info binary=demos/debugging/examples/bin/debug_cpp

  # Disassemble a binary
  pf disassemble binary=demos/debugging/examples/bin/debug_rust

EOF
