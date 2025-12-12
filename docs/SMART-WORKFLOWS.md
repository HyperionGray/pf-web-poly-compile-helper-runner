# Smart Workflows Guide

## Overview

Round 2 of integration tightening introduces **smart workflows** - powerful task combinations that demonstrate "doing less, but doing it smart." These workflows combine multiple tools intelligently to accomplish complex security research, development, and testing tasks with minimal commands.

## Philosophy

Instead of running 10 separate commands to analyze a binary, discover vulnerabilities, and generate exploits, you can now run a single smart workflow that orchestrates all these tools together with intelligent defaults and error handling.

## Available Smart Workflows

### 🔍 Vulnerability Discovery

#### `vuln-discover` - Smart Vulnerability Discovery Pipeline

Combines binary analysis, parse function detection, complexity analysis, and exploit information gathering into one comprehensive workflow.

**Usage:**
```bash
pf vuln-discover binary=/path/to/binary
# Or use the quick alias:
pf vd binary=/path/to/binary
```

**What it does:**
1. **Binary Security Analysis** - Checks security features (NX, PIE, RELRO, Stack Canaries)
2. **Automagic Parse Function Detection** - Finds functions that parse untrusted input
3. **Complexity Analysis** - Identifies functions with high cyclomatic complexity (likely bugs)
4. **Exploit Information Gathering** - Collects all data needed for exploitation
5. **ROP Gadget Search** - Finds useful gadgets for ROP chain construction

**Example Output:**
```
╔══════════════════════════════════════════════════════════════╗
║     SMART VULNERABILITY DISCOVERY PIPELINE                   ║
╚══════════════════════════════════════════════════════════════╝

Target: /usr/bin/vulnerable_app

→ Phase 1: Binary Security Analysis
  RELRO:    Partial RELRO
  Stack:    No canary found
  NX:       NX enabled
  PIE:      No PIE (0x400000)

→ Phase 2: Automagic Parse Function Detection
  ✓ Found parse function: parse_input
  ✓ Found parse function: handle_request

→ Phase 3: Complexity Analysis
  ⚠️  High complexity in function: parse_input (CC: 25)
  ⚠️  Long function detected: handle_request (150 lines)

→ Phase 4: Exploit Information Gathering
  Architecture: x86_64
  Symbols: 45 functions
  Writable sections: .data, .bss

→ Phase 5: ROP Gadget Search
  ✓ Found 234 gadgets
```

#### `vuln-discover-and-exploit` - Complete Discovery and Exploitation

Extends `vuln-discover` by also generating ROP chains and exploit templates.

**Usage:**
```bash
pf vuln-discover-and-exploit binary=/path/to/binary
```

**What it does:**
Everything from `vuln-discover`, plus:
6. **ROP Chain Generation** - Builds working ROP chains automatically
7. **Exploit Template Creation** - Generates Python exploit template with pwntools

**Generated Artifacts:**
- `/tmp/vuln_discover_<binary>_summary.txt` - Full analysis report
- `/tmp/rop_chain_<binary>.py` - Generated ROP chain
- `/tmp/exploit_<binary>.py` - Complete exploit template

### 🔒 Secure Build Pipelines

#### `build-secure` - Smart Secure Build Pipeline

Builds your project with automatic security scanning, testing, and optional containerization.

**Usage:**
```bash
# Basic secure build
pf build-secure

# Release build with 8 parallel jobs
pf build-secure release=true jobs=8

# Build and containerize
pf build-secure release=true containerize=true

# Quick alias
pf bs release=true
```

**What it does:**
1. **Detect Build System** - Auto-detects Cargo, Make, CMake, npm, etc.
2. **Build Project** - Runs appropriate build command with optimizations
3. **Security Scan Binaries** - Checks all compiled binaries for security features
4. **Run Tests** - Executes project test suite
5. **Containerize (optional)** - Creates production-ready container

