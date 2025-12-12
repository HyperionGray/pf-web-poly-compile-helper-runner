# pf Quick Start Guide

A comprehensive guide to using the **pf** task runner with examples of all major features and parameter passing formats.

## Table of Contents

1. [Installation](#installation)
2. [Basic Concepts](#basic-concepts)
3. [Parameter Passing - All Formats](#parameter-passing---all-formats)
4. [Task Definition Basics](#task-definition-basics)
5. [Task Aliases (Shortcuts)](#task-aliases-shortcuts)
6. [Working with Parameters](#working-with-parameters)
7. [Environment Variables](#environment-variables)
8. [Shell Commands](#shell-commands)
9. [Polyglot Shell Support](#polyglot-shell-support)
10. [Build System Helpers](#build-system-helpers)
11. [System Management](#system-management)
12. [Remote Execution](#remote-execution)
13. [Multiple Tasks](#multiple-tasks)
14. [Advanced Examples](#advanced-examples)

---

## Installation

### 1. Core pf CLI (container-based, recommended)

From the repository root:

```bash
# Build base + pf-runner images and install ~/.local/bin/pf using podman
./install --runtime podman

# or explicitly
./install.sh --runtime podman
```

This will:
- Build `localhost/pf-base:latest`
- Build `pf-runner:local` (used by the `pf` wrapper)
- Install the wrapper at `~/.local/bin/pf` (unless you pass `--no-wrapper`)

Verify installation:
```bash
pf list
```

### 2. Optional: full containerized web stack

Once `pf` works, you can build the full container suite (API server, debuggers, WASM builders):

```bash
# Build all container images with podman
pf container-build-all

# Or use the higher-level installer (containers + quadlets)
pf install-full runtime=podman
```

For interactive development with containers:
```bash
# Start API server + pf-runner containers
./containers/scripts/run-dev.sh

# Build all WASM modules (Rust/C/Fortran/WAT)
./containers/scripts/run-dev.sh build
```

### 3. Manual host-only installation (legacy)

If you prefer a pure host install without containers:

```bash
pip install --user "fabric>=3.2,<4"
cd pf-runner && make install-local
```

In that mode, `pf` runs directly on the host Python instead of inside a container.

---

## Basic Concepts

**pf** uses a simple DSL defined in `Pfyfile.pf` files to define tasks. Tasks are like functions that can:
- Run shell commands
- Accept parameters
- Set environment variables
- Install packages
- Manage services
- Build projects with various build systems
- Execute remotely via SSH

---

## Parameter Passing - All Formats

One of the most powerful features of pf is its flexible parameter passing. All of these formats are **equally valid** and produce the same result:

### All Supported Formats

```bash
# Format 1: key="value" (with quotes)
pf the-task key="mykey"

# Format 2: key=value (without quotes, if no spaces)
pf the-task key=mykey

# Format 3: --key=value (GNU-style with equals)
pf the-task --key=mykey

# Format 4: --key value (GNU-style with space) 
pf the-task --key mykey
```

**All four formats above are equivalent!** Use whichever style feels most natural or matches your team's conventions.

### Mixing Parameter Formats

You can even mix formats in the same command:

```bash
# Mix different formats - all valid!
pf build-app name=myapp --version 1.2.3 env="production"
pf deploy --host=server1 port=8080 ssl="true"
```

### Multiple Parameters

Pass multiple parameters in any format:

```bash
# All of these work:
pf web-server port=8080 host=localhost debug=true
pf web-server --port 8080 --host localhost --debug true
pf web-server --port=8080 --host=localhost --debug=true
pf web-server port=8080 --host localhost debug="true"
```

### Special Characters in Values

When values contain spaces or special characters, use quotes:

```bash
pf the-task key="my value with spaces"
pf the-task --key="value with spaces"
pf the-task --key "value with spaces"
pf deploy message="Release v1.2.3 - Bug fixes"
```

### Task Definition Example

Here's a task that demonstrates parameter usage:

```text
task the-task
  describe Example task showing parameter usage
  shell echo "Received key: $key"
end
```

You can call this task with any of these:
```bash
pf the-task key="mykey"
pf the-task key=mykey
pf the-task --key=mykey
pf the-task --key mykey
```

All produce the same output:
```
[@local] --> the-task
[@local]$ echo "Received key: mykey"
Received key: mykey
```

---

## Task Definition Basics

### Simple Task

The most basic task runs shell commands:

```text
task hello
  describe Print a greeting message
  shell echo "Hello, World!"
end
```

Run it:
```bash
pf hello
```

### Task with Parameters

Tasks can accept parameters that are interpolated using `$variable` syntax:

```text
task greet
  describe Greet someone by name
  shell echo "Hello, $name!"
end
```

Call it with any format:
```bash
pf greet name=Alice
pf greet --name Alice
pf greet --name=Bob
pf greet name="Charlie Brown"
```

### Task with Multiple Parameters

```text
task create-user
  describe Create a new user account
  shell echo "Creating user: $username"
  shell echo "Email: $email"
  shell echo "Role: $role"
end
```

Call with mixed formats:
```bash
pf create-user username=john --email john@example.com role="admin"
pf create-user --username=jane --email=jane@example.com --role=developer
```

### Task with Aliases (Short Commands)

You can define short aliases for tasks with long names using the `[alias name]` syntax:

```text
task long-complicated-task-name [alias lct]
  describe A task with a short alias
  shell echo "Running the task with params: $param1"
end
```

Now you can call this task using either the full name or the alias:
```bash
# Using the full name
pf long-complicated-task-name param1=value

# Using the alias
pf lct param1=value
```

Both commands are equivalent!

**Multiple Aliases:**

You can define multiple aliases for a single task:

```text
task web-development-server [alias wds|alias=dev]
  describe Start the web development server
  shell npm run dev
end
```

This task can be called as:
- `pf web-development-server`
- `pf wds`
- `pf dev`

**Alias Syntax Formats:**

Both of these syntax forms are supported:
```text
# Space-separated
task my-task [alias m]

# Equals-separated  
task my-task [alias=m]

# Multiple in one block (pipe-separated)
task my-task [alias m|alias=mt]
```

### Task with Default Values

When parameters aren't provided, use bash parameter expansion with a two-step pattern:

```text
task web-server
  describe Start a web server with configurable port
  shell PORT=$port; PORT=${PORT:-8080}; echo "Starting server on port $PORT"
  shell python -m http.server $PORT
end
```

**How it works:**
1. `PORT=$port` - Assign the pf parameter to a shell variable
2. `PORT=${PORT:-8080}` - Apply bash default value expansion
3. Use `$PORT` in subsequent commands

For multi-line tasks:

```text
task build-app
  describe Build application with optional version tag
  shell VERSION=$version
  shell VERSION=${VERSION:-dev}
  shell echo "Building version: $VERSION"
  shell ./build.sh --version="$VERSION"
end
```

Call with or without parameters:
```bash
pf web-server              # Uses default port 8080
pf web-server port=3000    # Uses port 3000
pf web-server --port 9000  # Uses port 9000
```

---

## Working with Parameters

### Parameter Interpolation

Parameters are interpolated using `$param` or `${param}` syntax:

```text
task build-docker
  describe Build and tag a Docker image
  shell docker build -t $name:$version .
  shell docker tag $name:$version $name:latest
  shell echo "Built ${name}:${version} and tagged as ${name}:latest"
end
```

Usage:
```bash
pf build-docker name=myapp version=1.2.3
pf build-docker --name=myapp --version=1.2.3
pf build-docker --name myapp --version 1.2.3
```

### Complex Parameter Values

Parameters can contain paths, URLs, JSON, etc.:

```text
task deploy-config
  describe Deploy configuration to a server
  shell echo "Deploying to: $server"
  shell echo "Config file: $config"
  shell scp $config $server:/etc/myapp/config.yml
end
```

Usage with complex values:
```bash
pf deploy-config server=user@prod.example.com:22 config=/path/to/config.yml
pf deploy-config --server user@prod.example.com:22 --config /path/to/config.yml
pf deploy-config server="user@prod.example.com:22" --config="/path/to/config.yml"
```

### Conditional Logic Based on Parameters

```text
task build-project
  describe Build project in debug or release mode
  shell if [ "$mode" = "release" ]; then
  shell   echo "Building in RELEASE mode"
  shell   cargo build --release
  shell else
  shell   echo "Building in DEBUG mode"
  shell   cargo build
  shell fi
end
```

Usage:
```bash
pf build-project mode=debug
pf build-project --mode release
pf build-project mode="release"
```

---

## Environment Variables

### Setting Environment Variables for a Task

Use the `env` verb to set environment variables for all subsequent commands in the task:

```text
task run-app
  describe Run application with environment variables
  env APP_ENV=production DEBUG=false PORT=8080
  shell echo "Environment: $APP_ENV"
  shell echo "Debug mode: $DEBUG"
  shell ./start-app.sh
end
```

### Combining Env Variables with Parameters

Parameters take precedence over `env` settings:

```text
task start-service
  describe Start service with configurable environment
  env PORT=8080 HOST=localhost
  shell echo "Starting on $HOST:$PORT"
  shell ./service --host=$HOST --port=$PORT
end
```

Usage:
```bash
pf start-service                    # Uses defaults: localhost:8080
pf start-service PORT=9000          # Override port: localhost:9000
pf start-service --HOST 0.0.0.0 --PORT 3000  # Override both
```

### Inline Environment Variables

You can also set environment variables inline with shell commands:

```text
task compile-flags
  describe Compile with custom flags
  shell CC=gcc CFLAGS="-O3 -Wall" make
  shell DEBUG=1 npm run build
end
```

---

## Shell Commands

### Basic Shell Commands

The `shell` verb executes shell commands:

```text
task basic-shell
  describe Run basic shell commands
  shell echo "Current directory: $(pwd)"
  shell ls -la
  shell whoami
end
```

### Multi-line Commands

Use backslash for line continuation:

```text
task complex-command
  describe Run a complex multi-line command
  shell docker run --rm \
          -v $(pwd):/app \
          -w /app \
          -p 8080:8080 \
          myimage:latest
end
```

### Command Chaining

Chain commands with `&&` or `;`:

```text
task build-and-test
  describe Build and test if build succeeds
  shell cargo build && cargo test
  shell echo "Build completed: $(date)"
end
```

### Conditional Commands

```text
task check-dependencies
  describe Check if dependencies are installed
  shell if ! command -v node >/dev/null; then
  shell   echo "Node.js not found, installing..."
  shell   curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
  shell   sudo apt-get install -y nodejs
  shell else
  shell   echo "Node.js is already installed: $(node --version)"
  shell fi
end
```

---

## Polyglot Shell Support

pf supports executing code in 40+ languages inline or from files!

### Setting Language for Multiple Commands

Use `shell_lang` to set the language for subsequent commands:

```text
task python-example
  describe Run Python commands
  shell_lang python
  shell print("Hello from Python!")
  shell import sys; print(f"Python version: {sys.version}")
  shell print("Current directory:", __import__('os').getcwd())
  
  shell_lang bash
  shell echo "Back to bash"
end
```

### Inline Language Specification

Use `[lang:language]` for a single command:

```text
task polyglot-demo
  describe Demonstrate multiple languages
  shell [lang:python] print("Hello from Python")
  shell [lang:rust] fn main() { println!("Hello from Rust!"); }
  shell [lang:go] package main; import "fmt"; func main() { fmt.Println("Hello from Go!") }
  shell echo "And bash too!"
end
```

### External File Execution

Run code from files with `@path/to/file` syntax:

```text
task run-scripts
  describe Run code from external files
  shell [lang:python] @scripts/analyze.py -- --input data.csv
  shell [lang:rust] @src/main.rs -- --verbose
  shell [lang:java] @scripts/Main.java -- arg1 arg2
end
```

### Supported Languages

- **Scripting**: python (py, python3), bash, sh, zsh, fish, lua
- **Compiled**: c (clang), c++ (cpp, cxx, clang++), rust, go (golang), fortran (gfortran)
- **Other**: java (openjdk), java-android, swift, asm (asm86)

### Language with Parameters

Parameters work with polyglot commands:

```text
task analyze-data
  describe Analyze data file with Python
  shell_lang python
  shell import sys
  shell print(f"Analyzing file: $filename")
  shell with open("$filename", "r") as f:
  shell     lines = f.readlines()
  shell     print(f"Total lines: {len(lines)}")
end
```

Usage:
```bash
pf analyze-data filename=data.txt
pf analyze-data --filename /path/to/data.csv
```

---

## Build System Helpers

pf provides native support for many build systems.

### Automagic Builder

The most powerful build helper - automatically detects your project type:

```text
task build
  describe Auto-detect and build project
  autobuild
end

task build-release
  describe Build in release mode with 8 parallel jobs
  autobuild release=true jobs=8
end
```

Usage:
```bash
pf build
pf build-release
pf build release=true          # Inline parameter
pf build --release=true --jobs 16  # Mix formats
```

The `autobuild` verb detects and supports:
- Rust (Cargo.toml)
- Go (go.mod)
- Node.js (package.json)
- Python (setup.py, pyproject.toml)
- CMake (CMakeLists.txt)
- Meson (meson.build)
- Make (Makefile)
- And many more...

### Make

```text
task build-with-make
  describe Build project using Make
  makefile all jobs=4
end

task make-clean
  describe Clean build artifacts
  makefile clean
end
```

Usage:
```bash
pf build-with-make
pf build-with-make jobs=8
pf build-with-make --jobs 12
```

### CMake

```text
task cmake-build
  describe Build with CMake
  cmake . build_dir=build build_type=Release
end

task cmake-debug
  describe Debug build with CMake
  cmake . build_dir=debug build_type=Debug
end
```

Usage:
```bash
pf cmake-build
pf cmake-build build_type=Debug
pf cmake-build --build-type Debug --build-dir my-build
```

### Cargo (Rust)

```text
task cargo-build
  describe Build Rust project
  cargo build
end

task cargo-release
  describe Build Rust project in release mode
  cargo build release=true
end

task cargo-test
  describe Run Rust tests
  cargo test
end
```

Usage:
```bash
pf cargo-build
pf cargo-release
pf cargo-test release=true
pf cargo-build --release=true
```

### Go Build

```text
task go-build
  describe Build Go project
  go_build output=myapp
end

task go-build-static
  describe Build static Go binary
  go_build output=myapp ldflags="-s -w" tags=netgo
end
```

Usage:
```bash
pf go-build
pf go-build output=custom-name
pf go-build --output myapp --ldflags "-s -w"
```

### Meson

```text
task meson-setup
  describe Setup Meson build
  meson setup build
end

task meson-compile
  describe Compile with Meson
  meson compile build
end
```

---

## System Management

### Package Management

```text
task install-packages
  describe Install required packages
  packages install git curl build-essential
end

task remove-old-packages
  describe Remove unnecessary packages
  packages remove old-package1 old-package2
end
```

### Service Management

```text
task start-nginx
  describe Start nginx service
  service start nginx
end

task enable-postgresql
  describe Enable PostgreSQL to start on boot
  service enable postgresql
end

task restart-app
  describe Restart application service
  service restart myapp
end
```

### Directory Operations

```text
task create-directories
  describe Create required directories
  directory /var/www/myapp owner=www-data mode=755
  directory /etc/myapp/conf.d
  directory /var/log/myapp mode=755
end
```

### File Operations

```text
task deploy-config
  describe Deploy configuration files
  copy local_file=config/app.conf remote_file=/etc/myapp/app.conf
  copy local_file=config/nginx.conf remote_file=/etc/nginx/sites-available/myapp
end
```

---

## Remote Execution

pf can execute tasks on remote servers via SSH!

### Single Remote Host

```bash
# Using host parameter
pf deploy --host user@server.com:22

# Using legacy format
pf host=user@server.com:22 deploy
```

### Multiple Remote Hosts

```bash
# Deploy to multiple servers
pf hosts=user@server1.com:22,user@server2.com:22 deploy

# Or with --hosts
pf --hosts user@server1.com:22,user@server2.com:22 deploy
```

### With Environment

```bash
# Use predefined environment (requires ENV_MAP in pf.py)
pf env=prod deploy

# Or
pf --env prod deploy
```

### Remote Task Example

```text
task deploy
  describe Deploy application to server
  shell cd /var/www/myapp
  shell git pull origin main
  shell npm install
  shell npm run build
  service restart myapp
end
```

Run remotely:
```bash
pf --host user@prod.server.com:22 deploy
pf host=user@prod.server.com:22 deploy
```

### With Sudo

```bash
# Run with sudo
pf --host user@server.com:22 --sudo update-system
pf host=user@server.com:22 sudo=true update-system

# Run as specific user
pf --host user@server.com:22 --sudo-user postgres backup-db
pf host=user@server.com:22 sudo_user=postgres backup-db
```

---

## Multiple Tasks

Run multiple tasks in sequence, each with their own parameters:

### Basic Multiple Tasks

```bash
# Run multiple tasks
pf build test deploy

# Each task can have its own parameters
pf build mode=release test coverage=true deploy env=prod
```

### Multiple Tasks with Different Parameters

```text
task build
  describe Build the application
  shell echo "Building in $mode mode"
  shell cargo build ${mode:+--release}
end

task test
  describe Run tests
  shell echo "Running tests (coverage: ${coverage:-false})"
  shell cargo test ${coverage:+--coverage}
end

task deploy
  describe Deploy to environment
  shell echo "Deploying to $env"
  shell ./deploy.sh $env
end
```

Run them all:
```bash
# All three formats work!
pf build mode=release test coverage=true deploy env=staging
pf build --mode=release test --coverage=true deploy --env=staging
pf build --mode release test --coverage true deploy --env staging
```

---

## Advanced Examples

### Full CI/CD Pipeline

```text
task ci-pipeline
  describe Complete CI/CD pipeline
  shell echo "=== Starting CI Pipeline ==="
  
  shell echo "Step 1: Linting"
  shell cargo clippy -- -D warnings
  
  shell echo "Step 2: Building"
  autobuild release=true
  
  shell echo "Step 3: Testing"
  cargo test
  
  shell echo "Step 4: Package"
  shell tar -czf app-${version}.tar.gz target/release/myapp
  
  shell echo "=== Pipeline Complete ==="
end
```

Usage:
```bash
pf ci-pipeline version=1.2.3
pf ci-pipeline --version 2.0.0
```

### Conditional Deployment

```text
task deploy-conditional
  describe Deploy only if tests pass
  shell if cargo test; then
  shell   echo "Tests passed, deploying..."
  shell   ./deploy.sh $environment
  shell else
  shell   echo "Tests failed, aborting deployment"
  shell   exit 1
  shell fi
end
```

Usage:
```bash
pf deploy-conditional environment=staging
pf deploy-conditional --environment production
```

### Database Backup with Parameters

```text
task backup-database
  describe Backup database with timestamp
  env TIMESTAMP=$(date +%Y%m%d_%H%M%S)
  shell echo "Backing up database: $db_name"
  shell pg_dump $db_name > backups/${db_name}_${TIMESTAMP}.sql
  shell echo "Backup saved to: backups/${db_name}_${TIMESTAMP}.sql"
  shell gzip backups/${db_name}_${TIMESTAMP}.sql
end
```

Usage:
```bash
pf backup-database db_name=myapp_db
pf backup-database --db-name myapp_db
pf backup-database db_name="production_db"
```

### Multi-Language Build Pipeline

```text
task full-stack-build
  describe Build full-stack application
  
  shell echo "Building backend (Rust)..."
  shell_lang rust
  shell @backend/src/main.rs
  
  shell echo "Building frontend (TypeScript)..."
  shell cd frontend && npm install && npm run build
  
  shell echo "Running integration tests (Python)..."
  shell_lang python
  shell @tests/integration_tests.py -- --verbose
  
  shell echo "Build complete!"
end
```

### Parameter Validation

```text
task validated-deploy
  describe Deploy with parameter validation
  shell if [ -z "$version" ]; then
  shell   echo "Error: version parameter is required"
  shell   exit 1
  shell fi
  shell if [ -z "$environment" ]; then
  shell   echo "Error: environment parameter is required"
  shell   exit 1
  shell fi
  shell echo "Deploying version $version to $environment"
  shell ./deploy.sh --version=$version --env=$environment
end
```

Usage:
```bash
# This will fail (missing parameters)
pf validated-deploy

# This works
pf validated-deploy version=1.0.0 environment=staging
pf validated-deploy --version 1.0.0 --environment production
```

---

## Summary of Parameter Formats

| Format | Example | Notes |
|--------|---------|-------|
| `key="value"` | `pf task key="my value"` | Use quotes for spaces/special chars |
| `key=value` | `pf task key=value` | No quotes needed for simple values |
| `--key=value` | `pf task --key=value` | GNU-style with equals |
| `--key value` | `pf task --key value` | GNU-style with space |

**All formats are equivalent and can be mixed in the same command!**

---

## 🚀 Most Novel Features

pf isn't just another task runner - it has several unique capabilities that set it apart:

### 1. Polyglot Shell Execution (40+ Languages)

Execute code in dozens of languages inline, without switching contexts:

```bash
# Python inline
pf task shell_lang python
pf task shell print("Hello from Python!")

# Rust inline  
pf task shell [lang:rust] fn main() { println!("Hello from Rust!"); }

# Go inline
pf task shell [lang:go] package main; import "fmt"; func main() { fmt.Println("Hello!") }

# External files
pf task shell [lang:python] @scripts/analyze.py -- --input data.csv
```

### 2. WebAssembly Multi-Language Pipeline

Compile multiple languages to WebAssembly in a unified workflow:

```bash
# Build all languages to WASM
pf web-build-all-wasm

# Individual language builds
pf web-build-rust-wasm    # Rust → WASM via wasm-pack
pf web-build-c-wasm       # C → WASM via Emscripten  
pf web-build-fortran-wasm # Fortran → WASM via LFortran
pf web-build-wat-wasm     # WAT → WASM via wat2wasm

# Also supports LLVM IR compilation
pf web-build-all-llvm opt_level=3 parallel=true
```

### 3. Smart Security Workflows

AI-like intelligent tool selection that reduces cognitive load:

```bash
# Auto-detect target and run appropriate analysis
pf smart-analyze target=/path/to/binary

# Automated exploit development
pf smart-exploit binary=/path/to/binary

# Comprehensive security testing
pf smart-security-test target=http://example.com

# Smart fuzzing with optimal strategy selection
pf smart-fuzz target=/path/to/binary duration=1h
```

### 4. Container & OS Environment Switching

Seamlessly switch between different operating system environments:

```bash
# Container management
pf container-build-all
pf compose-up

# OS environment switching
pf os-container-ubuntu
pf distro-switch

# Quadlet integration (systemd containers)
pf quadlet-install
pf quadlet-enable-all
```

### 5. Integrated Exploit Development

Complete exploit development pipeline built into the task runner:

```bash
# Install exploit development tools
pf install-exploit-tools  # pwntools, checksec, ROPgadget, ropper

# Binary analysis
pf checksec-analyze binary=/path/to/binary
pf rop-chain-auto binary=/path/to/binary

# Heap exploitation demos
pf heap-spray-demo
```

These features make pf unique in the task runner ecosystem - no other tool combines polyglot execution, WASM compilation, smart security workflows, and container integration in one unified interface.

---

## Quick Reference

### Common Commands

```bash
# List all available tasks
pf list

# Run a task
pf task-name

# Run with parameters (all formats work)
pf task-name param=value
pf task-name --param value
pf task-name --param=value

# Run multiple tasks
pf task1 task2 task3

# Run on remote host
pf --host user@server:22 task-name
pf host=user@server:22 task-name

# Run with sudo
pf --host user@server:22 --sudo task-name
pf host=user@server:22 sudo=true task-name
```

### Task File Location

By default, pf looks for `Pfyfile.pf` in the current directory. Specify a different file:

```bash
pf /path/to/custom.pf task-name
pf --file /path/to/custom.pf task-name
```

---

## Next Steps

- Read the full [pf-runner README](pf-runner/README.md) for detailed documentation
- Explore [BUILD-HELPERS.md](pf-runner/BUILD-HELPERS.md) for build system integration
- Check [LANGS.md](pf-runner/LANGS.md) for supported polyglot languages
- See [EXAMPLE-PIPELINE.md](pf-runner/EXAMPLE-PIPELINE.md) for CI/CD examples

---

## Tips and Best Practices

1. **Use `describe`**: Always add descriptions to your tasks for better documentation
2. **Validate parameters**: Check required parameters at the start of tasks
3. **Use defaults**: Provide sensible defaults with `${param:-default}` syntax
4. **Group related tasks**: Use `include` to split tasks into logical files
5. **Choose consistent parameter style**: Pick one format and stick with it (or don't - they all work!)
6. **Test locally first**: Test tasks locally before running on remote hosts
7. **Use `shell_lang`**: Set language once for multiple related commands
8. **Leverage `autobuild`**: Let pf auto-detect build systems when possible

Happy task running! 🚀
