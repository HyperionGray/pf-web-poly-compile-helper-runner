# Distro Container Management & OS Switching

This document describes the container-based approach to multi-distro package management and OS switching functionality in pf.

## Overview

The distro container system provides:

1. **Multi-Distro Package Management** - Install and use packages from different Linux distributions (Fedora, CentOS, Arch, openSUSE) without polluting your host system
2. **View Modes** - Unified view (all distro binaries in one place) or isolated view (separate directories per distro)
3. **OS Switching** - Switch between different OS using containers and kexec for rebootless kernel switching

## Distro Container Management

### Quick Start

```bash
# Initialize directories
pf distro-init

# Install packages from Fedora
pf distro-install-fedora packages="vim htop neofetch"

# Install packages from Arch
pf distro-install-arch packages="neovim tree"

# Check what's installed
pf distro-status
```

### How It Works

1. **Lightweight Containers**: Each distro (Fedora, CentOS, Arch, openSUSE) has a minimal container image with just the package manager
2. **rshared Mounts**: Containers mount the output directory with `rshared` propagation for efficient artifact extraction
3. **Binary Extraction**: When you install a package, the binaries are extracted to `~/.pf/distros/<distro>/bin`
4. **PATH Integration**: Add the distro's bin directory to your PATH to use the installed tools

### Supported Distros

| Distro | Package Manager | Container Image |
|--------|-----------------|-----------------|
| Fedora | dnf | fedora:40 |
| CentOS | dnf (yum) | almalinux:9 |
| Arch | pacman | archlinux:latest |
| openSUSE | zypper | opensuse/tumbleweed |

### Commands

#### Install Packages

```bash
# Generic install command
pf distro-install distro=fedora packages="vim htop"

# Distro-specific shortcuts
pf distro-install-fedora packages="vim htop"
pf distro-install-centos packages="nginx php"
pf distro-install-arch packages="neovim tree"
pf distro-install-opensuse packages="gcc make"
```

#### View Modes

Two view modes are available:

**Unified Mode** (default):
All distro binaries are symlinked to a single directory. First distro wins if there are conflicts.

```bash
pf distro-view-unified
export PATH="$HOME/.pf/distros/unified/bin:$PATH"
```

**Isolated Mode**:
Each distro has its own directory. Switch between them as needed.

```bash
pf distro-view-isolated
pf distro-switch distro=fedora
export PATH="$HOME/.pf/distros/fedora/bin:$PATH"
```

#### Management Commands

```bash
# Show status and installed packages
pf distro-status

# Build all distro images
pf distro-build-all

# Build specific distro image
pf distro-build distro=fedora

# Clean up images (keep artifacts)
pf distro-cleanup

# Clean up everything
pf distro-cleanup-all

# Show help
pf distro-help
```

### Directory Structure

```
~/.pf/distros/
├── config.json           # Current settings and installed packages
├── fedora/
│   ├── bin/              # Extracted binaries
│   ├── lib/              # Extracted libraries
│   ├── share/            # Shared data
│   └── etc/              # Configuration files
├── centos/
│   └── ...
├── arch/
│   └── ...
├── opensuse/
│   └── ...
└── unified/
    └── bin/              # Symlinks from all distros
```

## OS Switching

### ⚠️ Warning

**OS switching is a powerful system-level feature.** It can modify your system at a low level. Always:

1. Have working backups (bish-please or similar)
2. Test with `dry_run=true` first
3. Ensure you understand what will happen
4. Have a rescue USB/boot media ready

### How It Works

1. **MirrorOS Snapshots**: Creates backups of your current OS using btrfs/zfs/rsync
2. **Container Preparation**: Downloads and prepares the target OS container
3. **Filesystem Sync**: Syncs the new OS to a target partition
4. **kexec Switch**: Uses kexec for rebootless kernel switching

### Quick Start (Dry Run)

```bash
# Check current status
pf os-status

# Test switching to Fedora (dry run)
pf switch-os target=fedora dry_run=true
```

### Snapshot Methods

The system automatically detects the best snapshot method:

| Method | Speed | Requirements |
|--------|-------|--------------|
| btrfs | Fastest | Root on btrfs subvolume |
| zfs | Fast | ZFS pool |
| rsync | Slower | Always available |

### Commands

#### Create Snapshots

