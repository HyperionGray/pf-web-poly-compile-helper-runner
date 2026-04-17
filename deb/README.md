# Debian Package for pf-runner

This directory contains the files needed to build a `.deb` package for pf-runner.

## Building the Package

```bash
# Build with default version (1.0.0)
./build-deb.sh

# Build with specific version
./build-deb.sh 1.2.3

# Canonical package builder entrypoint
./build-packages.sh --version 1.2.3 deb
```

The package will be created at `build/pf-runner_<version>.deb`.

## Installing the Package

```bash
# Install the package
sudo dpkg -i build/pf-runner_1.0.0.deb

# If there are dependency issues, fix them
sudo apt-get install -f

# Verify installation
pf --version
pf list
```

## Package Contents

The `.deb` package includes:
- `/usr/local/lib/pf-runner/` - pf-runner Python library
- `/usr/local/lib/pf-runner/fabric/` - bundled fabric library for SSH support
- `/usr/local/bin/pf` - pf executable wrapper (launches `pf_universal`)
- Python dependencies (lark, json5, fabric, typer, rich) - installed via pip in postinst

## Dependencies

The package depends on:
- `python3` (>= 3.10)
- `python3-pip`
- `git`

It recommends:
- `podman` or `docker.io` for container support

Note: fabric is bundled with the package, so it doesn't need to be installed separately.

## Uninstalling

```bash
sudo dpkg -r pf-runner
```

## Notes

- The package uses `/usr/local` as the installation prefix
- Python dependencies are installed system-wide via pip
- The package is architecture-independent (`all`)
