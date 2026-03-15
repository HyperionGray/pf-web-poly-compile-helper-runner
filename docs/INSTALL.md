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

### 3. Source Runtime Install (install-static.sh)

Fast installation that copies the Python runtime files without creating a venv.

**Requirements:**
- Python 3 on PATH
- Python packages: `lark`, `fabric`, `typer`

**Install:**

```bash
# System-wide install (requires sudo)
sudo ./install-static.sh

# User install (no sudo required)
./install-static.sh --prefix ~/.local

# Run built-in post-install smoke tests
./install-static.sh --prefix ~/.local --self-test
```

**What it does:**
- Copies runtime files from `pf-runner-full` to `<prefix>/lib/pf-runner`
- Installs a `pf` launcher to `<prefix>/bin/pf`
- Includes default `pf-files` task packs
- Optionally validates install via `--self-test` (`pf -V`, `pf --help`, `pf list`)

**Pros:**
- Simplest installation
- Fast installation
- No build step

**Cons:**
- Requires Python runtime dependencies to already be installed
- Not a single-file binary

---

## Which Method Should I Use?

- **Use .deb Package** (Recommended) if you're on Ubuntu/Debian and want system package manager integration and automatic updates
- **Use Source Runtime Install** if you want a fast non-venv install and already have Python deps available
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

**Source runtime install (`install-static.sh`):**
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

Upgrade to Python 3.8 or higher, or use the Debian package method.

### "ModuleNotFoundError" after install-static

Install required Python runtime dependencies:
```bash
pip install --user "lark>=1.1.0" "fabric>=3.2,<4" "typer>=0.12"
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
./install-static.sh            # Source runtime install (no build step)
```

---

## Support

For issues and questions, please visit:
https://github.com/HyperionGray/pf-web-poly-compile-helper-runner/issues
