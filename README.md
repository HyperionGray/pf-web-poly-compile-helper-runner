# pf-web-poly-compile-helper-runner

A comprehensive polyglot WebAssembly development environment featuring the **pf** task runner (Fabric-based DSL) and multi-language WASM compilation demos.

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

### Automagic Builder 🪄
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

### Testing & Development
- **Live dev server**: Static HTTP server with CORS headers for WASM
- **Playwright tests**: Automated browser testing for WASM modules
- **Hot reload**: Development workflow with instant feedback

## Prerequisites

### Minimum Requirements
- Linux (Ubuntu/Debian recommended) or macOS
- Git
- Python 3.8+ with pip
- sudo access (for system package installation)

**Note:** The installer script (`./install.sh`) will automatically install most prerequisites. You only need Git and Python to get started.

### Optional Prerequisites
These will be installed automatically by the installer if you choose the "web" or "all" installation:

- Node.js 18+ (for static server and Playwright tests)
- Rust toolchain (for building Rust WASM modules)
- Emscripten (for compiling C/C++ to WASM)
- WABT (WebAssembly Binary Toolkit for WAT compilation)
- LFortran (for Fortran WASM compilation - experimental)

## Installation

### Recommended: One-Command Install

The easiest way to get started:

```bash
# Clone the repository
git clone <repository-url>
cd pf-web-poly-compile-helper-runner

# Run the installer (interactive mode)
./install.sh

# Or install everything directly
./install.sh all
```

The installer will:
1. Install Python Fabric library (task runner framework)
2. Set up the pf command-line tool
3. Install shell completions (bash/zsh)
4. Optionally install web/WASM development tools

**Installation Modes:**

- `./install.sh base` - Install just pf runner and core dependencies
- `./install.sh web` - Install web/WASM development tools only
- `./install.sh all` - Install everything (recommended)
- `./install.sh --help` - Show detailed help

### Using pf Tasks (After Initial Install)

Once pf is installed, you can use these tasks:

```bash
pf install-base  # Install/update base components
pf install-web   # Install/update web tools
pf install       # Install/update everything
```

### What Gets Installed?

**Base Installation:**
- Python Fabric library (`fabric>=3.2,<4`)
- pf runner CLI tool (installed to `~/.local/bin/pf`)
- Shell completions for bash and zsh
- Core build tools (gcc, make, git)

**Web Installation:**
- Node.js and npm (if not present)
- Playwright for browser testing
- Rust toolchain with wasm-pack
- WABT (WebAssembly Binary Toolkit)
- Emscripten info (manual installation guidance)
- LFortran info (optional Fortran support)

## Quick Start

### 1. Install pf-runner

The repository includes a **comprehensive installer script** that sets up everything you need:

#### One-Command Installation (Recommended)

```bash
# Interactive installer - choose what to install
./install.sh

# Or install everything directly
./install.sh all
```

The installer provides three installation modes:

- **Base** (`./install.sh base`): Install pf runner, Python dependencies, and core build tools
- **Web** (`./install.sh web`): Install web/WASM development tools (Node.js, Playwright, Rust, Emscripten, WABT)
- **All** (`./install.sh all`): Install everything (recommended)

#### Using pf Commands

After initial installation, you can also use pf tasks:

```bash
pf install-base  # Install base pf runner and dependencies
pf install-web   # Install web/WASM development tools
pf install       # Install everything
```

#### Legacy Installation (Alternative)

The older installation script is still available:

```bash
./start.sh  # Legacy setup script
```

#### Manual Installation

For manual control:

```bash
cd pf-runner
pip install --user "fabric>=3.2,<4"
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

#### Start Development Server

```bash
pf web-dev
```

The server will start on http://localhost:8080. Open this URL in your browser to see the polyglot WASM demo in action.

You can customize the port and directory:
```bash
pf web-dev port=3000 dir=demos/pf-web-polyglot-demo-plus-c/web
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

- **pf-runner Documentation**: See [`pf-runner/README.md`](pf-runner/README.md) for comprehensive pf runner documentation
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
| `pf web-dev` | Start development server (default: localhost:8080) |
| `pf web-test` | Run Playwright tests |
| `pf web-build-all` | Build all WASM modules (Rust, C, Fortran, WAT) |
| `pf web-build-rust` | Build Rust → WASM |
| `pf web-build-c` | Build C → WASM |
| `pf web-build-wat` | Assemble WAT → WASM |
| `pf web-build-fortran` | Build Fortran → WASM |
| `pf install-base` | Install base pf runner and dependencies |
| `pf install-web` | Install web/WASM development tools |
| `pf install` | Install everything (base + web) |
| `pf list` | List all available tasks |

## Troubleshooting

### Installation Issues

#### pf command not found
- Run `./install.sh base` to install pf-runner
- Or run `source ~/.bashrc` to reload your shell configuration
- Check that `~/.local/bin` is in your PATH
- Legacy option: Run `./start.sh` to use the older installer

#### Fabric import error
- Ensure Fabric is installed: `pip install --user "fabric>=3.2,<4"`
- Verify with: `python3 -c "import fabric; print(fabric.__version__)"`
- Re-run: `./install.sh base`

#### Installation script fails
- Check that you have sudo access for system packages
- Ensure internet connection is available
- Review error messages for specific missing dependencies
- Try manual installation steps from README

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
