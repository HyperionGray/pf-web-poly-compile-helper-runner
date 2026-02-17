# Binary Injection and Shared Library Compilation Guide

This guide covers advanced debugging and binary manipulation capabilities including compiling to shared libraries, injecting code into binaries, and hooking functions at runtime.

## Overview

The binary injection system allows you to:

1. **Compile code to shared libraries** (.so on Linux, .dylib on macOS)
2. **Inject/preload libraries** into running programs
3. **Patch binary dependencies** to use custom libraries
4. **Hook function calls** for debugging and monitoring
5. **Convert WASM to native code** for injection
6. **Inject WASM components** into other WASM modules
7. **Patch binaries at assembly level** for advanced modifications

## Use Cases

- **Debugging**: Intercept and log function calls without modifying source
- **Security Testing**: Test how programs behave with modified libraries
- **Performance Analysis**: Inject profiling code into existing binaries
- **Hot Patching**: Replace library functions without recompiling
- **Reverse Engineering**: Analyze program behavior through hooks
- **Testing**: Inject mock implementations for testing

## Quick Start

### 1. Basic Hook Library Injection

```bash
# Create a hook library template
pf create-hook-lib output=my_hook.c

# Compile it to a shared library
pf compile-c-shared-lib source=my_hook.c output=my_hook.so

# Run your program with the hook
pf inject-shared-lib binary=./my_program lib=my_hook.so
```

### 2. Complete Workflow Demo

```bash
# Run the automated demonstration
pf demo-injection-workflow

# This will:
# - Create a hook library
# - Compile it
# - Create a test program
# - Run it with the hook injected
```

### 3. Install Required Tools

```bash
# Install all tools needed for injection
pf install-injection-tools
```

## Shared Library Compilation

### Compile C to Shared Library

```bash
pf compile-c-shared-lib source=mycode.c output=libmycode.so
```

Options:
- `source` (required): Path to C source file
- `output` (optional): Output library path (default: lib.so or lib.dylib)

### Compile C++ to Shared Library

```bash
pf compile-cpp-shared-lib source=mycode.cpp output=libmycode.so
```

### Compile Rust to Shared Library

```bash
# Your Cargo.toml should have:
# [lib]
# crate-type = ["cdylib"]

pf compile-rust-shared-lib crate=./my-rust-crate
```

### Compile Fortran to Shared Library

```bash
pf compile-fortran-shared-lib source=mycode.f90 output=libmycode.so
```

## Binary Injection Methods

### Method 1: Library Preloading (LD_PRELOAD)

**Best for**: Runtime function hooking without binary modification

```bash
# Inject a library when running a program
pf inject-shared-lib binary=./target_program lib=./hook.so args="program arguments"
```

This uses:
- `LD_PRELOAD` on Linux
- `DYLD_INSERT_LIBRARIES` on macOS

**How it works:**
- The hook library is loaded before the program starts
- Functions in the hook library override functions from other libraries
- Original functions can still be called via `dlsym(RTLD_NEXT, "function_name")`

### Method 2: Binary Dependency Patching

**Best for**: Permanent replacement of library dependencies

```bash
# Inspect current dependencies
pf inspect-binary-deps binary=./my_program

# Replace a library dependency
pf patch-binary-deps binary=./my_program old_lib=libold.so new_lib=/path/to/libnew.so
```

This uses:
- `patchelf` on Linux
- `install_name_tool` on macOS

**Note**: This modifies the binary's ELF/Mach-O headers permanently.

### Method 3: Assembly-Level Patching

**Best for**: Precise code modifications at specific addresses

```bash
# Disassemble to find injection points
pf disassemble-for-injection binary=./my_program section=.text

# Apply assembly patch at specific offset
pf inject-asm-patch binary=./my_program patch=my_patch.asm offset=0x1234
```

**Warning**: This is advanced and can easily corrupt binaries. Always backup!

## Creating Hook Libraries

### Example: Function Interception Hook

```bash
# Generate hook template
pf create-hook-lib output=my_hooks.c
```

The generated template shows how to hook malloc/free. Modify it to hook your target functions:

