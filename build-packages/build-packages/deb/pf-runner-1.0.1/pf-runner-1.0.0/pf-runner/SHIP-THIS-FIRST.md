# pf-runner - Task Runner CLI

**pf** is a lightweight, single-file task runner with a symbol-free DSL for managing development workflows.

## Quick Start

### Installation

```bash
# Install from bundled .deb (preferred, no pip/venv)
sudo dpkg -i build-packages/deb/pf-runner_1.0.0.deb
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
