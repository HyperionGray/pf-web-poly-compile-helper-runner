# Full review: `./deb/` (with root/project alignment)

Date: 2026-04-16

## Scope reviewed

- Root runner/layout used for packaging compatibility:
  - `/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/pf-runner-full/`
  - `/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/pf.sh`
  - `/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/test_installers.sh`
- Debian packaging directory:
  - `/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/deb/`

## Baseline validation before changes

- Ran installer baseline:
  - `./test_installers.sh`
- Result:
  - Fails early at repo wrapper (`pf -V failed`) due pre-existing Python runtime/dependency environment constraints.
  - This was pre-existing and not introduced by this review.

## Findings and fixes applied in `./deb/`

### 1) Entrypoint mismatch with current runner

- File: `deb/build-deb.sh`
- Finding:
  - Package wrapper was calling `/usr/local/lib/pf-runner/pf_main.py` directly.
  - Current project runner path uses wrapper/runtime flow (`pf_universal` + `pf_runtime.sh`) for Python resolution and env setup.
- Fix:
  - Wrapper now executes `/usr/local/lib/pf-runner/pf_universal`.
- Status: complete.

### 2) Runtime dependency under-installation in postinst

- File: `deb/postinst`
- Finding:
  - Script only installed `lark` + `json5`, while current runtime checks/use can require `fabric`, `typer`, and `rich`.
- Fix:
  - Expanded `pip3 install` set to:
    - `lark>=1.1.0,<2.0`
    - `json5>=0.13.0`
    - `fabric>=3.2.0`
    - `typer>=0.12.0`
    - `rich>=13.0.0`
- Status: complete.

### 3) Python version metadata drift

- File: `deb/control`
- Finding:
  - Control file had `python3 (>= 3.8)` while runner metadata in `pf-runner-full/pyproject.toml` requires `>=3.10`.
- Fix:
  - Updated to `python3 (>= 3.10)`.
- Status: complete.

### 4) Packaging metadata cleanup

- Files: `deb/changelog`, `deb/copyright`
- Findings:
  - `changelog` had literal `$(date -R)` placeholder.
  - Copyright `Source` pointed to placeholder example URL.
- Fixes:
  - Replaced changelog trailer date with concrete RFC 2822 date.
  - Updated source URL to this repository.
- Status: complete.

### 5) Documentation alignment

- File: `deb/README.md`
- Finding:
  - Package behavior/deps text was outdated relative to current runner entrypoint/runtime deps.
- Fix:
  - Updated docs to reflect `pf_universal` launcher and dependency set.
- Status: complete.

## Items reviewed but not fully unified in this round

These were identified and are now explicitly marked:

1. `deb/` currently mixes two packaging styles:
   - standalone `build-deb.sh`/`control` flow (single package `pf-runner`, `/usr/local` layout)
   - debhelper-style assets (`rules`, `pf-runner-core.*`) oriented around `pf-runner-core` naming and `/usr` layout.
2. The current changes keep behavior working/aligned for the active `build-deb.sh` path and its installed artifacts.
3. A full unification to one canonical Debian packaging pipeline (single-source `control`, scripts, install prefix, package names) is still pending.

Status: **partially complete by design for this round; explicitly marked**.

## Post-change verification performed

- Re-ran packaging build command:
  - `./deb/build-deb.sh`
- Verified built package metadata and file list:
  - package built successfully
  - `/usr/local/bin/pf` wrapper now targets `pf_universal`
  - postinst includes expanded runtime dependency install list

## Conclusion

`./deb/` has been reviewed against current project runner expectations and key compatibility gaps were fixed.  
Remaining work (full packaging-pipeline unification) is explicitly marked above so scope is clear and tracked.