```c
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>

// Hook any function - example with read()
ssize_t read(int fd, void *buf, size_t count) {
    static ssize_t (*real_read)(int, void*, size_t) = NULL;
    if (!real_read) {
        real_read = dlsym(RTLD_NEXT, "read");
    }
    
    fprintf(stderr, "[HOOK] read(fd=%d, count=%zu)\n", fd, count);
    ssize_t result = real_read(fd, buf, count);
    fprintf(stderr, "[HOOK] read returned %zd\n", result);
    return result;
}
```

Compile and use:
```bash
pf compile-c-shared-lib source=my_hooks.c output=my_hooks.so
pf inject-shared-lib binary=/usr/bin/cat lib=my_hooks.so args="test.txt"
```

## WebAssembly Injection

### Convert WASM to Native Library

```bash
# Convert WASM module to native shared library
pf wasm-to-native input=module.wasm output=module.so
```

This uses `wasm2c` from WABT to convert WASM to C, then compiles to native.

### Inject WASM Component into WASM Module

```bash
# Combine WASM modules
pf inject-wasm-component host=main.wasm component=plugin.wasm output=combined.wasm
```

Requires Binaryen's `wasm-merge` tool.

### Create WASM Hook Module

```bash
# Generate WASM hook template
pf create-wasm-hook output=hook.wat

# Compile to WASM
wat2wasm hook.wat -o hook.wasm
```

## Language-Specific Examples

### Rust Example

**1. Create Rust hook library:**

```rust
// src/lib.rs
use std::os::raw::{c_void, c_int};

#[no_mangle]
pub extern "C" fn my_hook_function(value: c_int) -> c_int {
    eprintln!("[RUST HOOK] Called with: {}", value);
    value + 1
}

// To hook existing C functions, use libc:
extern "C" {
    fn malloc(size: usize) -> *mut c_void;
}

#[no_mangle]
pub extern "C" fn malloc(size: usize) -> *mut c_void {
    eprintln!("[RUST HOOK] malloc({})", size);
    unsafe { malloc(size) }
}
```

**2. Cargo.toml:**
```toml
[lib]
crate-type = ["cdylib"]
```

**3. Compile and inject:**
```bash
pf compile-rust-shared-lib crate=./my-hook-crate
pf inject-shared-lib binary=./target lib=./my-hook-crate/target/release/libmy_hook_crate.so
```

### C Example with Complex Hooks

```c
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>

// Hook strcmp to log all string comparisons
int strcmp(const char *s1, const char *s2) {
    static int (*real_strcmp)(const char*, const char*) = NULL;
    if (!real_strcmp) {
        real_strcmp = dlsym(RTLD_NEXT, "strcmp");
    }
    
    int result = real_strcmp(s1, s2);
    fprintf(stderr, "[HOOK] strcmp(\"%s\", \"%s\") = %d\n", s1, s2, result);
    return result;
}

// Hook fopen to log file operations
FILE *fopen(const char *path, const char *mode) {
    static FILE* (*real_fopen)(const char*, const char*) = NULL;
    if (!real_fopen) {
        real_fopen = dlsym(RTLD_NEXT, "fopen");
    }
    
    FILE *result = real_fopen(path, mode);
    fprintf(stderr, "[HOOK] fopen(\"%s\", \"%s\") = %p\n", path, mode, result);
    return result;
}
```

### Fortran Example

```fortran
! hook.f90
module hook_functions
  use iso_c_binding
  implicit none
  
contains
  
  ! Hook function callable from C
  function fortran_hook(x) bind(c, name="fortran_hook") result(y)
    integer(c_int), value :: x
    integer(c_int) :: y
    
    print *, '[FORTRAN HOOK] Called with:', x
    y = x * 2
  end function fortran_hook
  
end module hook_functions
```

Compile:
```bash
pf compile-fortran-shared-lib source=hook.f90 output=hook.so
```

## Advanced Use Cases

### Case 1: Debugging Memory Issues

