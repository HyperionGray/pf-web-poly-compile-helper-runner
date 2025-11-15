# Polyglot WebAssembly Demo

This directory contains a multi-language WebAssembly demonstration featuring:

- **Rust**: A simple library with math functions
- **C**: A trap handler demonstration using `__builtin_trap`
- **Fortran**: A hello world program
- **WebAssembly Text Format (WAT)**: A minimal add function

## Building

To build all the WASM modules, you need to install the required toolchains:

### Prerequisites

1. **Rust and wasm-pack**:
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   cargo install wasm-pack
   ```

2. **Emscripten** (for C):
   ```bash
   git clone https://github.com/emscripten-core/emsdk.git
   cd emsdk
   ./emsdk install latest
   ./emsdk activate latest
   source ./emsdk_env.sh
   ```

3. **LFortran** (for Fortran, optional):
   Follow instructions at https://lfortran.org/

4. **WABT** (for WAT):
   ```bash
   # On Ubuntu/Debian:
   sudo apt-get install wabt
   
   # On macOS:
   brew install wabt
   ```

### Build Commands

Using the pf task runner:

```bash
# Build all modules
pf web-build-all

# Or build individually:
pf web-build-rust
pf web-build-c
pf web-build-wat
pf web-build-fortran  # Optional, requires lfortran
```

### Running the Demo

Start the development server:

```bash
pf web-dev
```

Then open http://localhost:8080 in your browser.

### Testing

Run the Playwright tests:

```bash
pf web-test
```

## Project Structure

```
demos/pf-web-polyglot-demo-plus-c/
├── rust/               # Rust source code
│   ├── src/
│   │   └── lib.rs
│   └── Cargo.toml
├── c/                  # C source code
│   └── c_trap.c
├── fortran/            # Fortran source code
│   └── src/
│       └── hello.f90
├── asm/                # WebAssembly text format
│   └── mini.wat
└── web/                # Output directory and web interface
    ├── index.html
    └── wasm/           # Compiled WASM modules (generated)
        ├── rust/
        │   └── pkg/
        ├── c/
        ├── fortran/
        └── asm/
```
