# FULL review: `./aflfuzz/`

Date: 2026-04-16

## Scope reviewed
- `./aflfuzz/`
- Root `Pfyfile.pf` delegation and fuzzing task sources used by current pf runner
- Relevant fuzzing task definitions under `pf-files/vuln-hunting/Pfyfile.fuzzing.pf` and `pf/Pfyfile.fuzzing.pf`

## What was validated
- Baseline project checks before changes:
  - `npm run build` (passed)
  - `npm run test:unit` (pre-existing unrelated failures)
  - `npm run test:fuzz` (passed)
- `aflfuzz` corpus/output structure is present and readable.
- Recorded AFL command format in `aflfuzz/out/default/fuzzer_setup` is compatible with current `pf afl-fuzz` task model (input dir + output dir + target with `@@`).
- Current root task loading path is through `pf-files/Pfyfile.pf`, which includes `vuln-hunting/Pfyfile.fuzzing.pf`.

## Findings
1. `./aflfuzz/` appears to be a preserved AFL run snapshot (seed + metadata), not a complete active campaign workspace.
2. `aflfuzz/out/default/` currently contains metadata files (`cmdline`, `fuzzer_setup`, `plot_data`) but does not include full result subtrees (for example `queue/`, `crashes/`, `hangs/`).
3. The canonical fuzzing task file (`pf-files/vuln-hunting/Pfyfile.fuzzing.pf`) is already aligned with current runner behavior.
4. A secondary legacy copy (`pf/Pfyfile.fuzzing.pf`) had a bad AFL++ source-build path and was fixed in this round.

## Changes made
- Fixed AFL++ install path logic in:
  - `pf/Pfyfile.fuzzing.pf`
- Added this review document:
  - `docs/FULL_REV.md`

## Completeness status
- **Review completeness:** complete for this round.
- **`aflfuzz` data completeness as a fuzzing campaign:** **incomplete** (metadata snapshot present; full result corpus/artifacts not present).

## Recommended next round (optional)
- If full replay is desired, run a fresh campaign with current task flow, e.g.:
  - `pf afl-fuzz target=./aflfuzz/ls input=./aflfuzz/in output=./aflfuzz/out time=5m`
- Then capture and retain `queue/`, `crashes/`, `hangs/`, and `fuzzer_stats` for a fully complete campaign record.