```bash
# Create malloc/free hook
cat > mem_debug.c << 'EOF'
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <execinfo.h>

void* malloc(size_t size) {
    static void* (*real_malloc)(size_t) = NULL;
    if (!real_malloc) real_malloc = dlsym(RTLD_NEXT, "malloc");
    
    void* ptr = real_malloc(size);
    
    // Print backtrace
    void *array[10];
    size_t size_bt = backtrace(array, 10);
    fprintf(stderr, "[MEM] malloc(%zu) = %p\n", size, ptr);
    backtrace_symbols_fd(array, size_bt, 2);
    
    return ptr;
}
EOF

# Compile and use
pf compile-c-shared-lib source=mem_debug.c output=mem_debug.so
pf inject-shared-lib binary=./my_buggy_program lib=mem_debug.so
```

### Case 2: Performance Profiling

```bash
# Hook expensive functions to measure time
cat > profiler.c << 'EOF'
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <time.h>

double expensive_calculation(double x) {
    static double (*real_calc)(double) = NULL;
    if (!real_calc) real_calc = dlsym(RTLD_NEXT, "expensive_calculation");
    
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    double result = real_calc(x);
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    double elapsed = (end.tv_sec - start.tv_sec) + 
                     (end.tv_nsec - start.tv_nsec) / 1e9;
    
    fprintf(stderr, "[PROF] expensive_calculation took %.6f seconds\n", elapsed);
    return result;
}
EOF

pf compile-c-shared-lib source=profiler.c output=profiler.so
```

### Case 3: Security Testing - Input Fuzzing

```bash
# Hook read() to inject fuzzed data
cat > fuzzer.c << 'EOF'
#define _GNU_SOURCE
#include <dlfcn.h>
#include <string.h>
#include <stdlib.h>

ssize_t read(int fd, void *buf, size_t count) {
    static ssize_t (*real_read)(int, void*, size_t) = NULL;
    if (!real_read) real_read = dlsym(RTLD_NEXT, "read");
    
    ssize_t result = real_read(fd, buf, count);
    
    // Fuzz the data (flip random bits)
    if (result > 0 && rand() % 10 == 0) {
        unsigned char *bytes = buf;
        for (int i = 0; i < result; i++) {
            if (rand() % 100 < 5) {  // 5% chance to flip
                bytes[i] ^= 1 << (rand() % 8);
            }
        }
        fprintf(stderr, "[FUZZ] Modified read data\n");
    }
    
    return result;
}
EOF

pf compile-c-shared-lib source=fuzzer.c output=fuzzer.so
```

### Case 4: Network Traffic Inspection

```bash
# Hook network functions
cat > netspy.c << 'EOF'
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

int connect(int sockfd, const struct sockaddr *addr, socklen_t addrlen) {
    static int (*real_connect)(int, const struct sockaddr*, socklen_t) = NULL;
    if (!real_connect) real_connect = dlsym(RTLD_NEXT, "connect");
    
    // Log connection attempt
    if (addr->sa_family == AF_INET) {
        struct sockaddr_in *addr_in = (struct sockaddr_in *)addr;
        fprintf(stderr, "[NET] Connecting to %s:%d\n",
                inet_ntoa(addr_in->sin_addr),
                ntohs(addr_in->sin_port));
    }
    
    return real_connect(sockfd, addr, addrlen);
}

ssize_t send(int sockfd, const void *buf, size_t len, int flags) {
    static ssize_t (*real_send)(int, const void*, size_t, int) = NULL;
    if (!real_send) real_send = dlsym(RTLD_NEXT, "send");
    
    fprintf(stderr, "[NET] Sending %zu bytes\n", len);
    return real_send(sockfd, buf, len, flags);
}
EOF

pf compile-c-shared-lib source=netspy.c output=netspy.so
```

## Platform-Specific Notes

### Linux

- Uses `LD_PRELOAD` for library injection
- Uses `patchelf` for binary patching
- Shared libraries use `.so` extension
- Libraries placed in `/usr/lib` or `/usr/local/lib`

### macOS

- Uses `DYLD_INSERT_LIBRARIES` for library injection
- Uses `install_name_tool` for binary patching
- Shared libraries use `.dylib` extension
- System Integrity Protection (SIP) may block injection on system binaries
- Disable SIP for testing: `csrutil disable` (in Recovery Mode)