**Supported Build Systems:**
- Rust (Cargo.toml)
- Node.js (package.json)
- Go (go.mod)
- CMake (CMakeLists.txt)
- Make (Makefile)
- Maven (pom.xml)
- And 10+ more

#### `build-secure-web` - Secure Web Application Build

Specialized workflow for web applications with security testing.

**Usage:**
```bash
pf build-secure-web
```

**What it does:**
1. **Build Web App** - Compiles/bundles the web application
2. **Start Test Server** - Launches development server on port 8080
3. **Security Scan** - Checks for SQLi, XSS, CSRF, and other vulnerabilities
4. **Generate Report** - Creates security findings report
5. **Cleanup** - Stops test server gracefully

#### `build-polyglot-smart` - Polyglot Project Builder

Intelligently detects and builds all languages in a multi-language project.

**Usage:**
```bash
pf build-polyglot-smart
```

**Auto-detects and builds:**
- Rust projects
- Node.js/JavaScript
- WASM modules (Rust, C, Fortran, WAT)
- Go projects
- Java/Maven projects
- And more

### 🔬 Debug and Reverse Engineering

#### `debug-deep-dive` - Smart Deep-Dive Debugging

Comprehensive binary analysis and debugging workflow.

**Usage:**
```bash
# Full analysis with interactive debugger
pf debug-deep-dive binary=/path/to/binary interactive=true

# Analysis only (no debugger)
pf debug-deep-dive binary=/path/to/binary

# Analyze specific function
pf debug-deep-dive binary=/path/to/binary function=parse_input

# Quick alias
pf dd binary=/path/to/binary interactive=true
```

**What it does:**
1. **Binary Information** - ELF header, architecture, libraries
2. **Security Feature Analysis** - RELRO, Stack Canaries, NX, PIE, Fortify
3. **Disassembly Preview** - Shows disassembly of specified function
4. **ROP Gadget Analysis** - Finds useful gadgets for exploitation
5. **String Analysis** - Searches for interesting strings (passwords, keys, etc.)
6. **Interactive Debugger (optional)** - Starts GDB/LLDB with pwndbg

**Example:**
```bash
# Quick security analysis
pf dd binary=./vulnerable_app

# Deep dive with debugger
pf dd binary=./vulnerable_app function=main interactive=true
```

#### `lift-analyze-recompile` - Binary Transformation Pipeline

Lifts binary to LLVM IR, optimizes it, and recompiles.

**Usage:**
```bash
pf lift-analyze-recompile binary=/path/to/binary
```

**What it does:**
1. **Binary Lifting** - Converts binary to LLVM IR using RetDec
2. **LLVM IR Analysis** - Inspects the lifted IR
3. **LLVM Optimization** - Applies optimization passes
4. **Recompilation** - Compiles optimized IR back to native binary

**Use Cases:**
- Binary optimization
- Cross-architecture retargeting
- Security analysis via LLVM instrumentation
- Code understanding and documentation

### 🐳 Container Development

#### `dev-containerized` - Containerized Development Workflow

Manages complete container-based development lifecycle.

**Usage:**
```bash
pf dev-containerized
```

**What it does:**
1. **Build Container Images** - Builds all required container images
2. **Start Development Environment** - Launches containers with compose
3. **Run Tests** - Executes containerized test suite

**Follow-up Commands:**
```bash
pf compose-shell           # Open shell in container
pf compose-logs            # View container logs  
pf compose-down            # Stop all containers
```

### ⚡ Kernel Fuzzing

#### `kernel-smart-fuzz` - Smart Kernel Fuzzing Pipeline

Combines automagic analysis with fast in-memory fuzzing for kernel vulnerability discovery.

**Usage:**
```bash
# Full auto-analysis and fuzzing
pf kernel-smart-fuzz binary=/path/to/kernel_module

# Fuzz specific function
pf kernel-smart-fuzz binary=/path/to/kernel_module function=parse_ioctl

# Quick alias
pf ksf binary=/path/to/kernel_module
```

