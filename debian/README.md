# Debian Package for pf-runner

This directory contains the files needed to build `.deb` packages for pf-runner.

## Building the Package

```bash
# Build with the current changelog version
./build-deb.sh

# Build and set changelog version
./build-deb.sh 1.2.3
```

Packages will be created in `build/`.

## Installing the Package

```bash
# Install the packages
sudo dpkg -i build/pf-runner-core_*.deb build/pf-runner-langs_*.deb build/pf-runner-tools_*.deb build/pf-runner_*.deb

# If there are dependency issues, fix them
sudo apt-get install -f

# Verify installation
pf --version
pf list
```

## Package Contents

The `.deb` packages install:
- `/usr/lib/pf-runner/` - pf-runner Python library
- `/usr/bin/pf` - pf executable wrapper
- Systemd unit files under `/etc/systemd/system/`
- Python dependencies (fabric, lark, typer) - installed via pip in postinst

## Dependencies

The package depends on:
- `python3` (>= 3.8)
- `python3-pip`
- `git`

It recommends:
- `podman` for container support

## Uninstalling

```bash
sudo dpkg -r pf-runner
```

## Notes

- The packages use `/usr` as the installation prefix
- Python dependencies are installed system-wide via pip
- The package is architecture-independent (`all`)
