# Installation Guide

## Quick Install (One Command)

### System-wide Installation (Recommended)
```bash
sudo ./install.sh
```

### User Installation (No sudo required)
```bash
./install.sh --prefix ~/.local
```

## What the installer does

1. ✅ Checks prerequisites (Python 3.8+, Git, pip)
2. ✅ Installs system dependencies (build tools, python3-dev)
3. ✅ Sets up Python virtual environment (for user installs)
4. ✅ Installs Python dependencies (fabric, lark)
5. ✅ Installs pf-runner to your system
6. ✅ Sets up shell completions (bash/zsh)
7. ✅ Validates installation by running pf tasks

## Installation Options

```bash
# System-wide installation
sudo ./install.sh

# User installation (installs to ~/.local)
./install.sh --prefix ~/.local

# Custom installation directory
./install.sh --prefix /opt/pf-runner

# Skip system dependency installation
./install.sh --skip-deps

# Show help
./install.sh --help
```

## Prerequisites

- **Linux** (Ubuntu/Debian, RHEL/Fedora, Arch) or **macOS**
- **Python 3.8+** with pip
- **Git**
- **Build tools** (gcc, make) - installed automatically

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
   ls -la /usr/local/bin/pf
   
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

### System installation
```bash
sudo rm -f /usr/local/bin/pf
sudo rm -rf /usr/local/lib/pf-runner
sudo rm -f /etc/bash_completion.d/pf
sudo rm -f /usr/local/share/zsh/site-functions/_pf
```

### User installation
```bash
rm -f ~/.local/bin/pf
rm -rf ~/.local/lib/pf-runner
rm -rf ~/.local/lib/pf-runner-venv
rm -f ~/.local/share/bash-completion/completions/pf
rm -f ~/.zsh/completions/_pf
```

## Advanced Installation

For container-based workflows or development setups, see the full documentation in `docs/`.

## Getting Help

- **Installation issues**: Run `./install.sh --help`
- **Usage help**: Run `pf --help` or `pf list`
- **Documentation**: See `README.md` and `docs/` directory
- **Interactive help**: Run `pf tui` for the interactive interface

---

**That's it!** The installation should "just work" with one command. If you encounter any issues, check the troubleshooting section above.