# pf-web-poly-compile-helper-runner

A comprehensive polyglot WebAssembly development environment featuring the **pf** task runner (Fabric-based DSL) and multi-language WASM compilation demos.

## Quick Start

**New to pf?** Check out the [**QUICKSTART.md**](QUICKSTART.md) for a comprehensive guide with examples!

The QUICKSTART covers:
- All parameter passing formats (4 different ways!)
- Task definitions with examples
- Environment variables and defaults
- Polyglot shell support
- Build system helpers
- Remote execution
- And much more!

## Overview

This repository provides:

1. **pf-runner**: A lightweight, single-file task runner with a symbol-free DSL for managing development workflows
2. **Polyglot WebAssembly Demo**: A working demonstration of compiling multiple languages (Rust, C, Fortran, WAT) to WebAssembly
3. **WIT Component Support**: WebAssembly Component Model integration with WIT (WebAssembly Interface Types)
4. **End-to-End Testing**: Playwright-based test suite for validating WASM functionality

## Features

### pf Task Runner
- **Symbol-free DSL**: Clean, readable syntax with verbs like `shell`, `packages`, `service`, `directory`, `copy`
- **Polyglot shell support**: Run code inline in 40+ languages (Python, Rust, Go, C, C++, Fortran, Java, and more)
- **Build system helpers**: Native support for Make, CMake, Meson, Cargo, Go, Autotools, and Just
- **Parallel execution**: Run tasks across multiple hosts via SSH
- **Modular configuration**: Split tasks into multiple `.pf` files with `include`
- **Parameter interpolation**: Pass runtime parameters to tasks
- **Command aliases**: Define short command aliases with `[alias name]` syntax for quick access

### pf REST API Server 🌐 (NEW!)
Execute pf tasks remotely via HTTP with automatic API documentation:

```bash
# Start the REST API server (via systemd)
pf rest-on         # or use the alias: pf ron

# Stop the REST API server
pf rest-off        # or use the alias: pf roff

# Start in development mode (foreground with auto-reload)
pf rest-dev        # or use the alias: pf rdev
```

**Features:**
- **Auto-generated docs**: Swagger UI at `/docs` and ReDoc at `/redoc`
- **Task execution**: Run any pf task via HTTP POST
- **Alias routing**: Access tasks via their short aliases (e.g., `/ron` instead of `/pf/rest-on`)
- **Task listing**: Get all available tasks with descriptions
- **Configurable**: Set host, port, and worker count via environment variables

**API Endpoints:**
- `GET /pf/` - List all available tasks
- `GET /pf/{task}` - Get task details
- `POST /pf/{task}` - Execute a task
- `GET /{alias}` - Access task by alias
- `POST /{alias}` - Execute task by alias
- `POST /reload` - Reload tasks from Pfyfile

**Configuration (Environment Variables):**
- `PF_API_HOST` - Bind address (default: 127.0.0.1)
- `PF_API_PORT` - Port number (default: 8000)
- `PF_API_WORKERS` - Number of workers (default: 4)

### Node.js REST API Server 🌐
- **Build Management**: Trigger WebAssembly builds via REST endpoints
- **Real-time Updates**: WebSocket connections for live build status
- **Project Management**: List projects, modules, and build artifacts
- **Status Tracking**: Monitor build progress and retrieve detailed logs
- **Backward Compatibility**: Maintains static file serving for existing web demo
- **Multi-language Support**: API endpoints for Rust, C, Fortran, and WAT builds

### Automagic Builder
The **automagic builder** is an intelligent build system that automatically detects your project type and runs the appropriate build command - no configuration needed! Just run `pf autobuild` and it handles the rest.

**Supported Build Systems:**
- **Rust** (`Cargo.toml`) → `cargo build`
- **Go** (`go.mod`) → `go build`
- **Node.js** (`package.json`) → `npm run build` or `npm install`
- **Python** (`setup.py`, `pyproject.toml`) → `pip install -e .` or `python setup.py build`
- **Java/Maven** (`pom.xml`) → `mvn compile`
- **Java/Gradle** (`build.gradle`, `build.gradle.kts`) → `gradle build`
- **CMake** (`CMakeLists.txt`) → `cmake` + `cmake --build`
- **Meson** (`meson.build`) → `meson setup` + `meson compile`
- **Make** (`Makefile`, `makefile`, `GNUmakefile`) → `make`
- **Just** (`justfile`, `Justfile`) → `just`
- **Autotools** (`configure`, `configure.ac`) → `./configure` + `make`
- **Ninja** (`build.ninja`) → `ninja`

**Smart Detection Features:**
- Prioritizes more specific build systems (e.g., CMake over raw Makefile)
- Handles common directory structures and patterns
- Supports release/debug builds with `release=true` parameter
- Configurable parallel jobs with `jobs=N` parameter
- Can target specific subdirectories with `dir=<path>` parameter

**Quick Examples:**
```bash
# Automatically detect and build any project
pf autobuild

# Build in release mode
pf autobuild release=true

# Use 8 parallel jobs
pf autobuild jobs=8

# Build a subdirectory
pf autobuild dir=./subproject

# Just detect what build system would be used (no build)
pf build_detect
```

### WebAssembly Compilation
- **Rust**: Build WASM modules with wasm-pack
- **C**: Compile to WASM using Emscripten
- **Fortran**: Experimental WASM support via LFortran
- **WAT**: Assemble WebAssembly text format with WABT

### Container Infrastructure 🐳
Run the entire development environment in containers using Podman:
- **Podman Quadlets**: Systemd-integrated container management for production
- **Podman Compose**: Development workflow with podman-compose.yml
- **GPU Support**: Optional GPU-accelerated containers with CUDA
- **Build Containers**: Pre-configured containers for Rust, C, Fortran compilation
- **Debugger Container**: Full debugging suite with GDB, LLDB, pwndbg, radare2
- **Ubuntu 24.04 Base**: All containers based on Ubuntu 24.04 with debugging tools

See [Container Documentation](containers/README.md) for complete guide.

### Binary Injection & Advanced Debugging 🔧
Compile code to shared libraries and inject into binaries for advanced debugging and analysis:
- **Shared Library Compilation**: Build .so/.dylib from C, C++, Rust, Fortran
- **Function Hooking**: Intercept and monitor function calls at runtime
- **Binary Patching**: Replace library dependencies in existing binaries
- **WASM Injection**: Combine and inject WebAssembly components
- **Assembly Patching**: Direct binary modification at machine code level
- **Cross-Language Integration**: Inject code from any supported language into any binary

See [Binary Injection Guide](docs/BINARY-INJECTION.md) for complete documentation.

