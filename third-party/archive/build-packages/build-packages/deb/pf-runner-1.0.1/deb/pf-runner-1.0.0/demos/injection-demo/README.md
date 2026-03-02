# Binary Injection Demonstrations

This directory contains examples demonstrating the binary injection and shared library compilation capabilities of pf-web-poly-compile-helper-runner.

## Quick Start

### Run the Complete Demo

```bash
# Automated demonstration of the full workflow
pf demo-injection-workflow
```

This will:
1. Create a hook library that intercepts `malloc` and `free`
2. Compile it to a shared library
3. Create a simple test program
4. Run the test program with the hook library injected
5. Show how function calls are intercepted and logged

### Run WASM Injection Demo

```bash
# Demonstrate WASM component injection
pf demo-wasm-injection
```

## Examples

### Example 1: Simple Function Hook

**Create the hook:**
```c
// simple_hook.c
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>

int add(int a, int b) {
    static int (*real_add)(int, int) = NULL;
    if (!real_add) {
        real_add = dlsym(RTLD_NEXT, "add");
    }
    
    printf("[HOOK] add(%d, %d) called\n", a, b);
    int result = real_add ? real_add(a, b) : a + b;
    printf("[HOOK] add returned %d\n", result);
    return result;
}
```

**Compile and use:**
```bash
pf compile-c-shared-lib source=simple_hook.c output=simple_hook.so
pf inject-shared-lib binary=./my_program lib=simple_hook.so
```

### Example 2: Memory Tracking Hook

**Create memory tracker:**
```c
// mem_tracker.c
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdatomic.h>

static atomic_size_t total_allocated = 0;
static atomic_size_t total_freed = 0;

void* malloc(size_t size) {
    static void* (*real_malloc)(size_t) = NULL;
    if (!real_malloc) {
        real_malloc = dlsym(RTLD_NEXT, "malloc");
    }
    
    void* ptr = real_malloc(size);
    atomic_fetch_add(&total_allocated, size);
    
    fprintf(stderr, "[MEM] malloc(%zu) = %p (total: %zu bytes)\n", 
            size, ptr, atomic_load(&total_allocated));
    
    return ptr;
}

void free(void* ptr) {
    static void (*real_free)(void*) = NULL;
    if (!real_free) {
        real_free = dlsym(RTLD_NEXT, "free");
    }
    
    fprintf(stderr, "[MEM] free(%p)\n", ptr);
    real_free(ptr);
}

__attribute__((destructor))
void print_stats() {
    fprintf(stderr, "\n[MEM] Total allocated: %zu bytes\n", 
            atomic_load(&total_allocated));
}
```

**Usage:**
```bash
pf compile-c-shared-lib source=mem_tracker.c output=mem_tracker.so
pf inject-shared-lib binary=./my_app lib=mem_tracker.so
```

### Example 3: Rust Hook Library

**Create Rust hook:**
```rust
// lib.rs
use std::os::raw::c_char;
use std::ffi::CStr;

#[no_mangle]
pub extern "C" fn strlen(s: *const c_char) -> usize {
    unsafe {
        let cstr = CStr::from_ptr(s);
        let len = cstr.to_bytes().len();
        eprintln!("[RUST HOOK] strlen called on string of length {}", len);
        len
    }
}

#[no_mangle]
pub extern "C" fn init_hook() {
    eprintln!("[RUST HOOK] Library loaded!");
}

#[cfg(target_os = "linux")]
#[link_section = ".init_array"]
#[used]
static INIT_HOOK: extern "C" fn() = init_hook;
```

**Cargo.toml:**
```toml
[package]
name = "rust-hook"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]
```

**Usage:**
```bash
pf compile-rust-shared-lib crate=./rust-hook
pf inject-shared-lib binary=./target lib=./rust-hook/target/release/librust_hook.so
```

### Example 4: Fortran Hook Library

**Create Fortran hook:**
```fortran
! fortran_hook.f90
module fortran_hooks
  use iso_c_binding
  implicit none
  
contains
  
  function fortran_compute(x, y) bind(c, name="fortran_compute") result(z)
    real(c_double), value :: x, y
    real(c_double) :: z
    
    print *, '[FORTRAN HOOK] Computing:', x, '+', y
    z = x + y
    print *, '[FORTRAN HOOK] Result:', z
  end function fortran_compute
  
end module fortran_hooks
```

