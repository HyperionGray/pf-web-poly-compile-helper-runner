# Containers Directory

This directory contains all containerization files for the polyglot development environment.

## Structure

- `web-services/` - API server and web interface containers
- `build-environment/` - Compilation toolchains for Rust, C, Fortran, WAT
- `security-tools/` - Debugging and reverse engineering tools
- `development/` - pf-runner and development environment
- `base/` - Common base images and shared components
- `dockerfiles/` - All Dockerfile definitions
- `scripts/` - Container build and management scripts
- `quadlets/` - Podman Quadlet files for systemd integration

## PE Execution Containers

The project includes specialized containers for running Windows Portable Executables (PEs) and macOS applications:

### Available PE Containers

| Container | Description | Base |
|-----------|-------------|------|
| `pf-pe-vmkit` | VMKit lightweight VM with full passthrough | Ubuntu 22.04 + QEMU |
| `pf-pe-reactos` | ReactOS-based native PE execution | Ubuntu 22.04 + QEMU + ReactOS |
| `pf-macos-qemu` | macOS VM using QEMU (Docker-OSX style) | Ubuntu 22.04 + QEMU |

### Building PE Containers

```bash
# Build all PE containers
./containers/scripts/build-containers.sh pe

# Build individual containers
pf pe-build-vmkit
pf pe-build-reactos
pf pe-build-macos
```

### Using PE Containers

#### VMKit (Lightweight VM with passthrough)

```bash
# Setup VMKit environment
pf pe-vmkit-setup

# Run a PE file
pf pe-vmkit-run pe=/path/to/myapp.exe

# Analyze PE before running
pf pe-vmkit-analyze pe=/path/to/myapp.exe
```

#### ReactOS (Windows-compatible open-source OS)

```bash
# Setup ReactOS (downloads LiveCD)
pf pe-reactos-setup

# Run PE in ReactOS VM
pf pe-reactos-run pe=/path/to/myapp.exe

# Interactive shell
pf pe-reactos-shell
```

#### macOS (QEMU-based)

```bash
# Create macOS disk image
pf macos-setup

# Start macOS VM (requires legal macOS image)
pf macos-run

# Run headless
pf macos-run-headless
```

### KVM Acceleration

For best performance, use KVM acceleration:

```bash
# Docker/Podman with KVM
podman run --device /dev/kvm ...

# Check KVM availability
ls -la /dev/kvm
```

### Notes

- **ReactOS** is an open-source Windows-compatible operating system
- **macOS containers** require legitimate Apple hardware/license
- All containers support `--device /dev/kvm` for hardware acceleration
- See `Pfyfile.pe-containers.pf` for all available tasks

## Automatic Containerization

The pf-runner includes an automatic containerization module (`pf_containerize.py`) that can:

1. **Detect project type** - Automatically identify programming languages and build systems
2. **Generate Dockerfiles** - Create optimized Dockerfiles based on project detection
3. **Generate Quadlet files** - Create systemd service files for Podman
4. **Build with retry** - Automatically retry failed builds with error pattern matching

### Quick Start

```bash
# Auto-containerize the current project
pf containerize

# Generate Dockerfile only (no build)
pf containerize dockerfile_only=true

# Containerize with hints
pf containerize install_deps="libssl-dev" main_bin="./build/app" port=8080

# Build with retry and then containerize
pf ci-containerize image=myapp tag=v1.0.0
```

### Supported Languages and Build Systems

| Language | Build System | Detection File |
|----------|-------------|----------------|
| Rust | Cargo | `Cargo.toml` |
| Go | Go Modules | `go.mod` |
| Node.js | npm/yarn/pnpm | `package.json` |
| Python | pip/poetry/pipenv | `requirements.txt`, `pyproject.toml` |
| C/C++ | CMake | `CMakeLists.txt` |
| C/C++ | Make | `Makefile` |
| C/C++ | Meson | `meson.build` |
| Java | Maven | `pom.xml` |
| Java | Gradle | `build.gradle` |

### User Hints

When automatic detection isn't enough, you can provide hints:

- `--install-hint-deps="apt packages"` - Additional system packages to install
- `--main-bin-hint="path/to/binary"` - Main executable path
- `--port-hint=8080` - Port to expose
- `--base-image-hint="image:tag"` - Base Docker image to use
- `--build-commands-hint="make && make install"` - Custom build commands

### Retry Mechanism

The `autobuild_retry` command includes automatic error recovery:

```bash
# Basic retry with defaults (3 retries, exponential backoff)
pf autobuild_retry

# Custom retry configuration
pf autobuild_retry max_retries=5 initial_delay=2 max_delay=60
```

Error patterns automatically detected and fixed:
- Missing apt packages
- Missing Python/Node modules
- Permission denied errors
- Network timeouts
- Missing lock files (Cargo.lock, go.sum)

## Traditional Container Usage

Each subdirectory contains:
- `Dockerfile` - Container definition
- `entrypoint.sh` - Container startup script
- `README.md` - Service-specific documentation
- Configuration files as needed

### Building Containers

```bash
# Build all container images
./containers/scripts/build-containers.sh all

# Build specific components
./containers/scripts/build-containers.sh base
./containers/scripts/build-containers.sh api
./containers/scripts/build-containers.sh build
./containers/scripts/build-containers.sh debug
./containers/scripts/build-containers.sh pe    # PE execution containers
```

### Using Quadlets (Systemd Integration)

Quadlet files in `quadlets/` enable systemd-native container management:

```bash
# Install quadlet files
./containers/scripts/install-quadlets.sh --install

# Start services
systemctl --user start pf-main-pod

# View logs
journalctl --user -u pf-web-service -f
```

See the main README.md for complete setup instructions.