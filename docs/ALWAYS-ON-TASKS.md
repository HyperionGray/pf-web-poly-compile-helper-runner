# Always-On Tasks Documentation

## Overview

Always-on tasks are general-purpose pf tasks that are available system-wide, regardless of the current directory. These tasks don't require project-specific files and provide essential system management, security, and development capabilities.

## What Makes a Task "Always-On"?

A task is considered "always-on" if it:
1. Does NOT require reading files from a specific project directory
2. Provides general OS-level functionality
3. Works independently of project context
4. Is useful for system administration and development workflows

## Implementation

Always-on tasks are stored in `/pf-runner/Pfyfile.always-on-*.pf` files and are automatically included when pf-runner is installed. These tasks are available from any directory on the system.

## Task Categories

### 1. TUI (Terminal User Interface) - `Pfyfile.always-on-tui.pf`

Interactive terminal interface for managing pf tasks.

**Available Tasks:**
- `pf tui` - Launch interactive TUI
- `pf tui-with-file file=<path>` - Launch TUI with specific Pfyfile
- `pf install-tui-deps` - Install TUI dependencies (rich library)
- `pf tui-help` - Show TUI help

**Use Cases:**
- Browse and execute tasks interactively
- Explore available pf capabilities
- Visual task organization by category

### 2. Smart Workflows - `Pfyfile.always-on-smart.pf`

Intelligent tool combinations and workflow automation.

**Available Tasks:**
- `pf smart-help` - Show smart workflow help
- `pf smart-workflows-help` (alias: `swh`) - Comprehensive documentation

**Use Cases:**
- Reduce cognitive load by combining tools intelligently
- Quick reference for smart workflow capabilities

### 3. Exploit Development - `Pfyfile.always-on-exploit.pf`

Modern exploit development and binary analysis tools.

**Available Tasks:**
- `pf install-checksec` - Install checksec binary protection checker
- `pf install-pwntools` - Install pwntools framework
- `pf install-ropgadget` - Install ROPgadget tool
- `pf install-ropper` - Install ropper tool
- `pf install-exploit-tools` - Install all exploit tools
- `pf checksec binary=<file>` - Check binary security features
- `pf pwn-cyclic length=<n>` - Generate cyclic pattern
- `pf pwn-cyclic-find pattern=<hex>` - Find offset in pattern
- `pf pwn-shellcode arch=<arch>` - Generate shellcode
- `pf rop-find-gadgets binary=<file>` - Find ROP gadgets
- `pf exploit-help` - Show exploit development help

**Use Cases:**
- Security research and penetration testing
- Binary exploitation development
- ROP chain construction
- Buffer overflow analysis

### 4. Security Testing - `Pfyfile.always-on-security.pf`

Security scanning and vulnerability testing basics.

**Available Tasks:**
- `pf security-help` - Show security testing help
- `pf checksec binary=<file>` - Analyze binary security
- `pf checksec-json binary=<file>` - JSON output
- `pf security-scan-help` - Web security scanning help

**Use Cases:**
- Quick security feature checks
- Binary hardening verification
- Installation guidance for full security tools

### 5. Debugging Tools - `Pfyfile.always-on-debug.pf`

Installation and management of debugging/reverse engineering tools.

**Available Tasks:**
- `pf install-oryx` - Install oryx binary explorer (TUI)
- `pf install-binsider` - Install binsider binary analyzer
- `pf install-radare2` - Install Radare2 RE framework
- `pf install-gdb` - Install GDB debugger
- `pf install-lldb` - Install LLDB debugger
- `pf install-all-debug-tools` - Install all debugging tools
- `pf check-debug-tools` - Check installation status
- `pf run-oryx binary=<file>` - Run oryx on binary
- `pf run-binsider binary=<file>` - Run binsider on binary
- `pf debug-help` - Show debugging help

**Use Cases:**
- Setting up debugging environment
- Binary analysis and reverse engineering
- Checking tool installation status

### 6. Git Management - `Pfyfile.always-on-git.pf`

Git repository management and cleanup.

**Available Tasks:**
- `pf install-git-filter-repo` - Install git-filter-repo
- `pf git-analyze-large-files` - Find large files in history
- `pf git-repo-size` - Show repository size
- `pf git-status` - Show git status
- `pf git-log count=<n>` - Show git log
- `pf git-help` - Show git management help

**Use Cases:**
- Repository size management
- Finding large files in git history
- Quick git status checks

### 7. System Backup - `Pfyfile.always-on-backup.pf`

System backup and snapshot management (inspired by bish-please).