**Usage:**
```bash
pf compile-fortran-shared-lib source=fortran_hook.f90 output=fortran_hook.so
pf inject-shared-lib binary=./my_program lib=fortran_hook.so
```

### Example 5: WASM Component Injection

**Base WASM module (base.wat):**
```wat
(module
  (func $original (export "process") (param $x i32) (result i32)
    local.get $x
    i32.const 10
    i32.mul
  )
)
```

**Hook component (hook.wat):**
```wat
(module
  (import "env" "log" (func $log (param i32)))
  
  (func $hooked (export "process") (param $x i32) (result i32)
    ;; Log input
    local.get $x
    call $log
    
    ;; Process
    local.get $x
    i32.const 10
    i32.mul
    
    ;; Log output
    call $log
  )
)
```

**Compile and combine:**
```bash
wat2wasm base.wat -o base.wasm
wat2wasm hook.wat -o hook.wasm
pf inject-wasm-component host=base.wasm component=hook.wasm output=combined.wasm
```

## Practical Use Cases

### Debugging Memory Leaks

```bash
# Create and inject memory leak detector
pf create-hook-lib output=leak_detector.c
# Edit leak_detector.c to track allocations
pf compile-c-shared-lib source=leak_detector.c output=leak_detector.so
pf inject-shared-lib binary=./leaky_program lib=leak_detector.so
```

### Performance Profiling

```bash
# Hook slow functions to measure execution time
cat > profiler.c << 'EOF'
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <time.h>

void expensive_function(void) {
    static void (*real_func)(void) = NULL;
    if (!real_func) {
        real_func = dlsym(RTLD_NEXT, "expensive_function");
    }
    
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    real_func();
    clock_gettime(CLOCK_MONOTONIC, &end);
    
    double elapsed = (end.tv_sec - start.tv_sec) + 
                     (end.tv_nsec - start.tv_nsec) / 1e9;
    fprintf(stderr, "[PROF] Function took %.6f seconds\n", elapsed);
}
EOF

pf compile-c-shared-lib source=profiler.c output=profiler.so
pf inject-shared-lib binary=./my_program lib=profiler.so
```

### Security Testing

```bash
# Inject input fuzzing
cat > fuzzer.c << 'EOF'
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdlib.h>
#include <string.h>

ssize_t read(int fd, void *buf, size_t count) {
    static ssize_t (*real_read)(int, void*, size_t) = NULL;
    if (!real_read) {
        real_read = dlsym(RTLD_NEXT, "read");
    }
    
    ssize_t result = real_read(fd, buf, count);
    
    // Randomly corrupt data for fuzzing
    if (result > 0 && rand() % 10 == 0) {
        unsigned char *bytes = buf;
        bytes[rand() % result] ^= 0xFF;
    }
    
    return result;
}
EOF

pf compile-c-shared-lib source=fuzzer.c output=fuzzer.so
pf inject-shared-lib binary=./target_program lib=fuzzer.so
```

## Platform Notes

### Linux
- Uses `LD_PRELOAD` for injection
- Requires `patchelf` for binary patching
- Shared libraries use `.so` extension

### macOS
- Uses `DYLD_INSERT_LIBRARIES` for injection
- Requires `install_name_tool` for binary patching
- Shared libraries use `.dylib` extension
- System Integrity Protection (SIP) may block injection on system binaries

## Troubleshooting

### Hook Not Working

1. **Verify library is loaded:**
```bash
LD_DEBUG=libs ./my_program
```

2. **Check symbol visibility:**
```bash
nm -D my_hook.so | grep my_function
```

3. **Use correct calling convention:**
```c
// For C
extern "C" {
    void my_function();
}
```

### Segmentation Fault

1. **Verify function signature matches exactly**
2. **Check that dlsym returns non-NULL**
3. **Use a debugger:**
```bash
LD_PRELOAD=./hook.so gdb ./my_program
```

### macOS SIP Issues

Disable library validation on the target binary:
```bash
codesign --force --deep --sign - ./my_program
```

Or disable SIP entirely (not recommended for production):
1. Reboot to Recovery Mode (Cmd+R)
2. Terminal → `csrutil disable`
3. Reboot

## See Also

- [Binary Injection Guide](../../docs/BINARY-INJECTION.md) - Complete documentation
- [LLVM Lifting Guide](../../docs/LLVM-LIFTING.md) - Binary analysis
- Main [README](../../README.md) - Project overview
