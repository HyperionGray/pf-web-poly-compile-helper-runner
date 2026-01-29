#!/bin/bash
# Quick reference script for binary injection operations

cat << 'EOF'
╔════════════════════════════════════════════════════════════════╗
║              Binary Injection Quick Reference                  ║
╚════════════════════════════════════════════════════════════════╝

INSTALLATION
────────────────────────────────────────────────────────────────
  pf install-injection-tools    Install all injection tools
  
PAYLOAD CREATION
────────────────────────────────────────────────────────────────
  # Create injectable shared libraries from source code
  pf create-injection-payload-rust source=./rust-project
  pf create-injection-payload-c source=payload.c output=payload.so
  pf create-injection-payload-fortran source=payload.f90 output=payload.so
  pf create-injection-payload-llvm source=payload.ll output=payload.so
  pf create-injection-payload-wasm-native source=payload.wasm output=payload.so

BINARY ANALYSIS
────────────────────────────────────────────────────────────────
  # Analyze target binaries for injection opportunities
  pf analyze-injection-target binary=./target-program
  pf find-injection-points binary=./target-program

STATIC INJECTION (Binary Patching)
────────────────────────────────────────────────────────────────
  # Modify binaries to load injection libraries
  pf inject-static-library binary=./target payload=./payload.so
  pf inject-constructor binary=./target payload=./payload.so

DYNAMIC INJECTION (Runtime)
────────────────────────────────────────────────────────────────
  # Inject into running processes
  pf inject-runtime-library pid=1234 payload=./payload.so
  pf inject-preload binary=./target payload=./payload.so

CROSS-PLATFORM INJECTION
────────────────────────────────────────────────────────────────
  # macOS dylib injection
  pf inject-macos-dylib binary=./target payload=./payload.dylib

END-TO-END WORKFLOWS
────────────────────────────────────────────────────────────────
  # Complete injection workflows
  pf inject-rust-into-binary rust_source=./src target_binary=./app
  pf inject-c-into-binary c_source=payload.c target_binary=./app
  pf inject-wasm-into-binary wasm_source=payload.wasm target_binary=./app

TESTING & VALIDATION
────────────────────────────────────────────────────────────────
  pf test-injection-workflow    Test complete injection pipeline
  pf clean-injection-artifacts  Clean build artifacts

MANUAL INJECTION COMMANDS
────────────────────────────────────────────────────────────────
  # Direct tool usage
  python3 tools/injection/patch-binary.py ./target ./payload.so
  python3 tools/injection/add-constructor.py ./target ./payload.so
  python3 tools/injection/runtime-inject.py 1234 ./payload.so

PAYLOAD TEMPLATES
────────────────────────────────────────────────────────────────
  # C constructor template
  cat tools/injection/templates/constructor.c
  
  # Rust constructor template  
  cat tools/injection/templates/constructor.rs
  
  # Fortran constructor template
  cat tools/injection/templates/constructor.f90

COMMON INJECTION PATTERNS
────────────────────────────────────────────────────────────────
  Example 1: Simple C Injection
    echo 'void __attribute__((constructor)) init() { printf("Injected!\\n"); }' > payload.c
    pf create-injection-payload-c source=payload.c output=simple.so
    pf inject-preload binary=./target payload=injection/payloads/c/simple.so

  Example 2: Rust Library Injection
    # Create Rust library with constructor
    pf create-injection-payload-rust source=./my-rust-lib
    pf inject-static-library binary=./target payload=injection/payloads/rust/*.so

  Example 3: WASM to Native Injection
    # Convert WASM to native shared library and inject
    pf create-injection-payload-wasm-native source=payload.wasm output=wasm.so
    pf inject-runtime-library pid=$(pidof target) payload=injection/payloads/wasm-native/wasm.so

  Example 4: Cross-Language Workflow
    # Compile Fortran to LLVM IR, then to injectable library
    pf web-build-fortran-llvm
    pf create-injection-payload-llvm source=web/llvm/fortran/hello.ll output=fortran.so
    pf inject-constructor binary=./target payload=injection/payloads/llvm/fortran.so

INJECTION METHODS COMPARISON
────────────────────────────────────────────────────────────────
  LD_PRELOAD:     ⭐⭐⭐⭐⭐ Easy, safe, temporary
  Binary Patch:   ⭐⭐⭐⭐   Permanent, requires file modification
  Constructor:    ⭐⭐⭐⭐   Automatic execution, good compatibility
  Runtime:        ⭐⭐⭐     Advanced, requires privileges
  
SUPPORTED PLATFORMS
────────────────────────────────────────────────────────────────
  Linux:    Full support (.so libraries, ELF binaries)
  macOS:    Partial support (.dylib libraries, Mach-O binaries)
  Windows:  Limited support (.dll libraries, PE binaries)

SECURITY CONSIDERATIONS
────────────────────────────────────────────────────────────────
  - ASLR (Address Space Layout Randomization) may affect injection
  - DEP/NX (Data Execution Prevention) prevents code injection in data segments
  - SELinux/AppArmor may block injection attempts
  - Modern binaries may have additional protections
  - Always test injection on non-production systems first

TROUBLESHOOTING
────────────────────────────────────────────────────────────────
  Q: Injection fails with "Permission denied"
  A: Try running as root or check file permissions and SELinux policies

  Q: Library loads but constructor doesn't execute
  A: Verify constructor function syntax and check library symbols with 'nm -D'

  Q: Runtime injection fails
  A: Ensure target process is accessible and Frida/GDB is installed

  Q: Binary becomes corrupted after patching
  A: Always backup binaries before patching, use LIEF-based tools when possible

  Q: Cross-platform injection doesn't work
  A: Different platforms use different binary formats and injection methods

INTEGRATION WITH EXISTING COMPILATION
────────────────────────────────────────────────────────────────
  # Use existing pf compilation tasks to create injection payloads
  pf web-build-rust-llvm opt_level=2
  pf create-injection-payload-llvm source=web/llvm/rust/lib.ll output=rust-optimized.so
  
  pf web-build-c-wasm
  pf create-injection-payload-wasm-native source=web/wasm/c/c_trap.wasm output=c-wasm.so

DOCUMENTATION
────────────────────────────────────────────────────────────────
  tools/injection/templates/     Injection code templates
  Pfyfile.injection.pf          All injection tasks
  pf injection-help             This help text

For detailed examples and tutorials, see the injection workflow tasks:
  pf list | grep inject

EOF