**Available Tasks:**
- `pf backup-create [name=<name>]` - Create system backup snapshot
- `pf backup-list` - List available backups
- `pf backup-info` - Show backup system info
- `pf backup-help` - Show backup help

**Features:**
- Auto-detects best snapshot method (btrfs, ZFS, or rsync)
- Fast copy-on-write snapshots on supported filesystems
- Portable rsync fallback for any filesystem

**Use Cases:**
- Pre-upgrade system snapshots
- Regular system backups
- Recovery point creation

### 8. Package Management - `Pfyfile.always-on-packages.pf`

Package format translation and management tools.

**Available Tasks:**
- `pf pkg-formats` - Show supported package formats
- `pf pkg-help` - Show package management help
- `pf install-alien` - Install alien converter
- `pf install-pkg-tools` - Install package conversion tools

**Supported Formats:**
- deb (Debian/Ubuntu)
- rpm (Red Hat/Fedora)
- flatpak
- snap
- pacman (Arch)

**Use Cases:**
- Package format conversion
- Cross-distro package installation

### 9. OS Management - `Pfyfile.always-on-os.pf`

Operating system and distro management capabilities.

**Available Tasks:**
- `pf os-info` - Show current OS information
- `pf distro-help` - Show distro container help
- `pf os-status` - Show OS and container status
- `pf install-podman` - Install podman container runtime
- `pf os-help` - Show OS management help

**Use Cases:**
- System information queries
- Container runtime management
- Distro container guidance

## Quick Reference

### Installation Tasks
```bash
# Exploit Development
pf install-exploit-tools

# Debugging Tools
pf install-all-debug-tools

# Git Tools
pf install-git-filter-repo

# Package Tools
pf install-pkg-tools

# Container Runtime
pf install-podman

# TUI
pf install-tui-deps
```

### Common Workflows

#### Security Analysis
```bash
# Check binary security features
pf checksec binary=/path/to/binary

# Generate exploit pattern
pf pwn-cyclic length=1000

# Find ROP gadgets
pf rop-find-gadgets binary=/path/to/binary
```

#### System Backup
```bash
# Create named backup
pf backup-create name=before-upgrade

# List backups
pf backup-list

# Show backup system info
pf backup-info
```

#### Git Repository Management
```bash
# Analyze large files
pf git-analyze-large-files

# Check repository size
pf git-repo-size
```

#### Interactive Exploration
```bash
# Launch TUI
pf tui

# Explore binary
pf run-oryx binary=/path/to/binary
```

## Design Philosophy

Always-on tasks follow these principles:

1. **Portability**: Work on any system without project context
2. **Simplicity**: Single command for common operations
3. **Discoverability**: Built-in help for all task categories
4. **Safety**: Provide guidance and warnings for dangerous operations
5. **Extensibility**: Easy to add new always-on tasks

## Related Issues

- Issue #237: "always-on tasks" - Main implementation issue
- Issue #235: "Always-available pf tasks" - Requirements definition
- Issue #127: "Actually... management of packages and executables" - Mentions bish-please backup system

## Future Enhancements

Potential additions to always-on tasks:

1. Network diagnostics and troubleshooting
2. Performance monitoring and profiling
3. Log analysis and management
4. Service management (systemd integration)
5. Environment management (virtualenv, conda, etc.)

## Contributing

To add new always-on tasks:

1. Create a new `Pfyfile.always-on-<category>.pf` file in `/pf-runner/`
2. Add tasks that work independently of project context
3. Include a help task (e.g., `<category>-help`)
4. Update `/pf-runner/Pfyfile.pf` to include the new file
5. Document the tasks in this file
6. Ensure tasks are categorized appropriately

## Troubleshooting

### Tasks Not Available

If always-on tasks aren't available:

1. Ensure pf-runner is properly installed
2. Check that `/pf-runner/Pfyfile.always-on-*.pf` files exist
3. Verify `/pf-runner/Pfyfile.pf` includes the always-on files
4. Try running `pf list` to see all available tasks

### Missing Dependencies

Some tasks require dependencies:

```bash
# TUI requires rich library
pf install-tui-deps

# Exploit tools require python packages
pf install-exploit-tools

# Debugging tools require cargo/rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Permission Issues

Some tasks require elevated privileges:

```bash
# Backup creation
sudo pf backup-create

# Package installation
sudo pf install-podman
```

## See Also

- [QUICKSTART.md](../QUICKSTART.md) - General pf quickstart guide
- [pf-runner/README.md](../pf-runner/README.md) - pf-runner documentation
- [CONTRIBUTING.md](development/CONTRIBUTING.md) - Contribution guidelines
