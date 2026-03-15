# Installation Guide

## Quick Install (One Command)

Use the bundled quick installer to perform a native install with minimal setup:
```bash
# Clone and install in one go
git clone https://github.com/P4X-ng/pf-web-poly-compile-helper-runner.git
cd pf-web-poly-compile-helper-runner
./quick-install.sh
```

The quick installer applies the native workflow, selects the right prefix, and installs dependencies automatically.

If you prefer to run the installer directly, call:
```bash
# Preflight checks only (no install changes)
./install.sh --check

# System-wide install (requires sudo)
sudo ./install.sh

# User install (no sudo needed)
./install.sh --prefix ~/.local
```

### Running the WebAssembly toolchain tasks

Tasks such as `web-toolchain-check`, `web-build-c-wasm`, and `web-build-fortran-wasm` require the Emscripten SDK and related binaries in `PATH`. If you installed emsdk under `$HOME/emsdk-*`, run them through the helper:
```bash
./scripts/pf-with-emsdk.sh web-toolchain-check
./scripts/pf-with-emsdk.sh web-build-c-wasm
./scripts/pf-with-emsdk.sh web-build-fortran-wasm
```

The script sources `emsdk_env.sh` from the first matching `$HOME/emsdk-*` directory (override `EMSDK_ROOT` if needed) so `emcc`, `wasm-pack`, `wat2wasm`, `clang`, and `opt-18` become available to pf.

## What the installer does

1. Checks prerequisites (Python 3.8+, Git, pip)
2. Installs system dependencies (unless `--skip-deps` is requested)
3. Creates a per-prefix Python virtual environment (user installs only)
4. Installs Python dependencies (fabric, lark, typer)
5. Copies pf-runner into `${PREFIX}/lib/pf-runner`
6. Creates the `pf` executable wrapper in `${PREFIX}/bin`
7. Deploys shell completions (bash/zsh) when possible
8. Validates the native `pf` command (`pf list`, `pf --version`)

## Installation Options

```bash
# System install (requires sudo)
sudo ./install.sh

# User install (no sudo)
./install.sh --prefix ~/.local

# Use a custom prefix
./install.sh --prefix /opt/pf-runner

# Skip system dependency installation (when dependencies are already satisfied)
./install.sh --skip-deps

# Run readiness checks without changing the system
./install.sh --check --skip-deps --prefix ~/.local

# Show help page
./install.sh --help
```

## Prerequisites

- **Linux** (Ubuntu/Debian/Fedora/Arch) or **macOS**
- **Git**
- **Python 3.8+** with pip (`python3 -m ensurepip`)
- **Build tools** (`gcc`, `make`, `curl`) for compiling dependencies

## After Installation

1. **Restart your shell** or run: `source ~/.bashrc`
2. **Test the installation**:
   ```bash
   pf --version
   pf list
   ```
3. **Start using pf**:
   ```bash
   pf web-dev          # Start web development server
   pf autobuild        # Auto-detect and build your project
   pf tui              # Launch interactive TUI
   ```

## Troubleshooting

### Command not found: pf
If you get "command not found" after installation:

1. **Check your PATH** (for user installations):
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

2. **Verify installation location**:
   ```bash
   # System install
   ls -la /usr/bin/pf
   
   # User install  
   ls -la ~/.local/bin/pf
   ```

### Python dependency issues
If you get Python import errors:

1. **Reinstall with dependencies**:
   ```bash
   ./install.sh --skip-deps  # Skip system deps if they're already installed
   ```

2. **Manual dependency install**:
   ```bash
   pip3 install --user "fabric>=3.2,<4" "lark>=1.1.0"
   ```

### Permission denied
If you get permission errors:

1. **Use user installation**:
   ```bash
   ./install.sh --prefix ~/.local
   ```

2. **Or fix permissions for system install**:
   ```bash
   sudo ./install.sh
   ```

## Uninstallation

### System install
```bash
sudo rm -f /usr/bin/pf
sudo rm -rf /usr/lib/pf-runner
sudo rm -f /etc/bash_completion.d/pf
sudo rm -f /usr/share/zsh/vendor-completions/_pf
```

### User install
```bash
rm -f ~/.local/bin/pf
rm -rf ~/.local/lib/pf-runner
rm -rf ~/.local/lib/pf-runner-venv
rm -f ~/.local/share/bash-completion/completions/pf
rm -f ~/.zsh/completions/_pf
```

## Advanced Installation

For detailed workflows, scripting, or container references, see the relevant documents under `docs/`.

## Getting Help

- **Installation issues**: Run `./install.sh --help`
- **Readiness checks**: Run `./install.sh --check`
- **Usage help**: Run `pf --help` or `pf list`
- **Documentation**: See `README.md` and `docs/` directory
- **Interactive help**: Run `pf tui` for the interactive interface

---

**That's it!** The installation should "just work" with one command. If you encounter any issues, check the troubleshooting section above.
