# Installer Doctor

`install-doctor` provides a quick post-install health check for the PF runtime and commonly installed tooling.

## Why this exists

Recent installer improvements provide richer post-install guidance. This command adds a single verification step so users can confirm their environment and get actionable next commands when something is missing.

## Usage

```bash
# Guidance mode (default): always exits 0
pf install-doctor

# Strict mode: exits 1 if any required checks are missing
pf install-doctor strict=true
```

You can also run the underlying script directly:

```bash
bash scripts/installer/install-doctor.sh
bash scripts/installer/install-doctor.sh --strict
```

## What it checks

- Core runtime: `pf`, `python3`, `node`
- Installer verification targets:
  - `checksec`
  - `git-filter-repo`
  - `patchelf`, `nasm`, `wasm-opt`, `wat2wasm`
  - Python module import: `pwn` (pwntools)

## Output model

- `[OK]` lines show detected tools and paths.
- `[MISSING]` lines list gaps.
- A summary and suggested `pf install-*` commands are printed at the end.

## Recommended workflow

1. Run `pf install` (or specific installer tasks).
2. Run `pf install-doctor`.
3. Run any suggested installer commands for missing tools.
4. Re-run `pf install-doctor strict=true` for CI-style validation.
