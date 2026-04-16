# FULL_REV: `./src/` review against current project + pf runner

Date: 2026-04-16

## Scope reviewed
- `src/` tree and its relationship to top-level runtime files (`pf-files/`, `pf/`, `tools/`, `pf-runner-full/`, `Pfyfile.pf`)
- Current pf runner behavior via `python3 pf-runner-full/pf_main.py`
- Task/script path compatibility for enhanced workflow tasks

## Baseline state before changes
- `npm run build` passed.
- `npm run test:unit` had pre-existing failures unrelated to this patch (6 failing suites, 48 failing tests).
- `python3 -m pytest` was unavailable in this environment (pytest not installed).
- `python3 pf-runner-full/pf_main.py list` worked and listed modules/tasks.

## `src/` parity findings
Automated comparison of files under `src/` to same relative paths at repo root:
- Total files scanned: 472
- Same as root: 445
- Different from root: 25
- Present only in `src/`: 2

Most `src/` content is a near-mirror of root. The key functional gap found from this review was in enhanced workflow helpers expected by current pf tasks.

## Functional issues found (and fixed)

### 1) Missing enhanced workflow helper scripts in root `tools/`
Current pf task definitions (`pf-files/enhanced-tasks/Pfyfile.enhanced-workflows.pf`) invoke:
- `tools/enhanced-workflows/binary_analyzer.py`
- `tools/enhanced-workflows/report_generator.py`

These existed in `src/tools/enhanced-workflows/` but were missing at root.

**Fix applied:**
- Added:
  - `tools/enhanced-workflows/binary_analyzer.py`
  - `tools/enhanced-workflows/report_generator.py`

### 2) `enhanced-binary-analysis` task argument compatibility
`enhanced-binary-analysis` passes `--comprehensive`, but delegated analyzer/checksec path did not accept it.

**Fix applied:**
- Updated `tools/enhanced-workflows/binary_analyzer.py` to ignore `--comprehensive` while forwarding supported args.

### 3) `checksec-unified` flag compatibility
Task definitions use `${json:+--json}` while `tools/unified/unified_checksec.py` only supported `--format json`.

**Fix applied:**
- Added `--json` alias support in `tools/unified/unified_checksec.py`.

### 4) Legacy `pf/` task file path mismatch
`pf/Pfyfile.enhanced-workflows.pf` referenced a non-existent `tools/enhanced-workflows/unified_checksec.py`.

**Fix applied:**
- Updated that task to call `tools/unified/unified_checksec.py`.

## Validation after changes
- `python3 tools/enhanced-workflows/binary_analyzer.py /bin/ls --json` ✅
- `python3 tools/enhanced-workflows/report_generator.py --target /bin/ls --output /tmp/full-rev-report.json` ✅
- `python3 pf-runner-full/pf_main.py enhanced-binary-analysis binary=/bin/ls` ✅
- `python3 pf-runner-full/pf_main.py checksec-unified binary=/bin/ls json=true` ✅

## Marked incomplete / follow-up
To keep this change surgical, this review does **not** fully rework the broad enhanced workflow subsystem.
The following are still intentionally incomplete and should be handled in a dedicated follow-up:
- `tools/enhanced-workflows/workflow_orchestrator.py` contains many placeholder implementations (`"... not implemented"`).
- `tools/enhanced-workflows/README.md` lists additional components that are not all present as production-grade implementations.
- Unit test suite still has many pre-existing failures unrelated to this targeted compatibility fix.

Status for this round: **core `src`-to-root enhanced workflow compatibility gaps affecting current pf runner tasks are fixed; broader enhanced workflow completeness remains explicitly marked incomplete.**