```bash
# Create named snapshot
pf os-snapshot name=before-upgrade

# Create timestamped snapshot
pf os-snapshot

# List all snapshots
pf os-snapshots
```

#### Switch OS

```bash
# Full switch to Fedora (requires partition)
pf switch-os target=fedora partition=/dev/sda3

# Dry run (test what would happen)
pf switch-os target=arch dry_run=true

# Distro-specific shortcuts
pf switch-os-fedora partition=/dev/sda3
pf switch-os-ubuntu partition=/dev/sda3 dry_run=true
```

#### Other Commands

```bash
# Show current OS and capabilities
pf os-status

# Prepare target OS container without switching
pf os-prepare target=fedora

# Install kexec-tools
pf install-kexec

# Show help
pf switch-os-help
```

### Supported Target OS

| Target | Container Image | Notes |
|--------|-----------------|-------|
| fedora | fedora:40 | DNF package manager |
| arch | archlinux:latest | Rolling release |
| ubuntu | ubuntu:24.04 | LTS release |
| debian | debian:bookworm | Stable |

### The Switch Process

When you run `pf switch-os target=fedora partition=/dev/sda3`:

1. **[1/5] Backup**: Creates a snapshot of your current OS
2. **[2/5] Prepare**: Downloads and extracts the target OS container
3. **[3/5] Check**: Validates the target partition
4. **[4/5] Sync**: Rsyncs the new OS filesystem to the partition
5. **[5/5] kexec**: Loads the new kernel with kexec

After completion, run `sudo kexec -e` to switch to the new kernel.

### Recovery

If something goes wrong:

1. **From snapshot**: Restore from the pre-switch snapshot
2. **Boot media**: Use a live USB to access your system
3. **Backup partition**: Your original OS partition should be untouched

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PF_DISTRO_ARTIFACTS` | `~/.pf/distros` | Distro artifact base directory |
| `PF_SWITCH_BASE` | `~/.pf/os-switch` | OS switching base directory |
| `CONTAINER_RT` | `podman` | Container runtime (podman/docker) |

## Technical Details

### rshared Mounts

The system uses rshared bind mounts for efficient artifact extraction:

```bash
podman run --rm \
  -v ~/.pf/distros/fedora:/output:rshared \
  --security-opt label=disable \
  pf-distro-fedora \
  /usr/local/bin/distro-extract vim htop
```

### Container Build

Distro containers are minimal, containing only:
- Base OS image
- Package manager
- Extraction script

```bash
# Build all distro images
pf distro-build-all

# Images are tagged as:
# localhost/pf-distro-fedora:latest
# localhost/pf-distro-centos:latest
# etc.
```

### kexec Integration

The OS switcher uses kexec for rebootless kernel switching:

```bash
# Load new kernel
kexec -l /path/to/vmlinuz --initrd=/path/to/initrd.img --command-line="..."

# Execute switch (point of no return!)
kexec -e
```

## API Usage

Both tools export functions for programmatic use:

```javascript
import { 
  installPackage, 
  switchDistro, 
  setViewMode,
  CONFIG 
} from './tools/distro-container-manager.mjs';

import {
  createSnapshot,
  switchOS,
  detectSnapshotMethod
} from './tools/os-switcher.mjs';

// Install packages
await installPackage('fedora', 'vim htop');

// Switch view mode
setViewMode('unified');

// Create snapshot
await createSnapshot('my-backup');

// Switch OS (dry run)
await switchOS('fedora', { dryRun: true });
```

## Troubleshooting

### Container Build Fails

```bash
# Check container runtime
podman info

# Build with verbose output
podman build -t pf-distro-fedora -f containers/dockerfiles/Dockerfile.distro-fedora .
```

### Package Installation Fails

```bash
# Enter container manually
podman run -it --rm pf-distro-fedora /bin/bash

# Try installing package directly
dnf install -y vim
```

### kexec Not Available

```bash
# Install kexec-tools
pf install-kexec

# Or manually:
sudo apt install kexec-tools  # Debian/Ubuntu
sudo dnf install kexec-tools  # Fedora
```

### Snapshot Fails

```bash
# Check filesystem type
stat -f -c %T /

# Check if rsync is available
which rsync

# Try manual rsync
sudo rsync -axHAWXS --numeric-ids / /tmp/test-backup/
```

## License

See the project LICENSE file.