**What it does:**
1. **Automagic Analysis** - Detects parse functions, analyzes complexity
2. **Fast In-Memory Fuzzing** - 100-1000x faster than traditional fuzzing
3. **Vulnerability Detection** - Identifies crashes and security issues

**Benefits:**
- 100-1000x faster than traditional fuzzing
- Automatic target selection
- Loop-back capability for deeper coverage

### 🛡️ Web Security Testing

#### `web-security-full-stack` - Complete Web Security Testing

Comprehensive web application security workflow from build to report.

**Usage:**
```bash
pf web-security-full-stack
# Or use the quick alias:
pf wsfs
```

**What it does:**
1. **Build Web Application** - Compiles all WASM modules and assets
2. **Start Test Server** - Launches server on port 8080
3. **Security Header Analysis** - Checks CSP, HSTS, X-Frame-Options, etc.
4. **Vulnerability Scanning** - Tests for SQLi, XSS, CSRF, Path Traversal, etc.
5. **Comprehensive Fuzzing** - Fuzzes with all payload types
6. **Generate JSON Report** - Creates detailed security report
7. **Cleanup** - Gracefully stops test server

**Vulnerabilities Detected:**
- SQL Injection (error-based and blind)
- Cross-Site Scripting (XSS)
- Cross-Site Request Forgery (CSRF)
- Path Traversal
- OS Command Injection
- XML External Entity (XXE)
- Server-Side Request Forgery (SSRF)
- Security Misconfigurations
- Missing Security Headers

**Output:**
```bash
╔══════════════════════════════════════════════════════════════╗
║     FULL STACK WEB SECURITY TESTING                          ║
╚══════════════════════════════════════════════════════════════╝

→ Phase 1: Building Web Application
  ✓ Rust WASM compiled
  ✓ C WASM compiled
  ✓ Fortran WASM compiled

→ Phase 2: Starting Test Server
  ✓ Server running on http://localhost:8080

→ Phase 3: Security Header Analysis
  ⚠️  Missing: Content-Security-Policy
  ⚠️  Missing: X-Frame-Options
  ✓ Found: X-Content-Type-Options

→ Phase 4: Vulnerability Scanning
  ⚠️  Potential SQLi in /api/search
  ✓ No XSS detected

→ Phase 5: Comprehensive Fuzzing
  ⚠️  Anomaly detected in /api/user

→ Phase 6: Generating JSON Report
  Report saved to /tmp/security_report_20231208_120000.json

→ Cleanup: Stopping Test Server
  ✓ Server stopped

╔══════════════════════════════════════════════════════════════╗
║     WEB SECURITY TESTING COMPLETE                            ║
╚══════════════════════════════════════════════════════════════╝
```

## Quick Reference

### Aliases

Smart workflows include short aliases for quick access:

| Alias | Full Command | Description |
|-------|--------------|-------------|
| `pf vd` | `pf vuln-discover` | Vulnerability discovery |
| `pf bs` | `pf build-secure` | Secure build pipeline |
| `pf dd` | `pf debug-deep-dive` | Deep debugging workflow |
| `pf ksf` | `pf kernel-smart-fuzz` | Kernel fuzzing |
| `pf wsfs` | `pf web-security-full-stack` | Web security testing |

### Common Usage Patterns

#### Binary Security Research
```bash
# Quick vulnerability check
pf vd binary=./target

# Full exploit generation
pf vuln-discover-and-exploit binary=./target

# Interactive debugging
pf dd binary=./target interactive=true
```

#### Secure Development
```bash
# Secure release build
pf bs release=true jobs=8

# Web app with security testing
pf build-secure-web

# Full containerization
pf bs release=true containerize=true
```

#### Web Security
```bash
# Quick security scan
pf security-scan url=http://myapp.local

# Complete testing workflow
pf wsfs

# Focused testing
pf security-fuzz-sqli url=http://myapp.local/api
```

## Integration Benefits

These smart workflows demonstrate the power of tool integration:

