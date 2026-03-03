# START HERE: pf-web-poly-compile-helper-runner

Welcome! 👋 If you're new to this project, you're in the right place. This guide will help you understand what this project is all about, why it matters, and how to get started—whether you're a developer, security researcher, or just curious about polyglot programming.

---

## 📚 Table of Contents

1. [What Is This Project?](#what-is-this-project)
2. [Why Does This Matter?](#why-does-this-matter)
3. [Who Is This For?](#who-is-this-for)
4. [Quick Start (5 Minutes)](#quick-start-5-minutes)
5. [Technical Overview for Developers](#technical-overview-for-developers)
6. [Deep Dive: Understanding pf](#deep-dive-understanding-pf)
7. [Deep Dive: WebAssembly Compilation](#deep-dive-webassembly-compilation)
8. [Deep Dive: Security & Exploitation Tools](#deep-dive-security--exploitation-tools)
9. [Common Use Cases](#common-use-cases)
10. [Next Steps](#next-steps)

---

## What Is This Project?

**pf-web-poly-compile-helper-runner** is a comprehensive polyglot development environment that combines three powerful capabilities:

1. **pf Task Runner**: A lightweight, symbol-free task automation tool (think "Make" meets "Docker Compose" with polyglot superpowers)
2. **WebAssembly Multi-Language Compiler**: Compile Rust, C, Fortran, and WAT to WebAssembly in a unified workflow
3. **Security Research Toolkit**: Binary analysis, fuzzing, exploit development, and kernel debugging tools

Think of it as your Swiss Army knife for:
- **Building** polyglot applications
- **Automating** development workflows
- **Researching** binary security
- **Testing** web applications
- **Compiling** code to WebAssembly from multiple languages

### The Name Explained

Don't let the long name intimidate you! Here's what each part means:

- **pf**: The core task runner (short and sweet!)
- **web**: WebAssembly compilation support
- **poly**: Multiple programming languages (polyglot)
- **compile-helper**: Tools to make compilation easier
- **runner**: Task execution and automation

**In practice, you'll just use:** `pf <command>` for everything!

---

## Why Does This Matter?

### 🎯 The Problem It Solves

Modern software development involves:
- Multiple programming languages in one project
- Complex build systems (Make, CMake, Cargo, npm, etc.)
- Time-consuming manual tasks
- Security testing and vulnerability research
- WebAssembly compilation from various languages
- Remote deployment and execution

**Traditional solutions are fragmented:** You need separate tools for each task, each with its own syntax and learning curve.

### 💡 The pf Solution

**One tool, one simple syntax, unlimited possibilities:**

```bash
# Automatically detect and build ANY project
pf autobuild

# Compile Rust to WebAssembly
pf web-build-rust

# Run security scan on a web app
pf security-scan url=http://localhost:8080

# Execute Python code inline (no separate file needed!)
pf my-task shell_lang python shell "print('Hello!')"

# Deploy to multiple servers at once
pf --hosts server1:22,server2:22 deploy

# Start interactive debugging session
pf debug binary=./myapp
```

### 🚀 What Makes It Unique?

1. **Polyglot Execution**: Run code in 40+ languages inline, without context switching
2. **Automagic Building**: Automatically detects your project type (Rust, Go, Node.js, CMake, etc.) and builds it
3. **Symbol-Free DSL**: Clean, readable task definitions without cryptic symbols
4. **WebAssembly Pipeline**: Unified workflow for compiling multiple languages to WASM
5. **Security Tools Built-In**: Fuzzing, binary analysis, exploit development, vulnerability scanning
6. **Container Integration**: Seamless Docker/Podman support for isolated environments
7. **Smart Workflows**: Intelligent tool combinations that "just work" for complex tasks

**No other tool combines all of these capabilities in one unified interface.**

---

## Who Is This For?

### 👨‍💻 Software Developers

**You'll benefit if you:**
- Work with multiple programming languages
- Want to automate repetitive tasks
- Need to compile code to WebAssembly
- Work with containerized applications
- Deploy to multiple servers
- Want simpler build automation

**What you'll gain:**
- One tool for all your automation needs
- Faster development workflows
- Easy WebAssembly compilation
- Simplified deployment processes

### 🔒 Security Researchers

**You'll benefit if you:**
- Perform binary analysis and reverse engineering
- Develop exploits or conduct vulnerability research
- Fuzz test applications
- Analyze kernel modules or drivers
- Need ROP chain generation

**What you'll gain:**
- Integrated security toolkit (pwntools, checksec, ROPgadget, AFL++, etc.)
- Automated vulnerability detection
- Binary lifting to LLVM IR
- Fast fuzzing workflows
- Kernel debugging capabilities

### 🎓 Students & Learners

**You'll benefit if you:**
- Want to learn multiple programming languages
- Are studying computer security
- Want to understand WebAssembly
- Need to automate homework or projects

**What you'll gain:**
- Practice with real-world tools
- Learn polyglot programming
- Hands-on security research experience
- Simplified project management

### 🏢 DevOps Engineers

**You'll benefit if you:**
- Manage multiple servers
- Automate deployment pipelines
- Work with CI/CD systems
- Need multi-language build support

**What you'll gain:**
- Unified deployment automation
- Remote execution across multiple hosts
- Container orchestration
- Flexible task definitions

---

## Quick Start (5 Minutes)

Let's get you up and running quickly!

### Step 1: Install pf

**Option A: Quick Install (Recommended)**

```bash
git clone https://github.com/HyperionGray/pf-web-poly-compile-helper-runner.git
cd pf-web-poly-compile-helper-runner
./quick-install.sh
```

**Option B: Container Install**

```bash
./install.sh --runtime podman
```

**Option C: Native Install (No Containers)**

```bash
./install.sh --mode native --prefix ~/.local
```

### Step 2: Verify Installation

```bash
pf --version
pf list  # See all available tasks
```

### Step 3: Try Your First Command

**Build a project automatically:**
```bash
pf autobuild
```

This will auto-detect your project type and build it!

**Or try the interactive interface:**
```bash
pf tui
```

This launches a beautiful text-based interface for browsing and running tasks.

### Step 4: Explore Built-in Tasks

```bash
# List all tasks
pf list

# Run the WebAssembly demo
pf web-build-all
pf web-dev

# Try security scanning
pf security-scan url=http://localhost:8080

# Launch debugging tools
pf tui
```

**That's it!** You're now ready to explore the full capabilities.

---

## Technical Overview for Developers

### Architecture

The project consists of several key components:

```
┌─────────────────────────────────────────────┐
│           pf Task Runner Core               │
│  (Python + Fabric + Lark Parser)            │
└────────────┬────────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────┐      ┌────▼─────┐
│ Build  │      │  Remote  │
│Systems │      │Execution │
└───┬────┘      └────┬─────┘
    │                │
┌───▼────────────────▼─────┐
│   Task DSL Interpreter    │
│   (Pfyfile.pf files)      │
└───────────┬───────────────┘
            │
    ┌───────┴────────┐
    │                │
┌───▼────┐     ┌────▼──────┐
│  WASM  │     │ Security  │
│Compile │     │   Tools   │
└────────┘     └───────────┘
```

### Technology Stack

**Core Runtime:**
- **Python 3.10+**: Main runtime environment
- **Fabric 3.x**: SSH and remote execution
- **Lark**: DSL parser for `.pf` files

**WebAssembly Toolchain:**
- **Rust → WASM**: wasm-pack, wasm-bindgen
- **C → WASM**: Emscripten
- **Fortran → WASM**: LFortran (experimental)
- **WAT → WASM**: WABT (WebAssembly Binary Toolkit)

**Security Tools:**
- **Binary Analysis**: Radare2, Ghidra, Binary Ninja, checksec
- **Fuzzing**: AFL++, libfuzzer, sanitizers (ASan, MSan, UBSan, TSan)
- **Debugging**: GDB, LLDB, pwndbg
- **Exploit Dev**: pwntools, ROPgadget, ropper
- **Binary Lifting**: RetDec, McSema

**Container Infrastructure:**
- **Podman/Docker**: Container runtime
- **Quadlets**: Systemd-integrated containers
- **Multi-arch**: x86_64, ARM support

**Web Stack:**
- **Node.js**: REST API server
- **Express**: Web framework
- **WebSockets**: Real-time updates
- **Playwright**: E2E testing

### Project Structure

```
pf-web-poly-compile-helper-runner/
├── pf-runner/              # Core pf task runner
│   ├── pf.py              # Main Python runner
│   ├── Pfyfile.*.pf       # Modular task definitions
│   └── scripts/           # Helper scripts
├── demos/                 # Example applications
│   ├── pf-web-polyglot-demo-plus-c/  # WASM demo
│   ├── debugging/         # Debug examples
│   ├── binary-lifting/    # LLVM lifting demos
│   ├── rop-exploit/       # ROP exploitation demo
│   └── kernel-debugging/  # Kernel analysis examples
├── tools/                 # Development tools
│   ├── security/          # Security scanners
│   ├── smart-workflows/   # Intelligent workflows
│   └── api-server.mjs     # REST API server
├── containers/            # Container definitions
│   ├── base/             # Ubuntu 24.04 base
│   ├── compilers/        # Language toolchains
│   └── debugger/         # Debug tools
├── tests/                 # Test suite
│   ├── e2e/              # End-to-end tests
│   ├── unit/             # Unit tests
│   └── tui/              # TUI tests
├── docs/                  # Documentation
│   ├── QUICKSTART.md     # Quick start guide
│   ├── SMART-WORKFLOWS.md # Smart workflows
│   └── ...               # Feature-specific docs
└── Pfyfile.pf            # Root task definitions
```

### Key Design Principles

1. **Simplicity**: Symbol-free DSL that's easy to read and write
2. **Modularity**: Split tasks across multiple `.pf` files
3. **Flexibility**: Support for 40+ languages inline
4. **Automation**: Auto-detect build systems and project types
5. **Security**: Built-in security tools and vulnerability scanning
6. **Portability**: Runs natively or in containers
7. **Remote Execution**: SSH support for multi-host deployments

### Prerequisites

**Minimum Requirements:**
- Linux or macOS
- Python 3.10+
- Git

**Optional (for full features):**
- Docker or Podman (for containers)
- Node.js 18+ (for web demo)
- Rust toolchain (for Rust → WASM)
- Emscripten (for C → WASM)

---

## Deep Dive: Understanding pf

### What is pf?

**pf** is a task runner with a clean, symbol-free DSL. It's like Make, but:
- **Easier to read**: No cryptic symbols or special syntax
- **More powerful**: Built-in support for 40+ languages
- **More flexible**: Works with any build system
- **Remote-capable**: Execute tasks on multiple servers via SSH

### Task Definition Syntax

Tasks are defined in `Pfyfile.pf` files using a simple, readable format:

```text
task build-app
  describe Build the application with auto-detection
  autobuild release=true
end

task deploy
  describe Deploy to production server
  shell echo "Deploying application..."
  shell scp ./dist/* user@server:/var/www/app/
  service restart myapp
end

task test-python
  describe Run Python tests inline
  shell_lang python
  shell import pytest
  shell pytest.main(['-v'])
end
```

**Key features:**
- `task <name>`: Define a new task
- `describe`: Human-readable description
- `shell`: Execute shell commands
- `shell_lang`: Set language for polyglot execution
- `autobuild`: Auto-detect and build project
- `service`, `packages`, `directory`: System management
- `end`: Close task definition

### Parameter Passing (4 Ways!)

All of these are equivalent:

```bash
pf deploy version=1.2.3
pf deploy version="1.2.3"
pf deploy --version=1.2.3
pf deploy --version 1.2.3
```

Mix and match as you like:

```bash
pf build mode=release --jobs 8 output="./dist"
```

### Polyglot Execution

Execute code in any language without switching tools:

```text
task data-analysis
  describe Analyze data using multiple languages
  
  # Python for data processing
  shell_lang python
  shell import pandas as pd
  shell df = pd.read_csv('data.csv')
  shell print(df.describe())
  
  # Rust for performance-critical code
  shell [lang:rust] fn main() { println!("Fast processing!"); }
  
  # Go for concurrency
  shell [lang:go] package main; import "fmt"; func main() { fmt.Println("Concurrent!") }
end
```

**Supported languages:** Python, Rust, Go, C, C++, Fortran, Java, JavaScript, Ruby, Lua, Swift, and many more!

### Remote Execution

Run tasks on multiple servers:

```bash
# Single server
pf --host user@server.com:22 deploy

# Multiple servers
pf --hosts user@server1:22,user@server2:22 deploy

# With sudo
pf --host user@server:22 --sudo update-system
```

### Build System Integration

Built-in support for major build systems:

```text
task build-everything
  describe Build using appropriate tool
  
  # Auto-detection
  autobuild
  
  # Or specific tools
  makefile all jobs=4
  cmake . build_dir=build build_type=Release
  cargo build release=true
  go_build output=myapp
  meson compile build
end
```

---

## Deep Dive: WebAssembly Compilation

### Why WebAssembly?

**WebAssembly (WASM)** is a binary instruction format that runs in web browsers at near-native speed. It allows you to:
- Write performance-critical web code in any language
- Run existing C/C++/Rust code in browsers
- Share code between server and client
- Execute code safely in sandboxed environments

### Multi-Language WASM Support

This project makes WASM compilation trivial:

```bash
# Build all languages to WASM
pf web-build-all-wasm

# Individual languages
pf web-build-rust-wasm    # Rust → WASM
pf web-build-c-wasm       # C → WASM
pf web-build-fortran-wasm # Fortran → WASM
pf web-build-wat-wasm     # WAT → WASM
```

### LLVM IR Compilation

Beyond WASM, you can also compile to LLVM Intermediate Representation:

```bash
# Build all to LLVM IR with optimization
pf web-build-all-llvm opt_level=3

# With parallelization (OpenMP)
pf web-build-c-llvm parallel=true

# Custom optimization passes
pf web-build-c-llvm-opt passes="mem2reg,dce,gvn"
```

**Why LLVM IR?**
- **Analysis**: Inspect and analyze compiled code
- **Optimization**: Apply custom optimization passes
- **Transformation**: Retarget to different architectures
- **Security**: Instrument for vulnerability detection

### WebAssembly Demo

The project includes a complete WASM demo:

```bash
# Build all WASM modules
pf web-build-all

# Start development server
pf web-dev

# Open browser to http://localhost:8080
```

This demonstrates:
- Rust WASM modules with wasm-pack
- C code compiled via Emscripten
- Fortran WASM (experimental)
- WAT (WebAssembly Text) assembly
- JavaScript interop
- REST API for build management

### WIT Component Model

Support for WebAssembly Interface Types (WIT):

```bash
# Build WIT component
cd examples/wit-rust-component
pf build-wit-component
```

WIT enables:
- Language-agnostic interfaces
- Component composition
- Type-safe interop between WASM modules

---

## Deep Dive: Security & Exploitation Tools

### Why Security Tools?

Modern software security requires:
- Binary analysis and reverse engineering
- Vulnerability discovery through fuzzing
- Exploit development for research
- Kernel-level debugging
- Web application security testing

**pf integrates all of these** into a unified workflow.

### Binary Analysis

Analyze binaries for security properties:

```bash
# Check binary security features
pf checksec-analyze binary=./myapp

# Lift binary to LLVM IR for analysis
pf lift-binary-retdec binary=./myapp

# Disassemble and inspect
pf disassemble binary=./myapp

# Interactive debugging
pf debug binary=./myapp
```

**Tools included:**
- **checksec**: Security feature detection
- **RetDec**: Binary to LLVM IR lifting
- **GDB/LLDB**: Interactive debugging
- **pwndbg**: Enhanced GDB for exploit development
- **Radare2**: Reverse engineering framework
- **Ghidra**: NSA's reverse engineering suite

### Fuzzing & Sanitizers

Discover vulnerabilities through automated testing:

```bash
# Build with sanitizers
pf build-with-asan source=mycode.c
pf build-with-msan source=mycode.c
pf build-with-ubsan source=mycode.c

# AFL++ fuzzing
pf build-afl-target source=target.c
pf afl-fuzz target=target_afl time=1h

# libfuzzer
pf build-libfuzzer-target source=fuzz_target.c
pf run-libfuzzer target=fuzzer time=60

# Fuzz black-box binaries!
pf lift-and-instrument-binary binary=./closed_source
pf afl-fuzz target=closed_source_afl time=30m
```

**Fuzzing capabilities:**
- **AFL++**: State-of-the-art fuzzer with LLVM instrumentation
- **libfuzzer**: In-process coverage-guided fuzzing
- **Sanitizers**: ASan (memory), MSan (uninitialized), UBSan (undefined behavior), TSan (threads)
- **Binary fuzzing**: Lift closed-source binaries to LLVM IR and fuzz them!

### Exploit Development

Build and test exploits:

```bash
# ROP chain generation
pf rop-gadgets binary=./vulnerable
pf rop-exploit binary=./vulnerable

# Heap exploitation
pf heap-spray-demo

# Smart exploit development
pf smart-exploit-dev binary=./target
```

**Features:**
- **pwntools**: Python exploit development framework
- **ROPgadget**: Automatic ROP chain generation
- **ropper**: Find ROP/JOP/SYS gadgets
- **Practice binaries**: Vulnerable examples for learning

### Kernel Debugging

Advanced kernel-level analysis:

```bash
# Auto-detect parse functions
pf kernel-parse-detect binary=./driver.ko

# Complexity analysis
pf kernel-complexity-analyze binary=./driver.ko

# Fast in-memory fuzzing
pf kernel-fuzz-in-memory binary=./driver.ko

# Complete analysis
pf kernel-automagic-analysis binary=./driver.ko
```

**Capabilities:**
- **Parse function detection**: Automatically find input parsing code
- **Complexity analysis**: Identify high-complexity functions
- **In-memory fuzzing**: 100-1000x faster than traditional fuzzing
- **IOCTL detection**: Find kernel interface handlers

### Web Security Testing

Test web applications for vulnerabilities:

```bash
# Comprehensive security scan
pf security-scan url=http://localhost:8080

# Specific vulnerability checks
pf security-scan-sqli url=http://example.com
pf security-scan-xss url=http://example.com

# Fuzzing
pf security-fuzz url=http://example.com/api
pf security-fuzz-all url=http://example.com

# Complete test suite
pf security-test-all url=http://example.com
```

**Detects:**
- SQL Injection
- Cross-Site Scripting (XSS)
- Cross-Site Request Forgery (CSRF)
- Path Traversal
- Command Injection
- XML External Entity (XXE)
- Server-Side Request Forgery (SSRF)
- Security misconfigurations
- Missing security headers

### Smart Workflows

Intelligent tool combinations that "just work":

```bash
# Complete binary analysis
pf smart-binary-analysis binary=./target

# Intelligent exploit development
pf smart-exploit-dev binary=./vulnerable

# Comprehensive security testing
pf smart-security-test url=http://target.com binary=./backend

# Kernel vulnerability research
pf smart-kernel-analysis binary=./driver.ko
```

**Smart workflows automatically:**
- Select appropriate tools
- Chain multiple analyses
- Provide actionable recommendations
- Handle common edge cases

---

## Common Use Cases

### Use Case 1: Building a Multi-Language Project

**Scenario:** You have a project with Rust backend, Node.js frontend, and C libraries.

```bash
# Auto-detect and build everything
pf autobuild

# Or build specific components
pf autobuild dir=./backend
pf autobuild dir=./frontend
pf autobuild dir=./lib
```

### Use Case 2: WebAssembly Development

**Scenario:** You want to compile Rust and C code to WASM for a web app.

```bash
# Build all WASM modules
pf web-build-all-wasm

# Start development server
pf web-dev

# Run tests
pf web-test
```

### Use Case 3: Security Research

**Scenario:** You need to analyze a binary for vulnerabilities.

```bash
# Check security features
pf checksec-analyze binary=./target

# Lift to LLVM IR for analysis
pf lift-binary-retdec binary=./target

# Fuzz for vulnerabilities
pf lift-and-instrument-binary binary=./target
pf afl-fuzz target=./target_afl time=1h
```

### Use Case 4: Automated Deployment

**Scenario:** Deploy to multiple production servers.

```bash
# Deploy to all servers
pf --hosts server1:22,server2:22,server3:22 deploy

# With different environments
pf --host staging:22 deploy env=staging
pf --host production:22 deploy env=production
```

### Use Case 5: Data Analysis Pipeline

**Scenario:** Process data using Python, analyze with Rust, visualize with Node.js.

```text
task data-pipeline
  describe Complete data processing pipeline
  
  # Fetch data with Python
  shell_lang python
  shell import requests
  shell data = requests.get('https://api.example.com/data').json()
  shell with open('data.json', 'w') as f: json.dump(data, f)
  
  # Process with Rust (for performance)
  shell [lang:rust] @scripts/process_data.rs -- data.json
  
  # Visualize with Node.js
  shell node scripts/visualize.js processed_data.json
end
```

---

## Next Steps

### Learning Path

1. **Start with the basics:**
   - Read [QUICKSTART.md](QUICKSTART.md) for detailed examples
   - Try the `pf tui` interactive interface
   - Run `pf list` to see all available tasks

2. **Explore specific features:**
   - [SMART-WORKFLOWS.md](docs/SMART-WORKFLOWS.md) for intelligent workflows
   - [FUZZING.md](docs/FUZZING.md) for security testing
   - [BINARY-INJECTION.md](docs/BINARY-INJECTION.md) for advanced techniques
   - [KERNEL-DEBUGGING.md](docs/KERNEL-DEBUGGING.md) for kernel research

3. **Try the demos:**
   - WebAssembly demo: `pf web-build-all && pf web-dev`
   - ROP exploit: `pf rop-demo`
   - Kernel debugging: `pf kernel-automagic-analysis`
   - Git cleanup: `pf git-cleanup`

4. **Create your own tasks:**
   - Edit `Pfyfile.pf`
   - Define custom workflows
   - Share with your team

### Documentation Index

**Getting Started:**
- [QUICKSTART.md](QUICKSTART.md) - Comprehensive quick start guide
- [README.md](README.md) - Project overview and reference

**Feature Guides:**
- [SMART-WORKFLOWS.md](docs/SMART-WORKFLOWS.md) - Intelligent tool combinations
- [SUBCOMMANDS.md](docs/SUBCOMMANDS.md) - Task organization
- [ALWAYS-ON-TASKS.md](docs/ALWAYS-ON-TASKS.md) - System-wide tasks
- [REST-API.md](docs/REST-API.md) - REST API server

**Security & Analysis:**
- [FUZZING.md](docs/FUZZING.md) - Fuzzing and sanitizers
- [SECURITY-TESTING.md](docs/SECURITY-TESTING.md) - Web security testing
- [BINARY-INJECTION.md](docs/BINARY-INJECTION.md) - Binary manipulation
- [LLVM-LIFTING.md](docs/LLVM-LIFTING.md) - Binary lifting
- [KERNEL-DEBUGGING.md](docs/KERNEL-DEBUGGING.md) - Kernel analysis

**Advanced Topics:**
- [TUI.md](docs/TUI.md) - Interactive interface
- [GIT-CLEANUP.md](docs/GIT-CLEANUP.md) - Repository maintenance
- [PACKAGE-MANAGER.md](docs/PACKAGE-MANAGER.md) - Package conversion
- [Container Documentation](containers/README.md) - Container infrastructure

**Developer Resources:**
- [pf-runner/README.md](pf-runner/README.md) - Core runner documentation
- [BUILD-HELPERS.md](pf-runner/BUILD-HELPERS.md) - Build system integration
- [LANGS.md](pf-runner/LANGS.md) - Supported languages

### Community & Support

- **Issues**: File bugs or feature requests on GitHub
- **Contributions**: See [CONTRIBUTING.md](CONTRIBUTING.md)
- **Security**: Report vulnerabilities via [SECURITY.md](SECURITY.md)
- **Code of Conduct**: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

### Pro Tips

1. **Use aliases**: Many tasks have short aliases (e.g., `pf ron` for `pf rest-on`)
2. **Mix parameter formats**: Use whatever feels natural (`key=value` or `--key value`)
3. **Try the TUI**: `pf tui` provides an interactive way to explore tasks
4. **Check the help**: Run `pf <task>-help` for task-specific help
5. **Leverage autobuild**: Let pf detect your build system automatically
6. **Use smart workflows**: Combine multiple tools intelligently with `pf smart-*` tasks

---

## Welcome Aboard! 🚀

You now have a solid understanding of what this project does, why it's unique, and how to get started. The best way to learn is by doing, so:

1. **Install pf** following the Quick Start section
2. **Try a few commands** to see it in action
3. **Explore the demos** to understand different use cases
4. **Create your own tasks** for your specific needs

**Remember:** The pf community is here to help. Don't hesitate to:
- Read the documentation
- Ask questions via GitHub issues
- Contribute improvements
- Share your workflows

**Happy coding, and welcome to the polyglot revolution!** ✨
