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

### System Requirements
- Linux (Ubuntu/Debian recommended) or macOS
- Python 3.8+ with pip
- Node.js 18+ (for static server and Playwright tests)
- Git

### Optional (for WASM compilation)
- **Rust toolchain**: For building Rust WASM modules
  ```bash
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
  cargo install wasm-pack
  ```

- **Emscripten**: For compiling C/C++ to WASM
  ```bash
  git clone https://github.com/emscripten-core/emsdk.git
  cd emsdk
  ./emsdk install latest
  ./emsdk activate latest
  source ./emsdk_env.sh
  ```

- **WABT**: WebAssembly Binary Toolkit for WAT compilation
  ```bash
  # Ubuntu/Debian:
  sudo apt-get install wabt
  
  # macOS:
  brew install wabt
  ```

- **LFortran**: For Fortran WASM compilation (experimental)
  - Follow instructions at https://lfortran.org/

## Quick Start

### 1. Install pf-runner

The repository includes an installation script that sets up the pf task runner:

```bash
# Run the complete setup (installs dependencies and builds pf-runner)
./start.sh
```

This script will:
- Update system packages
- Set up Python virtual environment
- Install base dependencies
- Install build tools
- Build and install the pf runner

Alternatively, for manual installation:

```bash
cd pf-runner
pip install "fabric>=3.2,<4"
make setup        # Creates ./pf symlink
make install      # Installs to system or ~/.local/bin
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
| `pf web-dev` | Start development server (default: localhost:8080) |
| `pf web-test` | Run Playwright tests |
| `pf web-build-all` | Build all WASM modules (Rust, C, Fortran, WAT) |
| `pf web-build-rust` | Build Rust → WASM |
| `pf web-build-c` | Build C → WASM |
| `pf web-build-wat` | Assemble WAT → WASM |
| `pf web-build-fortran` | Build Fortran → WASM |
| `pf list` | List all available tasks |

## Troubleshooting

### pf command not found
- Run `./start.sh` to install pf-runner
- Or use `./pf-runner/pf` instead of `pf`
- Check that `~/.local/bin` is in your PATH

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
