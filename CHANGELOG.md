# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-05

### Added
- Initial stable release
- **pf-runner**: Lightweight, single-file task runner with Fabric-based DSL
- **Polyglot WebAssembly Demo**: Multi-language WASM compilation (Rust, C, Fortran, WAT)
- **REST API Server**: Build management via REST endpoints with WebSocket support
- **Interactive TUI**: Terminal UI for task management using Python's rich library
- **Container Infrastructure**: Podman quadlets and compose support
- **Debugging Tools Integration**: GDB, LLDB, pwndbg, radare2, Ghidra support
- **Binary Injection**: Multi-language injection payloads and techniques
- **LLVM Binary Lifting**: RetDec and McSema integration
- **Kernel Debugging**: IOCTL detection, firmware extraction, advanced breakpoints
- **Web Security Testing**: SQL injection, XSS, CSRF scanning and fuzzing
- **Package Manager Translation**: Convert between deb, rpm, flatpak, snap, pacman
- **Multi-Distro Container Management**: CentOS, Fedora, Arch, openSUSE containers
- **OS Switching**: Experimental kexec-based OS switching
- **Git Repository Cleanup**: Interactive TUI for large file removal
- **ROP Exploit Demo**: Educational buffer overflow exploitation

### Documentation
- Comprehensive README with examples
- QUICKSTART guide
- REST API documentation
- Security testing guide
- Kernel debugging guide
- TUI documentation
- Multiple example demos

### Infrastructure
- Playwright end-to-end testing
- GitHub Actions CI/CD workflows
- Amazon Q and Copilot agent reviews
- Container support (Docker/Podman)

## [Unreleased]

### Planned
- Enhanced REST API with FastAPI/Uvicorn
- Improved help system with typo tolerance
- Subcommand grouping
- Multiline bash support with backslash continuation
