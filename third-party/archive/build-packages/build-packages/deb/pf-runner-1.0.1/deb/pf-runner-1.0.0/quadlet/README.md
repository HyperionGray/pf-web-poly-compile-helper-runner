# Quadlet Configuration

This directory contains Quadlet configuration files for managing the polyglot development environment with Podman.

## Files

- `*.pod` - Pod definitions that group related containers
- `*.container` - Individual container definitions
- `*.network` - Network configuration
- `*.volume` - Volume definitions for persistent storage

## Pods

1. **pf-web-pod** - Web services (API server, static files)
2. **pf-build-pod** - Build environment (Rust, C, Fortran, WASM)
3. **pf-security-pod** - Security and debugging tools
4. **pf-dev-pod** - Development environment (pf-runner, TUI)

## Usage

Copy these files to your systemd user directory:

```bash
# Create systemd user directory
mkdir -p ~/.config/containers/systemd

# Copy quadlet files
cp quadlet/*.{pod,container,network,volume} ~/.config/containers/systemd/

# Reload systemd
systemctl --user daemon-reload

# Start the main pod
systemctl --user start pf-main-pod.service
```

## GPU Support

For GPU support, use the GPU-enabled variants:
- `pf-build-pod-gpu.pod`
- `pf-security-pod-gpu.pod`

## Networking

All pods are connected via the `pf-network` for inter-service communication.
External access is provided through port mappings on the web pod.