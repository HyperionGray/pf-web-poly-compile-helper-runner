# pf task audit — Ubuntu 24.04 (root) — 2026-01-24

Environment:
- OS: Ubuntu 24.04.3 LTS (noble)
- User: root (UID 0)

This started as a documentation-first pass: smoke-run tasks to see what breaks, plus a longer pass over `install*` tasks. During follow-up reruns, a few “small but high-impact” fixes were applied where they clearly improved reliability:
- Runner fixes (bash parsing/execution, polyglot `@file` behavior, multiline `shell |` blocks, nested `pf` calls).
- A couple task fixes for correctness/paths (notably `install-radare2` and `install-snowman`).

## What was run

Initial smoke (non-install tasks; short timeout):

`python3 scripts/pf_task_audit.py --timeout 3 --exclude '^install($|-)' --out-dir task-audit/2026-01-24-ubuntu24-root-smoke`

Initial install pass (install tasks; longer timeout):

`python3 scripts/pf_task_audit.py --timeout 600 --include '^install($|-)' --exclude '^install$|^install-all$' --out-dir task-audit/2026-01-24-ubuntu24-root-install`

Manual installer smoke (native install into a temp prefix): `./pf-runner-full/pf_universal run install-smoke-test` (passed).

Reruns after runner/task fixes:
- `python3 scripts/pf_task_audit.py --timeout 3 --exclude '^install($|-)' --out-dir task-audit/2026-01-24-ubuntu24-root-smoke-rerun`
- `python3 scripts/pf_task_audit.py --timeout 600 --include '^install($|-)' --exclude '^install$|^install-all$' --out-dir task-audit/2026-01-24-ubuntu24-root-install-rerun`
- `python3 scripts/pf_task_audit.py --timeout 3 --exclude '^install($|-)' --out-dir task-audit/2026-01-24-ubuntu24-root-smoke-after-fixes`
- `python3 scripts/pf_task_audit.py --timeout 600 --include '^install($|-)' --exclude '^install$|^install-all$' --out-dir task-audit/2026-01-24-ubuntu24-root-install-after-fixes`

## Results

Smoke (non-install; 505 evaluated, 539 loaded; `install*` excluded):
- Initial: `task-audit/2026-01-24-ubuntu24-root-smoke/` → ok 198 / fail 256 / timeout 22 / skipped 29
- After runner fixes: `task-audit/2026-01-24-ubuntu24-root-smoke-rerun/` → ok 210 / fail 244 / timeout 22 / skipped 29
- After runner+task fixes: `task-audit/2026-01-24-ubuntu24-root-smoke-after-fixes/` → ok 209 / fail 244 / timeout 23 / skipped 29

Install (32 evaluated; `install*` included, excludes `install` + `install-all`):
- Initial: `task-audit/2026-01-24-ubuntu24-root-install/` → ok 20 / fail 10 / skipped 2
- After runner fixes: `task-audit/2026-01-24-ubuntu24-root-install-rerun/` → ok 21 / fail 9 / skipped 2
- After runner+task fixes: `task-audit/2026-01-24-ubuntu24-root-install-after-fixes/` → ok 20 / fail 10 / skipped 2

Note: the “after fixes” install run has different failures than the initial run (some aggregate `install-*` tasks now fail correctly because nested `pf ...` calls run real subtasks).

See:
- `task-audit/2026-01-24-ubuntu24-root-smoke/SUMMARY.md`
- `task-audit/2026-01-24-ubuntu24-root-smoke/results.json`
- `task-audit/2026-01-24-ubuntu24-root-install/SUMMARY.md`
- `task-audit/2026-01-24-ubuntu24-root-install/results.json`
- `task-audit/2026-01-24-ubuntu24-root-smoke-rerun/SUMMARY.md`
- `task-audit/2026-01-24-ubuntu24-root-smoke-rerun/results.json`
- `task-audit/2026-01-24-ubuntu24-root-install-rerun/SUMMARY.md`
- `task-audit/2026-01-24-ubuntu24-root-install-rerun/results.json`
- `task-audit/2026-01-24-ubuntu24-root-smoke-after-fixes/SUMMARY.md`
- `task-audit/2026-01-24-ubuntu24-root-smoke-after-fixes/results.json`
- `task-audit/2026-01-24-ubuntu24-root-install-after-fixes/SUMMARY.md`
- `task-audit/2026-01-24-ubuntu24-root-install-after-fixes/results.json`

## Safety skips

The audit harness skips:
- OS switching tasks (`pf-files/distro-switching/Pfyfile.os-switching.pf`)
- all gitops tasks (`pf-files/gitops/**`) to avoid mutating the repo during audit
- a small regex list for “obviously destructive” operations (mkfs/dd/reboot/etc.)

## Path / working-dir fixes applied

These are intended to be small, mechanical fixes that make tasks runnable without changing intent:

