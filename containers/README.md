# Containers Directory

This directory contains all containerization files for the polyglot development environment.

## Structure

- `web-services/` - API server and web interface containers
- `build-environment/` - Compilation toolchains for Rust, C, Fortran, WAT
- `security-tools/` - Debugging and reverse engineering tools
- `development/` - pf-runner and development environment
- `base/` - Common base images and shared components

## Usage

Each subdirectory contains:
- `Dockerfile` - Container definition
- `entrypoint.sh` - Container startup script
- `README.md` - Service-specific documentation
- Configuration files as needed

See the main README.md for complete setup instructions.