### LLVM Binary Lifting 🔬
Convert compiled binaries back to LLVM IR for analysis, optimization, and transformation:
- **RetDec**: Automatic binary-to-LLVM lifting for multiple architectures (x86, ARM, MIPS)
- **McSema**: High-fidelity lifting using Remill (uses Ghidra/radare2/angr for CFG recovery)
- **LLVM Tools**: Built-in utilities for bitcode extraction and disassembly
- **Cross-Architecture**: Retarget binaries to different platforms via LLVM IR
- **Optimization**: Apply LLVM optimization passes to legacy/closed-source code
- **Security Analysis**: Instrument and analyze binaries for vulnerabilities

See [LLVM Lifting Guide](docs/LLVM-LIFTING.md) for complete documentation.

### Fuzzing & Sanitizers 🔍
Comprehensive fuzzing and memory safety testing with turnkey integration:
- **🛡️ Sanitizers**: ASan, MSan, UBSan, TSan for detecting memory errors and undefined behavior
- **⚡ libfuzzer**: In-process, coverage-guided fuzzing integrated with LLVM
- **🎯 AFL++**: Advanced fuzzing with LLVM instrumentation for maximum coverage
- **🔬 Binary Lifting + Fuzzing**: Fuzz black-box binaries by lifting to LLVM IR and instrumenting
- **📊 Turnkey Workflows**: Single commands like `pf afl-fuzz` for complete fuzzing campaigns
- **🚀 "Good Luck With That" Achievement**: Successfully instrument lifted binaries with AFL++ (they said it couldn't be done!)

**Quick Start:**
```bash
# Build with sanitizers
pf build-with-asan source=mycode.c
pf build-with-msan source=mycode.c

# libfuzzer
pf generate-libfuzzer-template
pf build-libfuzzer-target source=fuzz_target.c
pf run-libfuzzer target=fuzzer time=60

# AFL++
pf build-afl-target source=target.c
pf afl-fuzz target=target_afl time=1h

# Fuzz black-box binaries!
pf lift-and-instrument-binary binary=/path/to/binary
pf afl-fuzz target=binary_afl_lifted time=30m
```

See [Fuzzing Guide](docs/FUZZING.md) for complete documentation.

### Advanced Kernel Debugging 🛡️
Comprehensive kernel-mode debugging and security analysis capabilities:
- **🎯 Automagic Parse Function Detection**: Automatically identify parse functions in binaries for vulnerability research
- **📊 Complexity Analysis**: Detect functions with many if/else statements, long functions, and high cyclomatic complexity
- **⚡ In-Memory Fuzzing**: Blazing fast fuzzing (100-1000x faster) with loop-back capability and mutation strategies
- **IOCTL Detection**: Automated identification and analysis of IOCTL handlers in kernel modules
- **Firmware Extraction**: Integration with flashrom and other tools for firmware dumping and analysis
- **Advanced Breakpoints**: LLDB integration with complex conditional breakpoints and vulnerability detection
- **High-Performance Fuzzing**: Fast kernel interface fuzzing with parallel execution support
- **MicroVM Swarms**: Scalable fuzzing across multiple lightweight VMs for mass security testing
- **Plugin Ecosystem**: Radare2 and Binary Ninja plugins for enhanced reverse engineering
- **Vulnerability Scanning**: Automated detection of common kernel vulnerabilities and attack patterns
- **Mass Fuzzing Integration**: Syzkaller and KFuzz integration for comprehensive kernel testing

**NEW: Automagic Vulnerability Discovery**
```bash
# Comprehensive analysis in one command
pf kernel-automagic-analysis binary=/path/to/binary

# Detect parse functions automatically
pf kernel-parse-detect binary=/path/to/binary

# Find complex functions (many if/else, long functions)
pf kernel-complexity-analyze binary=/path/to/binary

# Fast in-memory fuzzing with loop-back
pf kernel-fuzz-in-memory binary=/path/to/binary function=parse_input
```

See [Kernel Debugging Guide](docs/KERNEL-DEBUGGING.md) for complete documentation.
See [Automagic Demo](demos/kernel-debugging/AUTOMAGIC-DEMO.md) for hands-on examples.

### Web Application Security Testing 🔒
Comprehensive web application security scanning and fuzzing inspired by Burp Suite and massweb:
- **Automated Vulnerability Detection**: Scan for SQL injection, XSS, CSRF, path traversal, command injection, XXE, SSRF
- **Mass Fuzzing**: High-throughput fuzzing with multiple payload types and anomaly detection
- **Security Headers**: Check for missing or misconfigured security headers
- **Access Control Testing**: Identify broken authentication and authorization issues
- **Multiple Output Formats**: Human-readable console output and JSON for CI/CD integration
- **Extensible Framework**: Easy to add custom vulnerability checks and payloads

**Quick Start:**
```bash
# Run comprehensive security scan
pf security-scan url=http://localhost:8080

# Run specific vulnerability checks
pf security-scan url=http://localhost:8080 checks=sqli,xss

# Fuzz an endpoint with all payloads
pf security-fuzz url=http://localhost:8080/api

# Fuzz with specific payload type
pf security-fuzz url=http://localhost:8080/search type=sqli

# Run complete security test suite
pf security-test-all url=http://localhost:8080
```

**Vulnerability Types Detected:**
- SQL Injection (error-based and blind)
- Cross-Site Scripting (XSS)
- Cross-Site Request Forgery (CSRF)
- Path Traversal / Directory Traversal
- OS Command Injection
- XML External Entity (XXE)
- Server-Side Request Forgery (SSRF)
- Security Misconfigurations
- Missing Security Headers
- Broken Access Control

See [Security Testing Guide](docs/SECURITY-TESTING.md) for complete documentation.

### Binary Injection 💉
Inject compiled polyglot code into existing binaries and shared libraries:
- **Multi-Language Payloads**: Create injectable libraries from Rust, C, Fortran, WASM, or LLVM IR
- **Multiple Injection Methods**: LD_PRELOAD, binary patching, constructor injection, runtime injection
- **Cross-Platform Support**: Linux (.so), macOS (.dylib), Windows (.dll) compatibility
- **Integration with Compilation**: Convert any pf-compiled code into injectable payloads
- **Advanced Techniques**: Function hooking, process memory injection, dynamic library manipulation
- **Security Research**: Tools for binary analysis, reverse engineering, and penetration testing

See [Binary Injection Guide](demos/binary-injection/README.md) for complete documentation.
### Advanced Debugging & Reverse Engineering 🐛
Interactive debugging and reverse engineering for ELF binaries (C/C++/Rust):
- **GDB & LLDB**: Support for both standard debuggers with seamless switching
- **pwndbg Integration**: Enhanced GDB with exploit development and reverse engineering features
- **Interactive Shell**: Simplified debugging interface with abstracted commands
- **Binary Analysis**: Automated disassembly, string extraction, and security feature detection
- **Practice Examples**: Vulnerable binaries for learning debugging and exploitation techniques
- **Multi-Language**: Dedicated support for C, C++, and Rust debugging workflows

See [Debugging Guide](demos/debugging/README.md) for complete documentation.

### ROP (Return-Oriented Programming) Exploit Demo 💥
End-to-end demonstration of exploiting buffer overflow vulnerabilities using ROP:
- **Vulnerable Legacy Service**: Simulated old software with stack-based buffer overflow
- **ROP Chain Generation**: Automated tools to build exploit chains
- **NX Bypass**: Demonstrates bypassing non-executable stack protection
- **Educational Framework**: Complete walkthrough from vulnerability to exploitation
- **Analysis Tools**: Gadget finding, disassembly, and security checking
- **Interactive Testing**: Build, analyze, and test exploits step-by-step

See [ROP Exploit Demo](demos/rop-exploit/README.md) for complete documentation.
### Git Repository Cleanup 🗑️
Interactive tool for removing large files from git history with an intuitive TUI:
- **Interactive TUI**: Beautiful terminal interface with checkbox selection
- **Size Analysis**: Scan and visualize large files across entire git history
- **Smart Filtering**: Set custom size thresholds (100KB - 50MB or custom)
- **Automatic Backup**: Creates git bundle backup before any changes
- **Safe Cleanup**: Uses git-filter-repo for efficient history rewriting
- **Step-by-Step Guidance**: Clear instructions for post-cleanup actions

**Quick Start:**
```bash
# Run interactive cleanup tool
pf git-cleanup

# Or analyze without removing
pf git-analyze-large-files

# Check repository size
pf git-repo-size
```

See [Git Cleanup Guide](docs/GIT-CLEANUP.md) for complete documentation.

### Interactive TUI 🎨
Beautiful text-based user interface for managing tasks and debugging:
- **Task Organization**: Browse tasks by category with rich formatting
- **Interactive Execution**: Run tasks with parameter input
- **Syntax Checking**: Validate task definitions before execution
- **Debugging Tools**: View and manage reverse engineering tools
- **Search Functionality**: Find tasks quickly by name or description

**Quick Start:**
```bash
# Launch the interactive TUI
pf tui

# Install TUI dependencies (if needed)
pf install-tui-deps

# View TUI help
pf tui-help
```

**Features:**
- **11 Task Categories**: Web, Build, Security, Debugging, Kernel, and more
- **178+ Tasks**: Full access to all pf tasks in an organized interface
- **Tool Status**: Check installation status of debugging tools (including Snowman decompiler)
- **Exploit Development**: Integration with pwntools, checksec, ROPgadget
- **Rich Formatting**: Color-coded categories, tables, and progress bars

See [TUI Documentation](docs/TUI.md) for complete guide.

### Package Manager Translation 📦
Translate packages between the 5 most common Linux package formats using a hub-and-spoke model:
- **Supported Formats**: deb (Debian/Ubuntu), rpm (Red Hat/Fedora), flatpak, snap, pacman (Arch)
- **Hub Architecture**: All conversions go through .deb as the hub format
- **Dependency Management**: Proper dependency resolution across formats
- **Batch Conversion**: Convert multiple packages at once
- **Cross-Distro**: Create packages for any distro from any source

**Quick Start:**
```bash
# Check available formats
pf pkg-formats

# Convert RPM to DEB
pf pkg-convert source=package.rpm target=deb

# Convert Flatpak to RPM (via .deb hub)
pf pkg-convert source=app.flatpak target=rpm

# Get package info
pf pkg-info package=myapp.deb

# Show conversion matrix
pf pkg-matrix
```

See [Package Manager Guide](docs/PACKAGE-MANAGER.md) for complete documentation.

### Multi-Distro Container Management 🐧
Use lightweight containers for CentOS, Fedora, Arch, and openSUSE to install and manage packages without polluting your host system:
- **Container Isolation**: Each distro runs in its own lightweight container
- **Artifact Extraction**: Binaries are extracted to host directories using rshared mounts
- **View Modes**: Unified (all distros in one PATH) or isolated (per-distro paths)
- **Efficient**: Containers spin up only when needed, then clean up

**Quick Start:**
```bash
# Install packages from Fedora
pf distro-install-fedora packages="vim htop"

# Install packages from Arch
pf distro-install-arch packages="neovim tree"

# Check status
pf distro-status

# Switch view mode
pf distro-view-unified
```

See [Distro Container Management Guide](docs/DISTRO-CONTAINER-MANAGEMENT.md) for complete documentation.

### OS Switching (Experimental) 🔄
Switch between different Linux distributions using containers and kexec for rebootless kernel switching:
- **MirrorOS Snapshots**: Automatic backups using btrfs/zfs/rsync
- **Container-Based**: Target OS prepared in container, synced to partition
- **kexec Integration**: Rebootless kernel switching for minimal downtime
- **Safety First**: Dry-run mode and automatic backup before switch

**Quick Start:**
```bash
# Check current OS and capabilities
pf os-status

# Create snapshot before changes
pf os-snapshot name=before-upgrade

# Test switching to Fedora (dry run)
pf switch-os target=fedora dry_run=true

# Full switch (requires partition)
pf switch-os target=fedora partition=/dev/sda3
```

⚠️ **Warning**: OS switching is a powerful feature that modifies your system. Always have backups!

See [Distro Container Management Guide](docs/DISTRO-CONTAINER-MANAGEMENT.md) for complete documentation.

### Testing & Development
- **Live dev server**: Static HTTP server with CORS headers for WASM
- **Playwright tests**: Automated browser testing for WASM modules
- **Hot reload**: Development workflow with instant feedback

## Prerequisites

### Minimum Requirements
- Linux (Ubuntu/Debian recommended) or macOS
- Git
- Docker or Podman (for building/running the pf container)

**Note:** The legacy host-based installer now lives in `bak/install-legacy.sh`. The default install path is container-first.

### Optional Prerequisites
The container image already bundles the pf runtime; language toolchains are installed inside the containers defined under `containers/`.

## Installation

### Recommended: Direct Install

The simplest way to get started:

```bash
# Clone the repository
git clone <repository-url>
cd pf-web-poly-compile-helper-runner

# Install to /usr/local/bin (requires sudo)
sudo ./install.sh

# Or install to user directory (no sudo needed)
./install.sh --prefix ~/.local
```

What this does:
1. Installs Python dependencies (fabric, lark)
2. Copies pf-runner library to `/usr/local/lib/pf-runner` (or your prefix)
3. Creates `pf` executable in `/usr/local/bin` (or your prefix/bin)

### Container Install (Alternative)

For containerized workflows or isolated environments:

```bash
# Build container images
./install-container.sh

# Pick a specific runtime/tag (optional)
./install-container.sh --runtime podman --image pf-runner:latest
```

### Using pf Tasks (After Initial Install)

Once pf is installed, you can use these tasks:

```bash
pf install       # Re-run installation
pf install-web   # Alias to install (for web development)
pf install-base  # Alias to install (for compatibility)
```

### What Gets Installed?

**Direct install (./install.sh):**
- `pf` executable in `/usr/local/bin` (or `~/.local/bin`)
- `pf-runner` library in `/usr/local/lib/pf-runner` (or `~/.local/lib/pf-runner`)
- Python dependencies (fabric, lark)

**Container install (./install-container.sh):**
- `pf-base:latest` container image
- `pf-runner:local` container image

## Quick Start

### 1. Install pf-runner

The repository includes a **simple installer script** that sets up everything you need:

#### One-Command Installation (Recommended)

```bash
# System-wide install (requires sudo)
sudo ./install.sh

# User install (no sudo needed)
./install.sh --prefix ~/.local
```

The installer copies pf directly to your system - no containers, no wrappers.

#### Using pf Commands

After initial installation, you can also use pf tasks:

```bash
pf install       # Re-run installation
pf install-web   # Alias to install
pf install-base  # Alias to install
```

#### Legacy Installation (Alternative)

The older host-based installation script is preserved for compatibility:

```bash
./bak/install-legacy.sh  # Legacy host installer
```

#### Manual Installation

For manual control:

```bash
cd pf-runner
pip install --user "fabric>=3.2,<4" "lark>=1.1.0"
make setup          # Creates ./pf symlink
make install-local  # Installs to ~/.local/bin
```

### 2. Verify Installation

Check that pf is available:

```bash
pf --version  # or: ./pf-runner/pf if not installed globally
```

### 3. Run the WebAssembly Demo

#### Build WASM Modules

Build all modules at once:
```bash
pf web-build-all
```

Or build individually:
```bash
pf web-build-rust     # Rust → WASM
pf web-build-c        # C → WASM
pf web-build-wat      # WAT → WASM
pf web-build-fortran  # Fortran → WASM (optional, requires lfortran)
```

Build to specific formats:
```bash
# Build all to WebAssembly
pf web-build-all-wasm

# Build all to asm.js (where supported)
pf web-build-all-asm

# Build all to LLVM IR (where supported, with O3 optimization by default)
pf web-build-all-llvm

# Build with custom optimization level (0, 1, 2, 3, s, or z)
pf web-build-all-llvm opt_level=2

# Build with parallelization support (OpenMP)
pf web-build-c-llvm parallel=true
pf web-build-fortran-llvm parallel=true opt_level=3
```

Individual language compilation targets:
```bash
# Rust
pf web-build-rust-wasm  # Rust → WASM
pf web-build-rust-llvm  # Rust → LLVM IR (with O3 optimization by default)
pf web-build-rust-llvm opt_level=2  # Rust → LLVM IR with O2

# C
pf web-build-c-wasm     # C → WASM
pf web-build-c-asm      # C → asm.js
pf web-build-c-llvm     # C → LLVM IR (with O3 optimization by default)
pf web-build-c-llvm opt_level=s  # C → LLVM IR optimized for size
pf web-build-c-llvm parallel=true  # C → LLVM IR with OpenMP support
pf web-build-c-llvm-opt  # C → LLVM IR with custom optimization passes
pf web-build-c-llvm-opt passes="mem2reg,dce,gvn"  # Custom passes

# Fortran
pf web-build-fortran-wasm  # Fortran → WASM
pf web-build-fortran-llvm  # Fortran → LLVM IR (with O3 optimization by default)
pf web-build-fortran-llvm parallel=true  # Fortran → LLVM IR with OpenMP

# WebAssembly Text
pf web-build-wat-wasm   # WAT → WASM
```

#### Start Development Server

```bash
pf web-dev
```

The server will start on http://localhost:8080 with full REST API support. Open this URL in your browser to see the polyglot WASM demo in action.

**New REST API Features:**
- **Build via API**: Trigger builds using REST endpoints
- **Real-time Status**: WebSocket connections for live build updates
- **Build Management**: Monitor progress and retrieve logs

You can customize the port and directory:
```bash
pf web-dev port=3000 dir=demos/pf-web-polyglot-demo-plus-c/web
```

**API Examples:**
```bash
# Health check
curl http://localhost:8080/api/health

# Trigger Rust build
curl -X POST http://localhost:8080/api/build/rust \
  -H "Content-Type: application/json" \
  -d '{"target": "wasm"}'

# Check build status
curl http://localhost:8080/api/status

# Build all languages
curl -X POST http://localhost:8080/api/build/all \
  -H "Content-Type: application/json" \
  -d '{"target": "wasm"}'
```

**Legacy Static Server:**
```bash
pf web-dev-static  # Use basic static file server
```

#### Run Tests

Execute Playwright end-to-end tests:
```bash
pf web-test
```

## Project Structure

```
pf-web-poly-compile-helper-runner/
├── Pfyfile.pf                      # Root task definitions for web/WASM
├── start.sh                        # Quick setup script
│
├── pf-runner/                      # pf task runner implementation
│   ├── pf.py                       # Main runner (single-file Fabric wrapper)
│   ├── Pfyfile.pf                  # Main pf configuration
│   ├── Pfyfile.*.pf                # Modular task files (dev, builds, tests, etc.)
│   ├── README.md                   # Detailed pf-runner documentation
│   ├── scripts/                    # Helper scripts for system setup
│   └── ...
│
├── demos/                          # Demo applications
│   └── pf-web-polyglot-demo-plus-c/
│       ├── rust/                   # Rust WASM source
│       │   ├── src/lib.rs
│       │   └── Cargo.toml
│       ├── c/                      # C WASM source
│       │   └── c_trap.c
│       ├── fortran/                # Fortran WASM source
│       │   └── src/hello.f90
│       ├── asm/                    # WAT (WebAssembly text) source
│       │   └── mini.wat
│       └── web/                    # Web frontend
│           ├── index.html          # Demo UI
│           └── wasm/               # Compiled WASM output (generated)
│
├── examples/                       # Example projects
│   └── wit-rust-component/         # WIT component example
│
├── pf/                             # WIT definitions
│   └── wit/
│       ├── pf-base.wit             # Base WIT interface definitions
│       └── README.md
│
├── tests/                          # Test suite
│   └── e2e/
│       ├── cautionary.spec.ts      # Cautionary test cases
│       └── polyglot-plus-c.spec.ts # Polyglot demo tests
│
├── tools/                          # Development tools
│   └── static-server.mjs           # HTTP server for local development
│
└── playwright.config.ts            # Playwright test configuration
```

## Usage Examples

### Basic pf Commands

List available tasks:
```bash
pf list
```

Run a specific task:
```bash
pf web-dev
```

Pass parameters to tasks:
```bash
pf web-dev port=8080 dir=web
```

### Polyglot Shell Examples

The pf runner supports inline code execution in multiple languages. Create a `Pfyfile.pf`:

```text
task demo-python
  shell_lang python
  shell print("Hello from Python!")
  shell import sys; print(f"Python {sys.version}")
end

task demo-rust
  shell [lang:rust] fn main() { println!("Hello from Rust!"); }
end

task demo-inline-file
  shell [lang:go] @examples/hello.go -- arg1 arg2
end
```

Then run:
```bash
pf demo-python
pf demo-rust
```

### Automagic Builder Examples

The automagic builder automatically detects your project's build system and runs the appropriate build command. No manual configuration needed!

#### Basic Usage

```bash
# Let pf auto-detect and build your project
pf autobuild
```

The builder will:
1. Scan the current directory for build system files
2. Detect the most appropriate build system (prioritizes specific over generic)
3. Execute the correct build command with sensible defaults

#### Advanced Usage

```bash
# Build in release/optimized mode
pf autobuild release=true

# Use more parallel jobs for faster builds
pf autobuild jobs=8

# Build a specific subdirectory
pf autobuild dir=./my-subproject

# Combine parameters
pf autobuild release=true jobs=16 dir=./backend
```

#### Detection Priority

When multiple build files are present, the automagic builder follows this priority order:

1. **Rust** (Cargo.toml) - Most specific, well-defined
2. **Go** (go.mod) - Language-specific module
3. **Node.js** (package.json) - JavaScript ecosystem
4. **Python** (setup.py, pyproject.toml) - Python packages
5. **Maven** (pom.xml) - Java/JVM projects
6. **Gradle** (build.gradle) - Java/JVM projects
7. **CMake** (CMakeLists.txt) - Cross-platform C/C++
8. **Meson** (meson.build) - Modern build system
9. **Just** (justfile) - Command runner
10. **Autotools** (configure) - Classic Unix builds
11. **Make** (Makefile) - Generic fallback
12. **Ninja** (build.ninja) - Low-level build files

This ensures that projects with both a CMakeLists.txt and a generated Makefile will use CMake (the source of truth) rather than the generated Makefile.

#### Detection Only

Want to see what would be built without actually building?

```bash
# Just show what build system is detected
pf build_detect
```

Output example:
```
✓ Detected: CMake (use 'cmake' verb)
✓ Detected: Makefile (use 'makefile' verb)
```

#### Creating Automagic Build Tasks

Use the `autobuild` verb in your own tasks:

```text
task quick-build
  describe Fast build with auto-detection
  autobuild jobs=8
end

task release
  describe Release build with auto-detection
  autobuild release=true jobs=12
end

task build-all-modules
  describe Build multiple modules automatically
  autobuild dir=./frontend
  autobuild dir=./backend
  autobuild dir=./shared
end
```

#### Real-World Examples

**Rust Project:**
```bash
# Auto-detects Cargo.toml and runs: cargo build
pf autobuild

# Runs: cargo build --release
pf autobuild release=true
```

**Node.js Project:**
```bash
# Auto-detects package.json and runs: npm run build (or npm install)
pf autobuild
```

**CMake C++ Project:**
```bash
# Auto-detects CMakeLists.txt and runs:
# cmake -B build -DCMAKE_BUILD_TYPE=Release
# cmake --build build -j 4
pf autobuild release=true
```

**Monorepo with Multiple Projects:**
```bash
# Build each subproject with its own build system
pf autobuild dir=./rust-service
pf autobuild dir=./web-frontend
pf autobuild dir=./c-lib
```

### Build System Integration

```text
task build-with-make
  makefile all jobs=4
end

task build-with-cmake
  cmake . build_dir=build build_type=Release
end

task build-with-cargo
  cargo build release=true
end
```

### Remote Execution

```bash
# Run on remote hosts
pf hosts=user@server1.com:22,user@server2.com:22 deploy

# Run with sudo
pf host=user@server.com:22 sudo=true update-system

# Use environment presets (requires ENV_MAP configuration in pf.py)
pf env=prod deploy
```

## Development Workflow

### Setting Up for Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pf-web-poly-compile-helper-runner
   ```

2. **Run the setup script**
   ```bash
   ./start.sh
   ```

3. **Install Node.js dependencies** (if running web demos)
   ```bash
   npm install playwright
   ```

### Making Changes

1. **Edit source files** in `demos/pf-web-polyglot-demo-plus-c/`

2. **Rebuild WASM modules**
   ```bash
   pf web-build-all
   ```

3. **Test changes**
   ```bash
   pf web-dev  # Start dev server
   pf web-test # Run automated tests
   ```

### Adding New Tasks

Create or edit `.pf` files:

```text
task my-new-task
  describe Brief description of what this task does
  shell echo "Task implementation"
  shell command1
  shell command2
end
```

Tasks support:
- `describe`: Documentation shown in `pf list`
- `shell`: Execute shell commands
- `shell_lang`: Set language for polyglot execution
- `env`: Set environment variables
- `packages`, `service`, `directory`, `copy`: System management verbs
- Build helpers: `makefile`, `cmake`, `cargo`, `go_build`, etc.

## Testing

### Run All Tests
```bash
pf web-test
```

### Run Specific Test Files
```bash
npx playwright test tests/e2e/polyglot-plus-c.spec.ts
```

### Debug Tests
```bash
npx playwright test --debug
```

### View Test Report
```bash
npx playwright show-report
```

## Documentation

- **🚀 QUICKSTART Guide**: See [`QUICKSTART.md`](QUICKSTART.md) - **Start here!** Comprehensive guide with examples of all features
- **pf-runner Documentation**: See [`pf-runner/README.md`](pf-runner/README.md) for comprehensive pf runner documentation
- **REST API Guide**: See [`docs/REST-API.md`](docs/REST-API.md) for complete API documentation and examples
- **Fuzzing & Sanitizers Guide**: See [`docs/FUZZING.md`](docs/FUZZING.md) for fuzzing, AFL++, and sanitizer documentation
- **Security Testing Guide**: See [`docs/SECURITY-TESTING.md`](docs/SECURITY-TESTING.md) for web application security testing
- **Binary Injection Guide**: See [`docs/BINARY-INJECTION.md`](docs/BINARY-INJECTION.md) for injection and hooking documentation
- **LLVM Lifting Guide**: See [`docs/LLVM-LIFTING.md`](docs/LLVM-LIFTING.md) for binary lifting documentation
- **Kernel Debugging Guide**: See [`docs/KERNEL-DEBUGGING.md`](docs/KERNEL-DEBUGGING.md) for advanced debugging features
- **Interactive TUI Guide**: See [`docs/TUI.md`](docs/TUI.md) for text user interface documentation
- **Package Manager Guide**: See [`docs/PACKAGE-MANAGER.md`](docs/PACKAGE-MANAGER.md) for package format translation

### 🆕 Reverse Engineering Tools Roadmap
- **Executive Summary**: See [`docs/RE-TOOLS-EXECUTIVE-SUMMARY.md`](docs/RE-TOOLS-EXECUTIVE-SUMMARY.md) - Quick overview of missing tools (start here!)
- **Comprehensive Tool List**: See [`docs/MISSING-RE-DEBUG-EXPLOIT-TOOLS.md`](docs/MISSING-RE-DEBUG-EXPLOIT-TOOLS.md) - Detailed descriptions of 40+ tools to integrate
- **Quick Reference**: See [`docs/RE-TOOLS-QUICK-REFERENCE.md`](docs/RE-TOOLS-QUICK-REFERENCE.md) - Fast lookup table and comparison charts
- **Implementation Roadmap**: See [`docs/IMPLEMENTATION-ROADMAP.md`](docs/IMPLEMENTATION-ROADMAP.md) - Detailed implementation plan with timelines

### Examples and Demos
- **Kernel Debugging Demo**: See [`demos/kernel-debugging/README.md`](demos/kernel-debugging/README.md) for examples
- **Binary Lifting Examples**: See [`demos/binary-lifting/README.md`](demos/binary-lifting/README.md) for lifting tutorials
- **Debugging Guide**: See [`demos/debugging/README.md`](demos/debugging/README.md) for debugging and reverse engineering
- **ROP Exploit Demo**: See [`demos/rop-exploit/README.md`](demos/rop-exploit/README.md) for ROP exploitation tutorial
- **Git Cleanup Guide**: See [`docs/GIT-CLEANUP.md`](docs/GIT-CLEANUP.md) for removing large files from git history
- **Web Demo Documentation**: See [`demos/pf-web-polyglot-demo-plus-c/README.md`](demos/pf-web-polyglot-demo-plus-c/README.md)
- **WIT Components**: See [`pf/wit/README.md`](pf/wit/README.md)

Additional documentation in `pf-runner/`:
- `BUILD-HELPERS.md`: Build system integration guide
- `LANGS.md`: Supported polyglot languages
- `EXAMPLE-PIPELINE.md`: CI/CD pipeline examples
- `IMPLEMENTATION-SUMMARY.md`: Implementation details

## Common Tasks Reference

| Command | Description |
|---------|-------------|
| `pf autobuild` | **Automagic builder** - auto-detect and build any project |
| `pf autobuild release=true` | Build in release/optimized mode |
| `pf build_detect` | Detect build system without building |
| `pf web-dev` | **Start development server with REST API support** |
| `pf web-dev-static` | Start basic static file server (legacy) |
| `pf api-server` | Start REST API server |
| `pf web-test` | Run Playwright tests |
| `pf web-build-all` | Build all WASM modules (Rust, C, Fortran, WAT) |
| `pf web-build-all-wasm` | Build all languages to WebAssembly |
| `pf web-build-all-asm` | Build all languages to asm.js (where supported) |
| `pf web-build-all-llvm` | Build all languages to LLVM IR (O3 optimization by default) |
| `pf web-build-all-llvm opt_level=2` | Build with custom optimization level (0-3, s, z) |
| `pf web-build-rust` | Build Rust → WASM |
| `pf web-build-rust-llvm` | Build Rust → LLVM IR (O3 by default) |
| `pf web-build-rust-llvm opt_level=2` | Build Rust → LLVM IR with O2 optimization |
| `pf web-build-c` | Build C → WASM |
| `pf web-build-c-asm` | Build C → asm.js |
| `pf web-build-c-llvm` | Build C → LLVM IR (O3 by default) |
| `pf web-build-c-llvm parallel=true` | Build C → LLVM IR with OpenMP parallelization |
| `pf web-build-c-llvm-opt` | Build C → LLVM IR with custom optimization passes |
| `pf web-build-wat` | Assemble WAT → WASM |
| `pf web-build-fortran` | Build Fortran → WASM |
| `pf web-build-fortran-llvm` | Build Fortran → LLVM IR (O3 by default) |
| `pf web-build-fortran-llvm parallel=true` | Build Fortran → LLVM IR with OpenMP |
| **Binary Lifting Commands** | |
| `pf install-retdec` | Install RetDec binary lifter |
| `pf build-lifting-examples` | Build example binaries for lifting demos |
| `pf lift-binary-retdec binary=<path>` | Lift binary to LLVM IR using RetDec |
| `pf lift-inspect binary=<path>` | Inspect binary with LLVM tools |
| `pf optimize-lifted-ir input=<file.ll>` | Optimize lifted LLVM IR |
| `pf test-lifting-workflow` | Test complete lifting workflow |
| `pf lifting-help` | Show detailed lifting commands help |
| **Binary Injection Commands** | |
| `pf install-injection-tools` | Install binary injection and manipulation tools |
| `pf build-injection-examples` | Build example injection payloads and targets |
| `pf create-injection-payload-rust source=<path>` | Create injectable Rust library |
| `pf create-injection-payload-c source=<file.c>` | Create injectable C library |
| `pf create-injection-payload-fortran source=<file.f90>` | Create injectable Fortran library |
| `pf create-injection-payload-llvm source=<file.ll>` | Create injectable library from LLVM IR |
| `pf create-injection-payload-wasm-native source=<file.wasm>` | Convert WASM to injectable native library |
| `pf analyze-injection-target binary=<path>` | Analyze binary for injection opportunities |
| `pf inject-static-library binary=<path> payload=<lib.so>` | Patch binary to load injection library |
| `pf inject-constructor binary=<path> payload=<lib.so>` | Add constructor injection to binary |
| `pf inject-runtime-library pid=<pid> payload=<lib.so>` | Inject library into running process |
| `pf inject-preload binary=<path> payload=<lib.so>` | Run binary with LD_PRELOAD injection |
| `pf inject-rust-into-binary rust_source=<path> target_binary=<path>` | Complete Rust injection workflow |
| `pf inject-c-into-binary c_source=<file.c> target_binary=<path>` | Complete C injection workflow |
| `pf inject-wasm-into-binary wasm_source=<file.wasm> target_binary=<path>` | Complete WASM injection workflow |
| `pf test-injection-workflow` | Test complete injection pipeline |
| `pf injection-help` | Show detailed injection commands help |
| `pf compile-c-shared-lib source=<c>` | Compile C to shared library (.so/.dylib) |
| `pf compile-rust-shared-lib crate=<dir>` | Compile Rust to shared library |
| `pf inject-shared-lib binary=<exe> lib=<so>` | Inject library into program (LD_PRELOAD) |
| `pf patch-binary-deps binary=<exe> old_lib=<old> new_lib=<new>` | Patch binary dependencies |
| `pf create-hook-lib output=<file.c>` | Generate function hook template |
| `pf wasm-to-native input=<wasm> output=<so>` | Convert WASM to native library |
| `pf inject-wasm-component host=<wasm> component=<wasm>` | Inject WASM into WASM |
| `pf demo-injection-workflow` | Demo complete injection workflow |
| `pf install-injection-tools` | Install patchelf, nasm, binaryen, wabt |
| `pf injection-help` | Show detailed injection commands help |
| **Automagic Vulnerability Discovery** | |
| `pf kernel-automagic-analysis binary=<path>` | **Comprehensive auto-analysis: parse functions + complexity + vulnerabilities** |
| `pf kernel-parse-detect binary=<path>` | **Auto-detect parse functions in binary** |
| `pf kernel-complexity-analyze binary=<path>` | **Find functions with many if/else, long functions, high complexity** |
| `pf kernel-fuzz-in-memory binary=<path>` | **Fast in-memory fuzzing with loop-back (100-1000x faster)** |
| **Fuzzing & Sanitizers** | |
| `pf install-fuzzing-tools` | Install all fuzzing tools (AFL++, libfuzzer, sanitizers) |
| `pf install-sanitizers` | Install LLVM sanitizer libraries |
| `pf install-libfuzzer` | Install libfuzzer development files |
| `pf install-aflplusplus` | Install AFL++ fuzzer |
| `pf build-with-asan source=<file>` | Build with AddressSanitizer |
| `pf build-with-msan source=<file>` | Build with MemorySanitizer |
| `pf build-with-ubsan source=<file>` | Build with UndefinedBehaviorSanitizer |
| `pf build-with-tsan source=<file>` | Build with ThreadSanitizer |
| `pf build-with-all-sanitizers source=<file>` | Build with all sanitizers |
| `pf generate-libfuzzer-template` | Generate libfuzzer harness template |
| `pf build-libfuzzer-target source=<file>` | Build fuzzing target with libfuzzer |
| `pf run-libfuzzer target=<fuzzer>` | Run libfuzzer on target |
| `pf build-afl-target source=<file>` | Build target with AFL++ instrumentation |
| `pf build-afl-llvm-target source=<file>` | Build target with AFL++ LLVM mode |
| `pf afl-fuzz target=<binary>` | Run AFL++ fuzzer |
| `pf afl-analyze-crashes` | Analyze AFL++ crash findings |
| `pf afl-minimize-corpus` | Minimize AFL++ corpus |
| `pf lift-and-instrument-binary binary=<path>` | Lift binary to LLVM IR and instrument with AFL++ |
| `pf instrument-llvm-ir-afl input=<file.ll>` | Instrument LLVM IR with AFL++ |
| `pf create-fuzzing-example` | Create example fuzzing target |
| `pf demo-fuzzing` | Run complete fuzzing demonstration |
| `pf fuzzing-help` | Show fuzzing and sanitizer help |
| **ROP Exploit Demonstration** | |
| `pf rop-build` | Build vulnerable binaries for ROP demonstration |
| `pf rop-check` | Check security features of built binaries |
| `pf rop-gadgets` | Find ROP gadgets in the vulnerable binary |
| `pf rop-exploit` | Generate ROP exploit payload |
| `pf rop-test` | Test the ROP exploit (will crash the program) |
| `pf rop-demo` | Complete ROP demonstration workflow |
| `pf rop-disasm` | Show disassembly of vulnerable function |
| `pf rop-symbols` | Show symbol table of vulnerable binary |
| `pf rop-install-tools` | Install ROP analysis tools (ROPgadget, ropper) |
| `pf rop-clean` | Clean ROP demo build artifacts |
| `pf rop-help` | Show ROP demo help and available commands |
| **Debugging & Reverse Engineering** | |
| `pf install-debuggers` | Install GDB, LLDB, and pwndbg |
| `pf build-debug-examples` | Build C/C++/Rust debug examples |
| `pf debug binary=<path>` | Start interactive debugger shell |
| `pf debug-gdb binary=<path>` | Debug directly with GDB |
| `pf debug-lldb binary=<path>` | Debug directly with LLDB |
| `pf debug-info binary=<path>` | Show binary information |
| `pf disassemble binary=<path>` | Disassemble binary |
| `pf binary-info binary=<path>` | Show detailed binary info |
| `pf debug-help` | Show debugging commands help |

| **Git Repository Cleanup** | |
| `pf git-cleanup` | **Interactive TUI for removing large files from git history** |
| `pf git-analyze-large-files` | Analyze repository for large files without removal |
| `pf git-repo-size` | Show current git repository size statistics |
| `pf install-git-filter-repo` | Install git-filter-repo dependency |
| `pf git-cleanup-help` | Show git cleanup commands help |

| **Interactive TUI** | |
| `pf tui` | **Launch interactive TUI for task management and debugging** |
| `pf tui-with-file file=<path>` | Launch TUI with specific Pfyfile |
| `pf install-tui-deps` | Install TUI dependencies (rich library) |
| `pf tui-help` | Show TUI usage and features |

| **Debugging Tools Installation** | |
| `pf install-oryx` | Install oryx - TUI for exploring binaries |
| `pf install-binsider` | Install binsider - Binary analyzer with TUI |
| `pf install-rustnet` | Install rustnet - Network monitoring tool |
| `pf install-sysz` | Install sysz - Systemd unit file viewer |
| `pf install-radare2` | Install Radare2 - Reverse engineering framework |
| `pf install-ghidra` | Install Ghidra - NSA's reverse engineering suite |
| `pf install-snowman` | Install Snowman - C++ decompiler (open source) |
| `pf install-binaryninja-info` | Show Binary Ninja information (commercial) |
| `pf install-all-debug-tools` | Install all debugging and RE tools |
| `pf check-debug-tools` | Check installation status of debugging tools |
| `pf run-oryx binary=<path>` | Run oryx binary explorer on a file |
| `pf run-binsider binary=<path>` | Run binsider binary analyzer on a file |
| `pf run-snowman binary=<path>` | Run Snowman decompiler on a file |
| `pf run-rustnet` | Run rustnet network monitor |
| `pf run-sysz` | Run sysz systemd unit viewer |
| `pf debug-tools-help` | Show help for debugging tools |

| **Web Application Security Testing** | |
| `pf security-scan [url=<url>]` | Run comprehensive security scan |
| `pf security-scan-verbose [url=<url>]` | Security scan with verbose output |
| `pf security-scan-json [url=<url>]` | Security scan with JSON output |
| `pf security-scan-sqli [url=<url>]` | Scan for SQL injection only |
| `pf security-scan-xss [url=<url>]` | Scan for XSS only |
| `pf security-scan-critical [url=<url>]` | Scan for critical vulnerabilities |
| `pf security-fuzz [url=<url>]` | Run web application fuzzer |
| `pf security-fuzz-sqli [url=<url>]` | Fuzz with SQL injection payloads |
| `pf security-fuzz-xss [url=<url>]` | Fuzz with XSS payloads |
| `pf security-fuzz-traversal [url=<url>]` | Fuzz with path traversal payloads |
| `pf security-fuzz-all [url=<url>]` | Fuzz with all payload types |
| `pf security-test-all [url=<url>]` | Run complete security test suite |
| `pf security-test-api [url=<url>]` | Test API security specifically |
| `pf security-test-dev` | Test development server |
| `pf security-check-headers [url=<url>]` | Check security headers |
| `pf security-check-csrf [url=<url>]` | Check CSRF protection |
| `pf security-check-auth [url=<url>]` | Check authentication/access control |
| `pf security-report [url=<url>]` | Generate JSON security reports |
| `pf security-help` | Show security testing help |

| **Package Manager Translation** | |
| `pf pkg-convert source=<pkg> target=<fmt>` | Convert package between formats (via .deb hub) |
| `pf pkg-convert-to-deb source=<pkg>` | Convert any package to .deb |
| `pf pkg-convert-to-rpm source=<pkg>` | Convert any package to .rpm |
| `pf pkg-convert-to-flatpak source=<pkg>` | Convert any package to .flatpak |
| `pf pkg-convert-to-snap source=<pkg>` | Convert any package to .snap |
| `pf pkg-convert-to-pacman source=<pkg>` | Convert any package to .pkg.tar.zst |
| `pf pkg-info package=<pkg>` | Display package information |
| `pf pkg-deps package=<pkg> target=<fmt>` | Resolve dependencies for target format |
| `pf pkg-formats` | Show available package formats |
| `pf pkg-matrix` | Show conversion compatibility matrix |
| `pf pkg-batch-convert packages=<pkgs> target=<fmt>` | Convert multiple packages |
| `pf pkg-check-deps package=<pkg> target=<fmt>` | Check if dependencies are satisfied |
| `pf pkg-install-deps package=<pkg> target=<fmt>` | Install missing dependencies |
| `pf install-pkg-tools` | Install package conversion tools |
| `pf install-flatpak` | Install Flatpak package manager |
| `pf install-snap` | Install Snapd package manager |
| `pf pkg-help` | Show package manager help |

| **Multi-Distro Container Management** | |
| `pf distro-install distro=<d> packages=<p>` | Install packages from specific distro container |
| `pf distro-install-fedora packages=<p>` | Install packages from Fedora container |
| `pf distro-install-centos packages=<p>` | Install packages from CentOS container |
| `pf distro-install-arch packages=<p>` | Install packages from Arch container |
| `pf distro-install-opensuse packages=<p>` | Install packages from openSUSE container |
| `pf distro-switch distro=<d>` | Switch active distro for PATH (isolated mode) |
| `pf distro-view-unified` | Enable unified view (all distros in one directory) |
| `pf distro-view-isolated` | Enable isolated view (per-distro directories) |
| `pf distro-status` | Show status and installed packages |
| `pf distro-build-all` | Build all distro container images |
| `pf distro-cleanup` | Remove distro images (keep artifacts) |
| `pf distro-cleanup-all` | Remove distro images and artifacts |
| `pf distro-help` | Show distro container help |

| **OS Switching (Experimental)** | |
| `pf switch-os target=<t> partition=<p>` | Switch to different OS using containers + kexec |
| `pf switch-os-fedora partition=<p>` | Switch to Fedora Linux |
| `pf switch-os-arch partition=<p>` | Switch to Arch Linux |
| `pf switch-os-ubuntu partition=<p>` | Switch to Ubuntu Linux |
| `pf switch-os-debian partition=<p>` | Switch to Debian Linux |
| `pf os-snapshot name=<n>` | Create OS snapshot for recovery |
| `pf os-snapshots` | List available OS snapshots |
| `pf os-status` | Show OS switching status and capabilities |
| `pf os-prepare target=<t>` | Prepare target OS container (no switch) |
| `pf install-kexec` | Install kexec-tools for rebootless switching |
| `pf switch-os-help` | Show OS switching help |

| **Installation & Setup** | |
| `pf install-base` | Install base pf runner and dependencies |
| `pf install-web` | Install web/WASM development tools |
| `pf install` | Install everything (base + web) |
| `pf list` | List all available tasks |

| **Container & Quadlet Commands** | |
| `pf container-build-all` | Build all container images |
| `pf container-build-base` | Build base Ubuntu 24.04 image |
| `pf container-build-api` | Build API server images |
| `pf container-build-compilers` | Build compiler images (Rust, C, Fortran) |
| `pf container-build-debugger` | Build debugger images |
| `pf compose-up` | Start API server using podman-compose |
| `pf compose-down` | Stop all containers |
| `pf compose-build-wasm` | Build all WASM modules using containers |
| `pf compose-debugger` | Start debugging container interactively |
| `pf compose-debugger-gpu` | Start GPU-enabled debugger |
| `pf quadlet-install` | Install Podman quadlet files for systemd |
| `pf quadlet-status` | Show status of quadlet services |
| `pf dev-container` | Start development environment using containers |
| `pf container-test` | Run container infrastructure tests |
| `pf container-help` | Show help for container and quadlet commands |

## Troubleshooting

### Installation Issues

#### pf command not found
- Run `sudo ./install.sh` to reinstall
- For user install: `./install.sh --prefix ~/.local`
- Run `source ~/.bashrc` (or `~/.zshrc`) to reload your shell configuration
- Check that the install path is in your PATH
- For legacy install, use `bak/install-legacy.sh`

#### Fabric import error
- Run `pip install --user "fabric>=3.2,<4"` to install the dependency
- Or reinstall with: `./install.sh` (dependencies are installed automatically)

#### Installation script fails
- Ensure Python 3.10+ is installed: `python3 --version`
- Ensure pip is available: `python3 -m pip --version`
- For container install, ensure docker or podman is installed
- Review error messages for specific missing dependencies

### WASM build failures
- **Rust**: Ensure `wasm-pack` is installed: `cargo install wasm-pack`
- **C**: Install and activate Emscripten (see Prerequisites)
- **WAT**: Install WABT: `sudo apt-get install wabt`
- **Fortran**: Install LFortran (experimental, optional)

### Server won't start
- Check port availability: `lsof -i :8080`
- Use a different port: `pf web-dev port=3000`
- Ensure Node.js is installed: `node --version`

### Tests failing
- Build WASM modules first: `pf web-build-all`
- Install Playwright: `npm install playwright`
- Install Playwright browsers: `npx playwright install`

### Permission errors during setup
- The setup script requires `sudo` for system packages
- Ensure you have sudo privileges or install dependencies manually

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run the test suite: `pf web-test`
6. Submit a pull request

## License

See LICENSE file for details.

## Support

- File issues on the GitHub repository
- Check existing documentation in `pf-runner/` directory
- Review example tasks in `Pfyfile.pf` files

---

**Quick Links:**
- [pf-runner Documentation](pf-runner/README.md)
- [Web Demo Guide](demos/pf-web-polyglot-demo-plus-c/README.md)
- [Build Helpers Guide](pf-runner/BUILD-HELPERS.md)
- [Supported Languages](pf-runner/LANGS.md)
