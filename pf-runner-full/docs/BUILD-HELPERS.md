# Build Helper Examples - Real World Usage

This directory contains examples demonstrating the build helper verbs.

## Automagic Builder (autobuild)

The `autobuild` verb is the most powerful build helper - it automatically detects your project's build system and runs the appropriate build command.

### Basic Usage

```bash
# Auto-detect and build any project
pf autobuild
```

### With Parameters

```bash
# Release build
pf autobuild release=true

# Custom job count
pf autobuild jobs=8

# Target specific directory
pf autobuild dir=./subproject

# Combined
pf autobuild release=true jobs=16
```

### Detection Priority

When multiple build files exist, `autobuild` uses this priority order:

1. Cargo.toml (Rust) - Highest priority
2. go.mod (Go)
3. package.json (Node.js/npm)
4. setup.py/pyproject.toml (Python)
5. pom.xml (Maven)
6. build.gradle (Gradle)
7. CMakeLists.txt (CMake)
8. meson.build (Meson)
9. justfile (Just)
10. configure (Autotools)
11. Makefile (Make)
12. build.ninja (Ninja) - Lowest priority

This ensures the "source of truth" build system is used (e.g., CMake instead of generated Makefiles).

## Example 1: C Project with Makefile

```bash
cd /tmp/test-build-helpers
pf test.pf build-with-make
```

## Example 2: CMake Project

```bash
cd /tmp/test-cmake
pf test.pf build-cmake
```

## Example 3: Auto-Detection

```bash
cd your-project
pf build-helper-demo  # Shows what build system is detected
pf autobuild          # Automatically builds the project
```

## Example 3a: Automagic Builder in Action

The `autobuild` verb automatically detects and builds projects:

```bash
# Rust project - auto-detects Cargo.toml
cd /path/to/rust-project
pf autobuild

# Node.js project - auto-detects package.json
cd /path/to/node-project  
pf autobuild

# CMake project - auto-detects CMakeLists.txt
cd /path/to/cmake-project
pf autobuild release=true jobs=8

# Go project - auto-detects go.mod
cd /path/to/go-project
pf autobuild

# Python project - auto-detects setup.py or pyproject.toml
cd /path/to/python-project
pf autobuild
```

## Example 4: LLVM IR Generation

```bash
pf c-llvm-demo      # Compile C to LLVM IR
pf cpp-llvm-demo    # Compile C++ to LLVM IR
```

## Example 5: Rust Project

```text
task cargo-release
  describe Build Rust project in release mode
  cargo build release=true
end

task cargo-test
  describe Run Rust tests
  cargo test
end
```

## Example 6: Go Project

```text
task go-build-static
  describe Build static Go binary
  go_build output=myapp ldflags="-s -w" tags=netgo
end
```

## Example 7: Complex Build Pipeline

```text
task full-build
  describe Complete build pipeline with detection
  build_detect
  shell if [ -f Makefile ]; then
  makefile clean all jobs=8
  shell elif [ -f CMakeLists.txt ]; then
  cmake . build_type=Release
  shell elif [ -f Cargo.toml ]; then
  cargo build release=true
  shell fi
end
```

## Example 7a: Simplified Build Pipeline with Autobuild

```text
task smart-build
  describe Use automagic builder for any project
  autobuild release=true jobs=8
end

task monorepo-build
  describe Build all modules in a monorepo
  autobuild dir=./frontend
  autobuild dir=./backend  
  autobuild dir=./shared
end
```

## All Available Build Verbs

- `autobuild [release=true] [jobs=N] [dir=<path>] [target=<target>]` - **Automagic builder** (auto-detect and build)
- `build_detect` - Auto-detect available build systems (detection only, no build)
- `makefile [targets...] [jobs=N] [VAR=value...]` - Run make
- `cmake [source_dir] [build_dir=...] [build_type=...]` - CMake build
- `meson [source_dir] [build_dir=...] [buildtype=...]` - Meson build
- `cargo <subcommand> [release=true] [features=...]` - Rust/Cargo
- `go_build [subcommand=build] [output=...] [tags=...]` - Go build
- `configure [prefix=...] [opt=value...]` - Autotools configure
- `justfile [recipe] [args...]` - Just build
