# Full Review: `./fuzzing/` (and project integration)

Date: 2026-04-16

## Scope reviewed

- `fuzzing/fuzz_target.c`
- `fuzzing/in/seed`
- `fuzzing/AGENTS.md`, `fuzzing/rules.json5`, `fuzzing/.copilot_rules`
- Integration points in:
  - `pf/Pfyfile.fuzzing.pf`
  - `tools/fuzzing/generate-template.sh`
  - `tools/fuzzing/create-examples.sh`
  - `tests/fuzz/pf-fuzzer.test.mjs`

## Findings

### 1) `pf/Pfyfile.fuzzing.pf` path resolution bug (fixed)

When invoked as:

```bash
PF_PYTHON=/usr/bin/python3 ./pf.sh --file pf/Pfyfile.fuzzing.pf <task>
```

`PFY_ROOT` points to `pf/`, so commands like:

- `${PFY_ROOT}/tools/fuzzing/generate-template.sh`
- `${PFY_ROOT}/demos/fuzzing/...`

resolved to non-existent paths (`pf/tools/...`, `pf/demos/...`).

### 2) AFL++ install path bug (fixed)

`install-aflplusplus` used:

```bash
/tmp/fuzzing-${PFY_ROOT:-.}/tools/AFLplusplus
```

which is invalid. This now correctly uses:

```bash
/tmp/fuzzing-tools/AFLplusplus
```

### 3) Template generation with nested absolute output path (fixed)

`tools/fuzzing/generate-template.sh` created only `output_dir`, not the parent dir of explicit `output=...`.
For paths like `/tmp/x/y/fuzz_target.c`, the write could fail. The script now ensures `dirname(output)` is created.

## Validation performed

Baseline (before changes):

- `npm run build` ✅
- `npm run test:fuzz` ✅

Post-fix checks:

- `PF_PYTHON=/usr/bin/python3 ./pf.sh --file pf/Pfyfile.fuzzing.pf list` ✅
- `... generate-libfuzzer-template output=/tmp/pf-fuzzing-review/fuzz_target.c` ✅
- `... create-fuzzing-example` ✅
- `... build-libfuzzer-target source=fuzzing/fuzz_target.c output=/tmp/pf-fuzzing-review-fuzzer` ✅
- `... run-libfuzzer target=/tmp/pf-fuzzing-review-fuzzer corpus=fuzzing/in time=1` ✅

Automated regression added:

- `tests/fuzz/pf-fuzzing-tasks.test.mjs`
- `npm run test:fuzz:tasks`

## Completeness status

- `./fuzzing/` content itself is complete for baseline libFuzzer usage:
  - Harness exists (`fuzz_target.c`)
  - Seed exists (`in/seed`)
- Integration with current pf runner for core fuzzing tasks is now working.
- **Not fully validated in this round** (explicitly marked):
  - `install-sanitizers`, `install-libfuzzer`, `install-aflplusplus`, `install-fuzzing-tools` task execution, because they require privileged package installation/networked toolchain setup.

These installation tasks are still present and documented, but operational validation of apt/sudo-based installation is environment-dependent.