- `Pfyfile.pf`: `web-build-c-llvm` now creates `../web/llvm/c/` before writing LLVM IR.
- `web-testing/Pfyfile.web.pf`: `build-c-llvm` now creates `../web/llvm/c/` before writing LLVM IR.
- `vuln-hunting/Pfyfile.injection.pf`:
  - `create-injection-payload-rust` no longer relies on a persistent `cd` and copies outputs into `injection/payloads/rust/` under the original working directory.
  - `build-injection-examples`, `clean-injection-examples`, `test-injection-workflow` use `cd ... && ...` so they don’t rely on a persistent working directory.
- `vuln-hunting/Pfyfile.sanitizers.pf`, `debugging/Pfyfile.debug-tools.pf`, `exploit-writing/Pfyfile.exploit.pf`: replaced `~/.local/...` with `$HOME/.local/...` where the runner’s quoting prevented `~` expansion.

## Runner fixes applied

These were needed to make a large number of tasks execute reliably (especially ones with redirects, grouping, and bashisms like `source`):

- Shell execution now uses `bash -lc` and preserves raw command strings for shell-feature commands (redirects/`&&`/`||`/grouping/etc.) instead of re-quoting tokens.
- Polyglot `shell_lang python @file.py` now runs the real file path (keeps imports/relative resources working); similarly, `shell_lang c/cpp @file` compiles from the real source path (keeps relative includes working).
- `shell |` multiline blocks are executed correctly in the installed runner.
- Nested `pf ...` calls inside tasks now resolve to the same runner being executed (prevents accidentally invoking a different `pf` earlier in PATH).

## Install task fixes applied

- `install-radare2`: fixed broken OS-branch logic (`&&`/`||` chaining) so only one branch runs on Ubuntu.
- `install-snowman`:
  - fixed OS-branch logic (`&&`/`||` chaining)
  - fixed CMake source dir (`cmake ../src`)
  - added CMake flags for Linux to avoid MSVC/x64dbg-module CMake errors
  - made clone idempotent by removing `/tmp/snowman-install` before cloning

## Notable install breakages (Ubuntu 24.04/root)

From `task-audit/2026-01-24-ubuntu24-root-install-after-fixes/results.json` (see per-task logs for full output):

- `install-aflplusplus`: clone destination already exists. Log: `task-audit/2026-01-24-ubuntu24-root-install-after-fixes/logs/0219-install-aflplusplus.log`.
- `install-binsider`: upstream cargo build failure (dependency/type mismatch). Log: `task-audit/2026-01-24-ubuntu24-root-install-after-fixes/logs/0223-install-binsider.log`.
- `install-oryx`: missing `dbus-1` dev headers/pkg-config (Rust `libdbus-sys` build). Log: `task-audit/2026-01-24-ubuntu24-root-install-after-fixes/logs/0235-install-oryx.log`.
- `install-rustnet`: crate has no binaries (`cargo install` can’t install it). Log: `task-audit/2026-01-24-ubuntu24-root-install-after-fixes/logs/0243-install-rustnet.log`.
- `install-sysz`: crate not found on crates.io as `sysz`. Log: `task-audit/2026-01-24-ubuntu24-root-install-after-fixes/logs/0250-install-sysz.log`.
- `install-ropper`: Ubuntu 24.04 PEP 668 “externally managed environment” (`pip3 install --user`). Log: `task-audit/2026-01-24-ubuntu24-root-install-after-fixes/logs/0242-install-ropper.log`.
- `install-tui-deps`: this environment has a broken `pip3`/`pip` in `/usr/local/bin` (shebang points to missing venv); once resolved, Ubuntu 24.04 will still hit PEP 668 unless using venv/pipx. Log: `task-audit/2026-01-24-ubuntu24-root-install-after-fixes/logs/0251-install-tui-deps.log`.

Aggregate install tasks (fail because a dependent install task fails):
- `install-all-debug-tools`: fails because one of `install-oryx` / `install-binsider` / `install-rustnet` / `install-sysz` fails (note: `install-radare2` and `install-snowman` now pass). Log: `task-audit/2026-01-24-ubuntu24-root-install-after-fixes/logs/0221-install-all-debug-tools.log`.
- `install-exploit-tools`: fails due to Python/pip tool installs (`install-ropper`). Log: `task-audit/2026-01-24-ubuntu24-root-install-after-fixes/logs/0226-install-exploit-tools.log`.
- `install-fuzzing-tools`: fails due to component install failures (see log). Log: `task-audit/2026-01-24-ubuntu24-root-install-after-fixes/logs/0228-install-fuzzing-tools.log`.

Manual note (outside the install-audit include set):
- `install` task currently calls `install.sh --mode native ...`, but `install.sh` does not accept `--mode`; this prevents `pf install` from working as written.

## Missing repo scripts (smoke run)

Several tasks reference scripts that are not present under `tools/` (examples seen in the smoke run):
- `tools/enhanced-workflows/binary_analyzer.py`
- `tools/enhanced-workflows/report_generator.py`
- `tools/unified-security/exploit_tester.py`
- multiple `tools/sanitizers/*.py` helpers and `tools/sanitizers/demo/*.c`
- `tools/fuzzing/fuzz_with_sanitizer.py`
