# pf-runner Installation Guide

This repository provides **TWO** officially supported installation methods for pf-runner. Choose the one that best fits your needs.

> **Note:** RPM and Arch Linux package support has been deprecated. See `bak/installers/README.md` for more information.

## Installation Methods

### 1. Native Installation (install.sh)

The native installer sets up pf-runner directly on your system with Python dependencies.

**Requirements:**
- Python 3.8 or higher
- pip
- Git

**Usage:**

```bash
# System-wide install (requires sudo)
sudo ./install.sh

# User install (no sudo required)
./install.sh --prefix ~/.local

# Skip system dependency installation
./install.sh --prefix ~/.local --skip-deps
```

**What it does:**
- Checks prerequisites (Python 3.8+, Git, pip)
- Installs system dependencies (optional)
- Sets up Python virtual environment (for user installs)
- Installs Python dependencies (lark, fabric, typer)
- Copies pf-runner files to installation directory
- Creates pf executable wrapper
- Installs shell completions

**Pros:**
- Full-featured installation
- Python dependencies properly managed
- Works on all systems with Python 3.8+

**Cons:**
- Requires Python and build tools
- Longer installation time

---

### 2. Debian Package (.deb)

Pre-built Debian package for Ubuntu/Debian systems.

**Requirements:**
- Ubuntu 24.04 or compatible Debian-based system
- dpkg

**Usage:**

```bash
# Build the .deb package
cd debian
./build-deb.sh 1.0.0

# Install the package
sudo dpkg -i build/pf-runner_1.0.0.deb

# If dependencies are missing, install them
sudo apt-get install -f
```

**What it does:**
- Installs pf-runner to /usr/local/lib/pf-runner
- Creates /usr/local/bin/pf executable
- Installs Python dependencies via postinst script
- Properly integrated with system package manager

**Pros:**
- Clean uninstall via dpkg
- System package manager integration
- Automatic dependency resolution

**Cons:**
- Debian/Ubuntu only
- Requires dpkg

---

### 3. Static Installer (`install-static.sh`)

`install-static.sh` now supports explicit install modes:

- `--mode static`: install `pf-runner-full/pf-static`
- `--mode python`: install a Python wrapper plus runtime files
- `--mode auto` (default): use static if available, otherwise fall back to Python mode

**Build static binary (optional, one-time):**

```bash
cd pf-runner-full
make build-static
```

**Install examples:**

```bash
# System-wide auto mode (uses static if present)
sudo ./install-static.sh

# User install, force static mode
./install-static.sh --prefix ~/.local --mode static

# User install, auto-build static if missing, then verify
./install-static.sh --prefix ~/.local --build-static-if-missing --verify

# User install, force Python mode
./install-static.sh --prefix ~/.local --mode python
```

**What it does:**
- Installs `pf` into `<prefix>/bin`
- In Python mode, installs runtime files under `<prefix>/lib/pf-runner`
- Optionally runs post-install smoke checks with `--verify`

**Pros:**
- Flexible install modes for different environments
- Optional dependency-free static install
- Predictable fallback behavior in auto mode

**Cons:**
- Static mode requires a built `pf-static` binary
- Python mode still needs Python runtime dependencies (`lark`, `fabric`, `typer`)

---

## Which Method Should I Use?

- **Use .deb Package** (Recommended) if you're on Ubuntu/Debian and want system package manager integration and automatic updates
- **Use Static Executable** (Recommended) if you want the simplest installation with no dependencies on non-Debian systems
- **Use Native Install** if you're developing pf-runner or need a customizable installation

## Verification

After installation, verify it works:

```bash
# Check version
pf --version

# List available tasks
pf list

# Get help
pf --help
```

## Uninstallation

**Debian package:**
```bash
sudo dpkg -r pf-runner
```

**Static executable:**
```bash
# System-wide
sudo rm /usr/local/bin/pf

# User install
rm ~/.local/bin/pf
```

**Native install:**
```bash
# System-wide
sudo rm -rf /usr/local/lib/pf-runner /usr/local/bin/pf

# User install
rm -rf ~/.local/lib/pf-runner ~/.local/bin/pf
```

## Troubleshooting

### "pf: command not found"

Add the installation directory to your PATH:

```bash
# For ~/.local/bin
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# For /usr/local/bin
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### "Python version too old"

Upgrade to Python 3.8 or higher, or use the static executable method.

### "PyInstaller not found"

Install it:
```bash
pip install --user pyinstaller
```

---

## Building from Source

If you want to build from source:

```bash
# Clone the repository
git clone https://github.com/HyperionGray/pf-web-poly-compile-helper-runner.git
cd pf-web-poly-compile-helper-runner

# Choose your installation method
./install.sh                    # Native
./debian/build-deb.sh 1.0.0    # Debian package
./install-static.sh --mode auto # Static when available, otherwise Python mode
```

---

## Support

For issues and questions, please visit:
https://github.com/HyperionGray/pf-web-poly-compile-helper-runner/issues
