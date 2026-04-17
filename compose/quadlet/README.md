# Quadlet Configuration

This directory contains Quadlet configuration files for managing the polyglot development environment with Podman.

## Files

- `*.pod` - Pod definitions that group related containers
- `*.container` - Individual container definitions
- `*.network` - Network configuration
- `*.volume` - Volume definitions for persistent storage

## Pods

1. **pf-main-pod** - Main pod used by `pf-web-service`, `pf-build-service`, `pf-security-service`, and `pf-dev-service`
2. **pf-main-pod-gpu** - Optional GPU variant used by `pf-build-service-gpu`

## Usage

Copy these files to your systemd user directory:

```bash
# Create systemd user directory
mkdir -p ~/.config/containers/systemd

# Copy quadlet files
cp compose/quadlet/*.{pod,container,network,volume} ~/.config/containers/systemd/

# Reload systemd
systemctl --user daemon-reload

# Start the main pod
systemctl --user start pf-main-pod.service
```

## GPU Support

For GPU support, use:
- `pf-main-pod-gpu.pod`
- `pf-build-service-gpu.container`

## Networking

All pods are connected via the `pf-network` for inter-service communication.
External access is provided through port mappings on the web pod.
