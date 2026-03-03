# pf task audit — 2026-01-24

This audit smoke-ran all discovered tasks from `pf-files/**` using `pf-runner-full/pf_universal`, with a **3s per-task timeout** and a small safety skip list.

## How it was run

From the repo root:

`python3 pf-files/scripts/pf_task_audit.py --timeout 3 --out-dir pf-files/task-audit/2026-01-24`

Artifacts:
- `pf-files/task-audit/2026-01-24/SUMMARY.md`
- `pf-files/task-audit/2026-01-24/results.json`
- `pf-files/task-audit/2026-01-24/logs/`

## Results (pre-path-fixes)

- ok: 210
- fail: 287
- timeout: 33
- skipped: 9

Skipped tasks:
- `inject-asm-patch` (contains `dd if=...`)
- all `os-*` tasks from `pf-files/distro-switching/Pfyfile.os-switching.pf`

## Common breakage themes

- Missing required parameters (many tasks intentionally require `binary=...`, `target=...`, etc.)
- Missing external tools (examples seen: `afl-clang-lto`, `pip3`, `rustnet`, `sysz`, LLVM pass `.so` files)
- Missing repo scripts under `tools/` (examples seen: `tools/enhanced-workflows/binary_analyzer.py`, `tools/unified-security/exploit_tester.py`, several `tools/sanitizers/*.py`)
- Long-running tasks timing out (servers, installers, container builds)

For specifics, use `results.json` to jump to the per-task log file.

## Path fixes applied after the audit

These are small, mechanical “paths/working-dir” fixes intended to make tasks runnable without changing their higher-level intent:

- `pf-files/web-testing/Pfyfile.web.pf`: `build-c-llvm` now creates `../web/llvm/c/` before writing LLVM IR.
- `pf-files/vuln-hunting/Pfyfile.injection.pf`: fixed non-persistent `cd` usage by moving related commands into `shell |` blocks; replaced `env LD_PRELOAD=... ./target-app` with `LD_PRELOAD=... ./target-app` so the line stays inside the `shell |` block.
- `pf-files/vuln-hunting/Pfyfile.sanitizers.pf`, `pf-files/debugging/Pfyfile.debug-tools.pf`, `pf-files/exploit-writing/Pfyfile.exploit.pf`: replaced `~/.local/...` with `$HOME/.local/...` to work with the current runner’s shell quoting behavior.
- `pf-files/always-available/Pfyfile.tui.pf`: points TUI tasks at `pf-runner-full` instead of `pf-runner`.
- `pf.sh`: now runs `pf-runner-full/pf_universal` (fallbacks to `pf-runner/.pf-venv/bin/pf` if present).

## Spot re-tests (post-path-fixes)

- `./pf.sh --version` now works.
- `./pf-runner-full/pf_universal run build-c-llvm` now succeeds.
- `./pf-runner-full/pf_universal run build-injection-examples` now succeeds.
- `test-injection-workflow` now succeeds when `pf` is available in `PATH` (the audit harness provides a shim at `pf-files/task-audit/2026-01-24/bin/pf`).
- `./pf-runner-full/pf_universal run create-sanitizer-wrappers` now succeeds.

