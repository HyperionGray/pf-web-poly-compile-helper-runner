# Example: Multi-Language Project Build Pipeline

This example demonstrates how to use the build helpers in a real project with multiple languages and build systems.

## Project Structure
```
myproject/
├── c/           # C library with Makefile
├── cpp/         # C++ app with CMake
├── rust/        # Rust crate with Cargo
├── go/          # Go module
└── Pfyfile.pf   # Build orchestration
```

## Complete Pfyfile.pf

```text
task detect-all
  describe Detect all build systems in project
  shell cd c && pf build_detect
  shell cd cpp && pf build_detect  
  shell cd rust && pf build_detect
  shell cd go && pf build_detect
end

task build-c
  describe Build C library
  shell cd c
  makefile clean all jobs=4 CFLAGS=-O3
end

task build-cpp
  describe Build C++ application
  shell cd cpp
  cmake . build_type=Release ENABLE_TESTS=ON
end

task build-rust
  describe Build Rust crate
  shell cd rust
  cargo build release=true
end

task build-go
  describe Build Go module
  shell cd go
  go_build output=../bin/myapp tags=netgo ldflags="-s -w"
end

task build-all
  describe Build entire project
  shell echo "Starting multi-language build..."
  build_detect
  shell cd c && pf build-c
  shell cd cpp && pf build-cpp
  shell cd rust && pf build-rust
  shell cd go && pf build-go
  shell echo "Build complete!"
end

task test-all
  describe Run all tests
  shell cd c && make test
  shell cd cpp && cmake --build build --target test
  shell cd rust && cargo test
  shell cd go && go test ./...
end

task clean-all
  describe Clean all build artifacts
  shell cd c && make clean
  shell cd cpp && rm -rf build
  shell cd rust && cargo clean
  shell cd go && rm -f ../bin/myapp
end

task generate-llvm-ir
  describe Generate LLVM IR for analysis
  shell cd c && pf shell-cli lang=c-llvm code="$(cat src/core.c)"
  shell cd cpp && pf shell-cli lang=cpp-llvm code="$(cat src/main.cpp)"
end

task ci-build
  describe Full CI pipeline
  env MAKEFLAGS=-j8
  clean-all
  build-all
  test-all
end
```

## Usage

### Quick start
```bash
cd myproject
pf build-all
```

### Development workflow
```bash
# Detect what's available
pf detect-all

# Build specific component
pf build-rust

# Run tests
pf test-all

# Clean everything
pf clean-all
```

### CI/CD Integration
```bash
# Complete CI pipeline
pf ci-build
```

### LLVM Analysis
```bash
# Generate IR for inspection
pf generate-llvm-ir
```

## Advanced: Conditional Building

```text
task smart-build
  describe Intelligently build based on what changed
  shell if git diff --name-only HEAD~1 | grep -q '^c/'; then
  build-c
  shell fi
  shell if git diff --name-only HEAD~1 | grep -q '^cpp/'; then
  build-cpp
  shell fi
  shell if git diff --name-only HEAD~1 | grep -q '^rust/'; then
  build-rust
  shell fi
  shell if git diff --name-only HEAD~1 | grep -q '^go/'; then
  build-go
  shell fi
end
```

## Benefits

1. **Unified Interface**: One command syntax for all build systems
2. **Parallel Builds**: `jobs=N` for make, automatic for others
3. **Type Safety**: Build system detection prevents mistakes
4. **LLVM Integration**: Easy IR generation for optimization analysis
5. **Cross-Platform**: Works locally and on remote hosts via SSH
6. **Polyglot**: Seamless integration with polyglot shell features

## Real-World Example: Full Stack Build

```text
task full-stack
  describe Build entire full-stack application
  # Backend (Rust)
  shell cd backend
  cargo build release=true features=api,database
  
  # Frontend (Web + WebAssembly)
  shell cd frontend/wasm
  cargo build --target=wasm32-unknown-unknown release=true
  shell cd ..
  shell npm run build
  
  # Native CLI (Go)
  shell cd cli
  go_build output=../dist/cli tags=netgo
  
  # System services (C)
  shell cd services
  cmake . build_type=Release
  makefile -C build install
  
  shell echo "Full stack build complete!"
end
```
