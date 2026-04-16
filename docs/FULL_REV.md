# Full Review: `pf-runner-full/`

- Date: 2026-04-16
- Scope reviewed:
  - `pf-runner-full/` runtime, packaging metadata, tests, and docs links
  - Root linkage into current runner (`pf-runner -> pf-runner-full`, `pf.sh`, root `Pfyfile.pf`)

## Completion Status

- [x] Clean up this directory (no new artifacts included in this review change)
- [x] Confirm `pf-runner-full` is the active runner path for the repository
- [x] Validate `pf` entrypoint behavior against current root/task layout
- [x] Verify test coverage in `pf-runner-full/tests`
- [x] Fix completeness gap found during review
- [x] Document results in `docs/FULL_REV.md`

## What was validated

1. **Root -> runner wiring is correct**
   - `pf-runner` is a symlink to `pf-runner-full`
   - `pf.sh` dispatches to `pf-runner-full/pf_universal` (fallback `pf`)
   - `pf-runner-full/pf` and `pf_universal` both route through `pf_runtime.sh` into `pf_main.py`

2. **Current runner behavior works with project task tree**
   - `pf-runner-full/pf version` succeeds
   - `pf-runner-full/pf list` succeeds and lists expected root tasks/modules
   - `pf.sh version` and `pf.sh list` also succeed through the same runtime path

3. **Test suite status**
   - `pf-runner-full/tests`: **89 passed**

## Gap found + fix applied

### Gap
`pf_runtime.sh` requires `fabric`, `lark`, `typer`, `json5`, and `rich`, but `pf-runner-full` default package dependencies only declared the first three (plus API deps). This made dependency metadata incomplete for normal runtime expectations.

### Fix
Added missing runtime dependencies to package metadata:
- `json5>=0.12`
- `rich>=13`

Updated files:
- `pf-runner-full/pyproject.toml`
- `pf-runner-full/pf_runner.egg-info/requires.txt`
- `pf-runner-full/pf_runner.egg-info/PKG-INFO`

## Notes

- The checked-in local venv symlink (`pf-runner-full/.venv/bin/python3 -> /usr/local/bin/python3`) is environment-specific and not relied on for this review. Runtime validation was performed with system Python plus declared dependencies.
