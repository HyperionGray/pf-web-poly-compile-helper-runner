# Debian Package for pf-runner

This directory contains the files needed to build a `.deb` package for pf-runner.

## Building the Package

```bash
# Build with default version (1.0.0)
./build-deb.sh

# Build with specific version
./build-deb.sh 1.2.3
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
- `/usr/local/bin/pf` - pf executable wrapper
- Python dependencies (fabric, lark, typer) - installed via pip in postinst

## Dependencies

The package depends on:
- `python3` (>= 3.10)
- `python3-pip`
- `git`

It recommends:
- `podman` or `docker.io` for container support

## Uninstalling

```bash
sudo dpkg -r pf-runner
```

## Notes

- The package uses `/usr/local` as the installation prefix
- Python dependencies are installed system-wide via pip
- The package is architecture-independent (`all`)
