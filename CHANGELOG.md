# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Complete CI/CD review workflow with documentation analysis
- CODE_OF_CONDUCT.md and SECURITY.md documentation files
- Build script in package.json for proper CI/CD integration

### Fixed
- Cleaned up CONTRIBUTING.md to remove duplication and improve structure
- Resolved CHANGELOG.md merge conflicts and consolidation

### Planned
- Enhanced REST API with FastAPI/Uvicorn
- Improved help system with typo tolerance
- Subcommand grouping
- Multiline bash support with backslash continuation

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
- **Interactive TUI**: Beautiful text-based interface for task management
- **Debugging & Reverse Engineering**: GDB, LLDB, and pwndbg integration

### Changed
- Simplified installation to container-first approach with `./install.sh`
- Legacy host-based installer moved to `bak/install-legacy.sh`

### Documentation
- Comprehensive README with examples
- QUICKSTART guide for new users
- API documentation for REST endpoints
- Security testing guide
- Binary injection guide
- LLVM lifting guide
- Kernel debugging guide
- TUI documentation
- Package manager guide

### Features

#### pf Task Runner
- **Symbol-free DSL**: Clean, readable task definitions without special characters
- **Polyglot Shell Support**: Execute code in 40+ languages inline
- **Build System Integration**: Native support for Make, CMake, Meson, Cargo, Go, Autotools, Just
- **Remote Execution**: SSH-based parallel task execution across multiple hosts
- **Parameter Interpolation**: Dynamic task configuration with environment variables
- **Modular Configuration**: Include and extend task files
- **Interactive Help**: Built-in documentation and task discovery

#### WebAssembly Development
- **Multi-Language Compilation**: Rust (wasm-pack), C (Emscripten), Fortran (LFortran), WAT (WABT)
- **Automagic Builder**: Intelligent project detection and build system selection
- **Container-Based Builds**: Isolated compilation environments
- **Performance Optimization**: Size and speed optimization for WASM modules

#### REST API & Web Interface
- **RESTful Endpoints**: Complete API for project and task management
- **WebSocket Support**: Real-time build status and log streaming
- **Multi-Project Support**: Manage multiple projects simultaneously
- **Build Artifact Management**: Download and manage compiled outputs

#### Security & Reverse Engineering
- **Binary Injection Framework**: Multi-language payload injection (Rust, C, Fortran, WASM, LLVM IR)
- **LLVM Binary Lifting**: Convert x86/x64 binaries to LLVM IR using RetDec and McSema
- **Kernel Debugging**: Parse function detection, complexity analysis, in-memory fuzzing
- **Web Security Testing**: Automated vulnerability scanning (SQL injection, XSS, CSRF)
- **Debugging Tools Integration**: GDB, LLDB, pwndbg, radare2, Ghidra, Rizin

#### Container & Package Management
- **Multi-Distro Containers**: Lightweight containers for CentOS, Fedora, Arch, openSUSE
- **Package Format Translation**: Convert between deb, rpm, flatpak, snap, pacman
- **Artifact Extraction**: Extract packages to host filesystem
- **Dependency Resolution**: Automatic dependency handling

#### Development Tools
- **Interactive TUI**: Rich terminal interface for task management and execution
- **Git Repository Cleanup**: Remove large files from git history with interactive selection
- **OS Switching**: Experimental kexec-based OS switching (educational)
- **ROP Exploit Demo**: Educational framework for buffer overflow exploitation

### Technical Implementation

#### Architecture
- **Container-First Design**: Podman quadlets and compose integration
- **Modular Task System**: Extensible task definition framework
- **Language Agnostic**: Support for 40+ programming languages
- **Cross-Platform**: Linux primary, macOS compatible

#### Performance
- **Parallel Execution**: Multi-host SSH-based task execution
- **Efficient Builds**: Optimized compilation pipelines
- **Resource Management**: Container resource limits and isolation
- **Caching**: Build artifact and dependency caching

#### Security
- **Sandboxed Execution**: Container-based isolation for dangerous operations
- **Privilege Separation**: Minimal privilege requirements
- **Audit Logging**: Comprehensive operation logging
- **Secure Defaults**: Safe configuration out of the box

---

For more details, see the [documentation](README.md) and [QUICKSTART guide](QUICKSTART.md).