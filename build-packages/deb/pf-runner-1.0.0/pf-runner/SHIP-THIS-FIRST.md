# pf-runner - Task Runner CLI

**pf** is a lightweight, single-file task runner with a symbol-free DSL for managing development workflows.

## Quick Start

### Installation

```bash
# Build the pf-runner container image and wrapper
cd .. && ./install.sh --runtime docker

# Legacy host-only (optional)
pip install --user "fabric>=3.2,<4"
make install-local
```

### Basic Usage

```bash
# List available tasks
pf list

# Run a task
pf <task-name>

# Run with parameters
pf <task-name> param=value

# Install shell completions
pf completions

# Auto-build any project
pf autobuild
```

## Documentation

See [README.md](README.md) for comprehensive documentation.
