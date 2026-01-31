# pf-runner Installer Validation and User Guide

This document provides comprehensive information about the pf-runner installer system, validation process, and user installation instructions.

## Quick Start for Users

### Fresh Ubuntu Installation (Native)

For users who just installed Ubuntu and want to get pf-runner working immediately:

```bash
# Clone the repository
git clone <repository-url>
cd pf-web-poly-compile-helper-runner

# Install natively (system-wide, requires sudo)
sudo ./install.sh --mode native

# OR install to user directory (no sudo required)
./install.sh --mode native --prefix ~/.local

# Test the installation
pf --version
pf list
```

### Container Installation

For users who prefer containerized execution:

```bash
# Clone the repository
git clone <repository-url>
cd pf-web-poly-compile-helper-runner

# Install with containers (podman preferred)
./install.sh --mode container --runtime podman

# OR with docker
./install.sh --mode container --runtime docker

# Test the installation
pf --version
pf list
```

## Installer Validation System

### Overview

The installer validation system consists of several test scripts that ensure both native and container installations work correctly without any assumptions about the user's environment.

### Test Scripts

1. **`master_validation.sh`** - Main validation script that runs all tests
2. **`test_native_installer.sh`** - Tests native installation process
3. **`test_container_installer.sh`** - Tests container installation and variants
4. **`apply_fixes.sh`** - Applies necessary fixes to the repository

### Running Validation Tests

```bash
# Run all validation tests
./master_validation.sh

# Run only native installer tests
./test_native_installer.sh

# Run only container installer tests
./test_container_installer.sh

# Apply repository fixes manually
./apply_fixes.sh
```

## Fixed Issues

### 1. Hardcoded Shebang Path

**Problem**: `pf-runner/pf_parser.py` contained a hardcoded shebang path:
```python
#!/home/punk/projects/pf-web-poly-compile-helper-runner/venv/bin/python
```

**Solution**: Replaced with portable shebang:
```python
#!/usr/bin/env python3
```

### 2. Installation Path Assumptions

**Problem**: The installer made assumptions about user environment and paths.

**Solution**: Enhanced the installer to:
- Detect and handle different installation prefixes
- Work without pre-existing virtual environments
- Handle both user and system installations
- Provide clear error messages and guidance

### 3. Container Runtime Detection

**Problem**: Container installation assumed specific runtime availability.

**Solution**: Improved runtime detection to:
- Try podman first, fall back to docker
- Provide clear error messages when no runtime is found
- Handle both rootless and rootful container scenarios

## Container Variants

The repository includes multiple container variants for different use cases:

### Core Containers
- **base** - Ubuntu 24.04 base image with common tools
- **pf-runner** - Main pf task runner with Python/Fabric
- **api-server** - REST API server for pf tasks

### Development Containers
- **build-c** - C/C++ development environment
- **build-rust** - Rust development environment
- **build-fortran** - Fortran development environment
- **debugger** - Debugging tools and environment
- **debugger-gpu** - GPU debugging capabilities

### OS Containers
- **distro-arch** - Arch Linux environment
- **distro-centos** - CentOS environment
- **distro-fedora** - Fedora environment
- **distro-opensuse** - openSUSE environment

### Specialized Containers
- **pe-reactos** - ReactOS PE environment
- **pe-windows-server** - Windows Server PE environment
- **macos-qemu** - macOS emulation environment

### Container Status

After validation, the containers are categorized as:
- **Buildable**: Can be built and used immediately
- **Requires Dependencies**: Needs other containers built first
- **External Dependencies**: Requires external resources
- **Broken**: Has configuration issues

## Installation Modes

### Native Installation

**Advantages**:
- Direct execution on host system
- Better performance
- Easier debugging
- Full system integration

**Requirements**:
- Python 3.8+
- Git
- pip
- Build tools (for some Python packages)

**Process**:
1. Check prerequisites
2. Install system dependencies (optional)
3. Set up Python environment
4. Install Python dependencies (fabric, lark)
5. Install pf-runner files
6. Create executable wrapper
7. Set up shell completions
8. Validate installation

### Container Installation

**Advantages**:
- Isolated execution environment
- Consistent behavior across systems
- No host system dependencies
- Easy cleanup and updates

**Requirements**:
- Container runtime (podman or docker)
- Sufficient disk space for images

**Process**:
1. Detect container runtime
2. Build base and pf-runner images
3. Install container wrapper
4. Set up shell completions
5. Validate installation

## Troubleshooting

### Common Issues

1. **Python version too old**
   ```
   Solution: Install Python 3.8 or newer
   ```

2. **pip not available**
   ```
   Solution: Install python3-pip package
   ```

3. **Container runtime not found**
   ```
   Solution: Install podman or docker
   ```

4. **Permission denied during installation**
   ```
   Solution: Use sudo for system install or --prefix ~/.local for user install
   ```

5. **pf command not found after installation**
   ```
   Solution: Add installation directory to PATH or restart shell
   ```

### Getting Help

1. Check the installation log for error messages
2. Run validation tests to identify issues
3. Ensure all prerequisites are installed
4. Try alternative installation mode (native vs container)

## Development and Testing

### For Developers

To test installer changes:

```bash
# Run full validation suite
./master_validation.sh

# Test specific installation mode
./test_native_installer.sh
./test_container_installer.sh

# Apply fixes after changes
./apply_fixes.sh
```

### Adding New Container Variants

1. Create Dockerfile in `containers/dockerfiles/`
2. Use appropriate base image
3. Follow naming convention: `Dockerfile.variant-name`
4. Test build process
5. Update documentation

### Validation Criteria

For an installer to pass validation:

1. **No hardcoded paths** - All paths must be dynamic
2. **No environment assumptions** - Must work on fresh Ubuntu
3. **Clear error messages** - Users should understand what went wrong
4. **Proper cleanup** - Failed installations should not leave artifacts
5. **Comprehensive testing** - All major code paths tested

## Conclusion

The pf-runner installer system now provides robust, assumption-free installation for both native and container modes. Users can install on fresh Ubuntu systems without any pre-configuration, and the validation system ensures continued reliability.

For the latest information and updates, refer to the repository documentation and run the validation tests before deployment.