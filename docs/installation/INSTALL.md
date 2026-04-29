# Installation Guide

pf-runner now supports a single installer path: **Debian `.deb` packages**.

## Build the package

```bash
./deb/build-deb.sh 1.0.0
# or legacy wrapper:
./build-packages/build-packages --version 1.0.0 deb
```

This creates a package under `deb/build/`.

## Install

```bash
sudo dpkg -i deb/build/pf-runner_1.0.0.deb
sudo apt-get install -f -y
```

## Verify

```bash
pf --version
pf list
```

## Uninstall

```bash
sudo dpkg -r pf-runner
```

## Notes

- `install.sh`, `install-static.sh`, and `quick-install.sh` are no longer part of the supported installation flow.
- If you do not have a Debian/Ubuntu-compatible environment, use a Debian-compatible container/VM and install via the `.deb` package.