### Cross-Platform Code

```c
// Portable library preload detection
#ifdef __APPLE__
    #include <mach-o/dyld.h>
#else
    #include <link.h>
#endif

// Portable shared library export
#ifdef _WIN32
    #define EXPORT __declspec(dllexport)
#else
    #define EXPORT __attribute__((visibility("default")))
#endif
```

## Security Considerations

⚠️ **Important Security Notes:**

1. **Only inject into your own binaries** - Injecting into system binaries or applications you don't own may violate terms of service or laws
2. **Code signing** - Signed binaries may reject injection or require re-signing
3. **System Integrity Protection** - Modern OS protections may block injection
4. **Testing only** - Use injection for development/testing, not production
5. **Backup binaries** - Always backup before patching
6. **Malware scanners** - Some tools may be flagged as suspicious

## Troubleshooting

### Library Not Found

```bash
# Check library dependencies
pf inspect-binary-deps binary=./my_program

# Set library path
export LD_LIBRARY_PATH=/path/to/libs:$LD_LIBRARY_PATH
```

### Symbol Not Found

```bash
# Check exported symbols
nm -D mylib.so | grep my_function

# For C++, use c++filt to demangle
nm -D mylib.so | c++filt
```

### Injection Doesn't Work

```bash
# Verify library is being loaded
LD_DEBUG=libs ./my_program

# Check for conflicts
ldd ./my_program
```

### Segmentation Faults

- Ensure correct calling conventions (use `extern "C"` in C++)
- Check function signatures match exactly
- Verify dlsym returns non-NULL
- Use debugger: `LD_PRELOAD=./hook.so gdb ./program`

### macOS SIP Issues

```bash
# Check SIP status
csrutil status

# Disable SIP (Recovery Mode):
# 1. Reboot to Recovery (Cmd+R)
# 2. Terminal → csrutil disable
# 3. Reboot

# Or use with SIP enabled by disabling library validation
codesign --force --deep --sign - ./my_program
```

## Command Reference

### Compilation Commands

| Command | Description |
|---------|-------------|
| `pf compile-c-shared-lib` | Compile C to shared library |
| `pf compile-cpp-shared-lib` | Compile C++ to shared library |
| `pf compile-rust-shared-lib` | Compile Rust to shared library |
| `pf compile-fortran-shared-lib` | Compile Fortran to shared library |
| `pf wasm-to-native` | Convert WASM to native library |

### Injection Commands

| Command | Description |
|---------|-------------|
| `pf inject-shared-lib` | Preload library into program |
| `pf patch-binary-deps` | Patch binary dependencies |
| `pf inspect-binary-deps` | Show binary dependencies |
| `pf inject-wasm-component` | Inject WASM into WASM |
| `pf inject-asm-patch` | Patch binary with assembly |

### Utility Commands

| Command | Description |
|---------|-------------|
| `pf create-hook-lib` | Generate hook template |
| `pf create-wasm-hook` | Generate WASM hook template |
| `pf disassemble-for-injection` | Disassemble for analysis |
| `pf demo-injection-workflow` | Run demo workflow |
| `pf demo-wasm-injection` | Run WASM demo |
| `pf install-injection-tools` | Install required tools |
| `pf injection-help` | Show help |

## Further Reading

- [ELF Format Specification](https://refspecs.linuxfoundation.org/elf/elf.pdf)
- [LD_PRELOAD Tricks](http://www.goldsborough.me/c/low-level/kernel/2016/08/29/16-48-53-the_-ld_preload-_trick/)
- [Dynamic Linking](https://tldp.org/HOWTO/Program-Library-HOWTO/dl-libraries.html)
- [Mach-O File Format](https://developer.apple.com/library/archive/documentation/Performance/Conceptual/CodeFootprint/Articles/MachOOverview.html)
- [Binary Patching with patchelf](https://github.com/NixOS/patchelf)
- [WebAssembly Component Model](https://github.com/WebAssembly/component-model)

## See Also

- `docs/LLVM-LIFTING.md` - Binary lifting to LLVM IR
- `pf-runner/BUILD-HELPERS.md` - Build system integration
- `README.md` - Main project documentation
