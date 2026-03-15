# Installer CLI Options

This document describes the canonical installer entrypoint and its command-line options.

## Entry Points

- Preferred: `./install.sh`
- Compatibility wrapper: `./scripts/install.sh` (for CI and older automation)

Both entry points run the same installer modules under `scripts/installer/`.

## Common Usage

```bash
# Show all options
./install.sh --help

# Native install to a user prefix
./install.sh --mode native --prefix ~/.local

# Container install using podman
./install.sh --mode container --runtime podman
```

## New Inspection/Guidance Flags

### `--dry-run`

Prints an execution plan and safety checks without modifying files or installing anything.

```bash
./install.sh --dry-run --mode native --prefix ~/.local --skip-deps
./install.sh --dry-run --mode container --runtime podman
```

The output includes:
- selected mode and prefix
- detected OS
- whether root privileges would be required
- planned install/build steps

### `--post-install-help`

Prints post-install usage guidance and exits (no install performed).

```bash
./install.sh --post-install-help --mode native --prefix ~/.local
./install.sh --post-install-help --mode container --runtime podman
```

This is useful after installation, in CI logs, or when validating onboarding instructions.

## Verification

A lightweight CLI regression script is available at:

```bash
tests/installation/test_install_cli.sh
```

It verifies:
- `--help` includes current flags
- `--post-install-help` prints actionable commands
- `--dry-run` prints mode-specific plans