1. **Less Manual Work** - One command instead of many
2. **Intelligent Defaults** - Sensible default parameters
3. **Error Handling** - Graceful degradation when tools unavailable
4. **Comprehensive Coverage** - Multiple analysis angles in one go
5. **Reproducible Results** - Consistent workflow every time

## Advanced Usage

### Custom Workflows

You can create your own smart workflows by combining these building blocks in `Pfyfile.smart-workflows.pf` or your own custom `.pf` files.

### Chaining Workflows

Smart workflows can be chained for even more powerful automation:

```bash
# Build, test, and deploy pipeline
pf build-secure release=true containerize=true && \
pf wsfs && \
pf compose-up
```

### CI/CD Integration

Smart workflows are designed for CI/CD integration:

```yaml
# .github/workflows/security.yml
- name: Secure Build and Test
  run: |
    pf build-secure release=true
    pf web-security-full-stack
```

## Comparison: Before vs After

### Before (Manual Process)
```bash
# Binary vulnerability research (14 commands)
pf debug-info binary=./target
pf checksec-file file=./target
pf binary-info binary=./target
pf disassemble binary=./target
pf kernel-parse-detect binary=./target
pf kernel-complexity-analyze binary=./target
pf exploit-info binary=./target
pf rop-find-gadgets binary=./target output=/tmp/gadgets.txt
pf rop-chain-auto binary=./target output=/tmp/chain.py
pf pwn-template-advanced binary=./target output=/tmp/exploit.py
strings ./target | grep -i password
file ./target
ldd ./target
objdump -d ./target
```

### After (Smart Workflow)
```bash
# Same result, one command
pf vuln-discover-and-exploit binary=./target
```

### Before (Web Security Testing)
```bash
# Manual web security testing (10+ commands)
pf web-build-all
node tools/api-server.mjs web 8080 &
sleep 5
pf security-check-headers url=http://localhost:8080
pf security-scan-sqli url=http://localhost:8080
pf security-scan-xss url=http://localhost:8080
pf security-fuzz-sqli url=http://localhost:8080
pf security-fuzz-xss url=http://localhost:8080
pf security-fuzz-traversal url=http://localhost:8080
pf security-report url=http://localhost:8080 > report.json
# manually kill server
```

### After (Smart Workflow)
```bash
# Same result, one command
pf wsfs
```

## Performance

Smart workflows include several performance optimizations:

- **Parallel Execution** - Where safe, tasks run in parallel
- **Caching** - Intermediate results are cached
- **Smart Detection** - Only runs applicable tools
- **Graceful Degradation** - Continues even if optional tools missing

## Troubleshooting

### Workflow Failed

If a smart workflow fails, you can run individual phases:

```bash
# Instead of full workflow
pf vuln-discover binary=./target

# Run phases individually
pf debug-info binary=./target
pf kernel-parse-detect binary=./target
pf kernel-complexity-analyze binary=./target
```

### Missing Tools

Smart workflows gracefully handle missing tools:

```
→ Phase 3: Complexity Analysis
  ℹ️  Complexity analysis skipped (tool not installed)
```

To install missing tools:
```bash
pf install-exploit-tools        # Exploit development tools
pf install-debuggers            # GDB, LLDB, pwndbg
pf install-security-tools       # Security scanning tools
```

### Verbose Output

For debugging, examine the workflow scripts in:
```
/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/Pfyfile.smart-workflows.pf
```

## Next Steps

1. **Try the workflows** - Start with `pf vd` or `pf bs`
2. **Customize parameters** - All workflows accept optional parameters
3. **Create your own** - Study the patterns and create custom workflows
4. **Integrate into CI/CD** - Use in your automation pipelines

## Summary

Smart workflows represent Round 2 of integration tightening - doing less, but doing it smarter. By combining tools intelligently, we reduce complexity while increasing power and usability.

**Key Takeaway:** Instead of remembering 50 commands, learn 5 smart workflows that orchestrate everything for you.
