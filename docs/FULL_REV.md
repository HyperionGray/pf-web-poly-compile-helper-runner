# Full review: `./scripts/` (and root integration)

Date: 2026-04-16

## Scope reviewed

- `scripts/` tree (shell, Python, and Node/MJS scripts)
- Root integration points that invoke scripts:
  - `package.json` scripts
  - `Pfyfile.pf` / `pf-files/Pfyfile.pf`
  - `tools/validate-pf-tasks.py` (used by `scripts/validate-pf-tasks.sh`)

## What was validated

1. **Baseline project checks (before edits)**
   - `npm run build` ✅
   - `npm run test:unit` ❌ (pre-existing failures)
   - `bash scripts/validate-pf-tasks.sh` ❌ (failed to load PF modules: `No module named 'pf_config'`)

2. **Scripts health checks**
   - Static syntax checks over `scripts/`:
     - `bash -n` for `*.sh/*.bash`
     - `node --check` for `*.mjs/*.js`
     - `python3 -m py_compile` for `*.py`
   - Result after fixes: **80 checked, 0 syntax failures** ✅

3. **CI/CD review script path execution**
   - `npm run cicd:file-analysis` ✅
   - `npm run cicd:review:json` ✅
   - `npm run cicd:test-coverage` ✅ (completes and reports summary)

4. **PF task compatibility validation**
   - `bash scripts/validate-pf-tasks.sh` now loads current PF runner and parses tasks successfully:
     - tasks parsed: **461**
   - Remaining path errors reduced from **74** to **11** (see Outstanding items).

## Changes made

### 1) Fixed PF runner compatibility in task validator
- File: `tools/validate-pf-tasks.py`
- Changes:
  - Removed dependency on legacy `pf_config` module (not present in current runner).
  - Load parser from current runner layout (`pf-runner-full` / `pf-runner`).
  - Anchor parsing to repository root (`chdir(repo_root)`) so include/path resolution matches runner behavior.
  - Improved script path resolution for task commands by checking both task-local and repo-root-relative candidates.

### 2) Fixed broken CI/CD wrapper script
- File: `scripts/ci-cd-review/test-coverage-aggregator.mjs`
- Changes:
  - Removed duplicate in-file class implementation that shadowed imported class and caused:
    - `SyntaxError: Identifier 'TestCoverageAggregator' has already been declared`
  - Kept file as a thin CLI wrapper, consistent with other `scripts/ci-cd-review/*.mjs` wrappers.

## Outstanding items (marked incomplete for follow-up)

The PF task validator now reports **11 real missing script paths** (down from 74). These are outside `./scripts/` and point to missing files referenced by pf task definitions under `pf-files/`:

- `pf-files/enhanced-tasks/Pfyfile.enhanced-workflows.pf`
  - `tools/enhanced-workflows/binary_analyzer.py`
  - `tools/enhanced-workflows/report_generator.py`
- `pf-files/practice/Pfyfile.practice.pf`
  - missing demo shell scripts under `pf-files/practice/demos/practice-binaries/`:
    - `demo_stack_overflow.sh`
    - `demo_format_string.sh`
    - `demo_uaf.sh`
    - `demo_command_injection.sh`
    - `demo_fuzzing.sh`
    - (and repeated references in `demo-all-practice`)

These are not fixed in this pass to keep scope surgical to the scripts review issue, but they are now clearly surfaced and reproducible.

