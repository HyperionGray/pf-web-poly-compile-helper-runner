# Binary Injection Demos

This directory contains demonstration examples for binary injection capabilities in pf-runner.

## Overview

The binary injection system allows you to:

1. **Compile polyglot code** (Rust, C, Fortran, WASM) into injectable shared libraries
2. **Inject code into existing binaries** using various methods
3. **Execute injected code** at runtime through constructors or function hooks

## Quick Start

### 1. Install Injection Tools

```bash
pf install-injection-tools
```

### 2. Run Basic Test

```bash
pf test-injection-workflow
```

### 3. Try Complete Workflows

```bash
# C injection example
pf inject-c-into-binary c_source=examples/simple-payload.c target_binary=examples/target-app

# Rust injection example  
pf inject-rust-into-binary rust_source=examples/rust-payload target_binary=examples/target-app

# WASM injection example
pf inject-wasm-into-binary wasm_source=examples/payload.wasm target_binary=examples/target-app
```

## Examples

### Example 1: Simple C Constructor Injection

Create a simple payload that prints a message when loaded:

```c
// examples/simple-payload.c
#include <stdio.h>

__attribute__((constructor))
void injected_init() {
    printf("[INJECTED] Hello from injected C code!\n");
}
```

Compile and inject:
```bash
pf create-injection-payload-c source=examples/simple-payload.c output=simple.so
pf inject-preload binary=examples/target-app payload=injection/payloads/c/simple.so
```

### Example 2: Rust Library Injection

Create a Rust library with constructor:

```rust
// examples/rust-payload/src/lib.rs
#[ctor::ctor]
fn injected_init() {
    println!("[INJECTED] Hello from injected Rust code!");
}

#[no_mangle]
pub extern "C" fn injected_function() -> i32 {
    println!("[INJECTED] Rust function called!");
    42
}
```

```toml
# examples/rust-payload/Cargo.toml
[package]
name = "rust-payload"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
ctor = "0.1"
```

Compile and inject:
```bash
pf create-injection-payload-rust source=examples/rust-payload
pf inject-static-library binary=examples/target-app payload=injection/payloads/rust/*.so
```

### Example 3: WASM to Native Injection

Convert existing WASM to injectable native code:

```bash
# Use existing WASM from web demos
pf web-build-rust-wasm
pf create-injection-payload-wasm-native source=demos/pf-web-polyglot-demo-plus-c/web/wasm/rust/pkg/rust_demo.wasm output=rust-wasm.so
pf inject-constructor binary=examples/target-app payload=injection/payloads/wasm-native/rust-wasm.so
```

### Example 4: Cross-Language Integration

Combine multiple languages in a single injection:

```bash
# Compile Fortran to LLVM IR
pf web-build-fortran-llvm opt_level=2

# Create injectable library from LLVM IR
pf create-injection-payload-llvm source=demos/pf-web-polyglot-demo-plus-c/web/llvm/fortran/hello.ll output=fortran-optimized.so

# Inject into target
pf inject-runtime-library pid=$(pidof target-app) payload=injection/payloads/llvm/fortran-optimized.so
```

## Injection Methods

### 1. LD_PRELOAD (Recommended for Testing)

Safest method, doesn't modify the binary:

```bash
pf inject-preload binary=./target payload=./payload.so
```

### 2. Binary Patching (Permanent Modification)

Modifies the binary to load the library:

```bash
pf inject-static-library binary=./target payload=./payload.so
```

### 3. Constructor Injection (Automatic Execution)

Ensures injected code runs at startup:

```bash
pf inject-constructor binary=./target payload=./payload.so
```

### 4. Runtime Injection (Advanced)

Injects into running processes:

```bash
pf inject-runtime-library pid=1234 payload=./payload.so
```

## Platform Support

### Linux (.so libraries)
- Full support for all injection methods
- ELF binary manipulation
- LD_PRELOAD, binary patching, runtime injection

### macOS (.dylib libraries)  
- Partial support
- Mach-O binary manipulation
- DYLD_INSERT_LIBRARIES, install_name_tool

### Windows (.dll libraries)
- Limited support
- PE binary manipulation  
- DLL injection techniques

## Integration with Existing Compilation

The injection system integrates with existing pf-runner compilation tasks:

```bash
# Compile any supported language to LLVM IR
pf web-build-all-llvm opt_level=3

# Convert LLVM IR to injectable libraries
pf create-injection-payload-llvm source=web/llvm/rust/lib.ll output=rust-opt.so
pf create-injection-payload-llvm source=web/llvm/c/c_trap.ll output=c-opt.so
pf create-injection-payload-llvm source=web/llvm/fortran/hello.ll output=fortran-opt.so

# Inject optimized code
pf inject-static-library binary=./target payload=injection/payloads/llvm/rust-opt.so
```

## Security Considerations

- **Test on non-production systems** - injection can destabilize programs
- **Backup binaries** before patching - modifications may be irreversible  
- **Check permissions** - injection may require elevated privileges
- **Verify compatibility** - modern security features may block injection
- **Use appropriate methods** - LD_PRELOAD is safest for testing

## Troubleshooting

### Common Issues

1. **Permission denied during injection**
   - Run as root or check file permissions
   - Disable SELinux/AppArmor temporarily for testing

2. **Library loads but constructor doesn't execute**
   - Verify constructor function syntax
   - Check library symbols: `nm -D payload.so`

3. **Binary becomes corrupted after patching**
   - Always backup before patching
   - Use LIEF-based tools when available

4. **Runtime injection fails**
   - Install Frida: `pip3 install frida-tools`
   - Install GDB: `sudo apt-get install gdb`
   - Check process permissions

### Debugging Tips

```bash
# Check if library is loaded
ldd ./patched-binary | grep payload

# Verify constructor symbols
nm -D ./payload.so | grep constructor

# Test library independently
LD_PRELOAD=./payload.so /bin/true

# Check process maps
cat /proc/PID/maps | grep payload
```

## Advanced Usage

### Custom Injection Scripts

The injection system provides Python scripts for advanced usage:

```bash
# Direct binary patching
python3 tools/injection/patch-binary.py ./target ./payload.so

# Constructor injection
python3 tools/injection/add-constructor.py ./target ./payload.so

# Runtime injection
python3 tools/injection/runtime-inject.py 1234 ./payload.so
```

### Template Customization

Modify injection templates for specific use cases:

```bash
# View available templates
ls tools/injection/templates/

# Customize C template
cp tools/injection/templates/constructor.c my-payload.c
# Edit my-payload.c with your injection code
pf create-injection-payload-c source=my-payload.c output=custom.so
```

## Documentation

- **Quick Reference**: `pf injection-help`
- **Task List**: `pf list | grep inject`
- **Tool Scripts**: `tools/injection/`
- **Templates**: `tools/injection/templates/`

## Examples Directory Structure

```
demos/binary-injection/
├── README.md                    # This file
├── examples/
│   ├── target-app.c            # Simple target application
│   ├── simple-payload.c        # Basic C injection payload
│   ├── rust-payload/           # Rust injection library
│   │   ├── Cargo.toml
│   │   └── src/lib.rs
│   ├── fortran-payload.f90     # Fortran injection code
│   └── payload.wasm            # WebAssembly payload
└── injection/                  # Generated artifacts (created by tasks)
    ├── payloads/               # Compiled injection libraries
    │   ├── c/
    │   ├── rust/
    │   ├── fortran/
    │   ├── llvm/
    │   └── wasm-native/
    └── patched/                # Modified binaries
```

For more examples and detailed tutorials, run the injection workflow tasks and examine the generated artifacts.