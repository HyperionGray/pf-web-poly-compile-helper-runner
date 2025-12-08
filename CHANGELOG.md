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
- **pf-runner**: Lightweight, single-file task runner with symbol-free DSL
- **Polyglot Shell Support**: Run inline code in 40+ programming languages (Python, Rust, Go, C, C++, Fortran, Java, and more)
- **Build System Helpers**: Native support for Make, CMake, Meson, Cargo, Go, Autotools, and Just
- **Automagic Builder**: Intelligent build system that auto-detects project type
- **WebAssembly Compilation**: Build WASM modules from Rust, C, Fortran, and WAT
- **REST API Server**: Build management via REST endpoints with WebSocket support for real-time updates
- **Binary Injection**: Multi-language payload injection (Rust, C, Fortran, WASM, LLVM IR)
- **LLVM Binary Lifting**: Convert binaries to LLVM IR using RetDec and McSema
- **Kernel Debugging**: Automagic vulnerability discovery with parse function detection and in-memory fuzzing
- **Web Security Testing**: Automated vulnerability detection for SQL injection, XSS, CSRF, and more
- **Package Manager Translation**: Convert packages between deb, rpm, flatpak, snap, and pacman formats
- **Multi-Distro Container Management**: Install packages from Fedora, CentOS, Arch, and openSUSE containers
- **OS Switching**: Experimental kexec-based OS switching
- **Git Repository Cleanup**: Interactive TUI for removing large files from git history
- **ROP Exploit Demo**: Educational framework for buffer overflow exploitation
- **Interactive TUI**: Beautiful text-based interface for task management
- **Debugging & Reverse Engineering**: GDB, LLDB, and pwndbg integration

### Changed
- Simplified installation to container-first approach with `./install.sh`
- Legacy host-based installer moved to `bak/install-legacy.sh`

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

### Security
- Added comprehensive web application security scanning framework
- Implemented security headers checking and CSRF protection verification

## [0.9.0] - 2024-11-01

### Added
- Shell completions for bash and zsh
- Enhanced installation process with single-command setup
- Improved documentation for command-line argument flexibility
- Language specification rules for polyglot shell features

### Changed
- Updated grammar file with comprehensive documentation
- Clarified shell compatibility and variable interpolation

## [0.8.0] - 2024-10-01

### Added
- Initial TUI implementation with rich formatting
- Package manager translation framework
- Distro container management system

### Fixed
- Parameter parsing for multi-value arguments
- Path handling for remote execution

## [0.7.0] - 2024-09-01

### Added
- Binary injection and hooking capabilities
- LLVM binary lifting with RetDec integration
- Kernel debugging and fuzzing framework

### Changed
- Improved container build process
- Enhanced documentation structure

## [0.6.0] - 2024-08-01

### Added
- REST API server for build management
- WebSocket support for real-time updates
- Git repository cleanup tool

### Fixed
- WASM compilation for Fortran sources
- Container networking issues

## [0.5.0] - 2024-07-01

### Added
- Podman Quadlet integration for systemd
- GPU-enabled container support
- ROP exploit demonstration framework

### Changed
- Migrated to Ubuntu 24.04 base containers
- Updated debugging tools integration

## [0.4.0] - 2024-06-01

### Added
- Web application security testing framework
- Automated vulnerability scanning
- Security header verification

## [0.3.0] - 2024-05-01

### Added
- Automagic builder with smart project detection
- Support for 12 build systems
- Release/debug build configurations

## [0.2.0] - 2024-04-01

### Added
- Polyglot shell support for 40+ languages
- Build system helpers (Make, CMake, Cargo, etc.)
- Remote execution via SSH

## [0.1.0] - 2024-03-01

### Added
- Initial release of pf-runner task system
- Symbol-free DSL for task definitions
- WebAssembly compilation demos
- Playwright-based testing framework
- Basic container support

---

For more details, see the [documentation](README.md) and [QUICKSTART guide](QUICKSTART.md).
