# pf-web-poly-compile-helper-runner

This repository contains **pf-runner** plus supporting scripts, containers, and task definitions for polyglot compilation and related workflows.

## Layout
- `Pfyfile.pf` – thin shim that includes `pf/Pfyfile.pf`
- `pf/` – structured task packs (always-available, core, distro-switching, containers, etc.)
- `pf-runner/` – pf runner source (Python)
- `demos/`, `examples/`, `tools/`, `fabric/`, `fuzzing/`, `web/` – runnable assets referenced by tasks
- `scripts/` – automation helpers and validation scripts
- `containers/` – container definitions used by container-required tasks
- `third-party/` – vendored binaries (e.g., bfg, keys)

## Quick start

**Installation Options:**

1. **Static executable** (recommended for most users):
   ```bash
   ./install-static.sh [--prefix ~/.local]
   ```

2. **Debian package** (for Debian/Ubuntu systems):
   ```bash
   ./debian/build-deb.sh
   sudo dpkg -i debian/build/*.deb
   ```

3. **Native install** (builds from source):
   ```bash
   ./install.sh [--prefix ~/.local] [--skip-deps]
   ```

**Using pf-runner:**
- List tasks: `pf list` (after install; defaults to `Pfyfile.pf` in repo root)
- Optional dev containers (only for container-required tasks): `bash scripts/manage-containers.sh`
- Read the task DSL + examples: `docs/QUICKSTART.md`
- Validate tasks: `python3 test_all_pf_tasks.py`

**Note:** RPM and Arch package support has been deprecated. See `bak/installers/README.md` for more information.

## Docs

Project documentation lives in `docs/`.
