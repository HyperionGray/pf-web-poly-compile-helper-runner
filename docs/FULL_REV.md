# Full review: `./corpus/` and project-root integration

Date: 2026-04-16

## Scope reviewed
- Repository root layout and runner entrypoints
- `./corpus/` contents and compatibility with current `pf` runner fuzzing paths
- Default fuzzing task wiring in:
  - `pf-files/vuln-hunting/Pfyfile.fuzzing.pf`
  - `pf/Pfyfile.fuzzing.pf`
  - `tools/fuzzing/fuzz_with_sanitizer.py`

## Baseline status (before corpus changes)
- `npm run build`: passes
- `npm run test:unit`: fails in multiple pre-existing suites (grammar/parser/api/sync/package-manager/task-validation)
- `pytest -q`: cannot run in this environment (`pytest` not installed)

These failures are pre-existing and unrelated to `./corpus/`.

## Corpus inventory and review
Files found in `./corpus/`:
- `1f444844b1ca616009c2b0e3564fecc065872b5b`
- `3d637fc604995b51a048db0058a7c210e57a38cc`
- `58e6b3a414a1e090dfc6029add0f3555ccba127f`
- `c845fd5022215c2a6fabcef4951090a59d82bb65`
- `ea31d4b8c018ba8973da1ae57e79df8d9eafdd02`
- `seed`
- `AGENTS.md`
- `rules.json5`
- hidden corpus files used as seed inputs: `.copilot_rules`, `.bish.sqlite`

### Compatibility verification
Validated with current runner and fuzzing helpers:

1) pf runner + libFuzzer task path
```bash
PF_PYTHON=$(command -v python3) ./pf-runner-full/pf \
  --file pf-files/vuln-hunting/Pfyfile.fuzzing.pf \
  run-libfuzzer target=./_fuzzer corpus=./corpus time=1
```
Result: success, corpus discovered and consumed by libFuzzer (`10 files found in ./corpus`).

2) sanitizer corpus runner path
```bash
python3 tools/fuzzing/fuzz_with_sanitizer.py \
  --sanitizer asan --binary /bin/cat --corpus ./corpus \
  --timeout 1 --per-run-timeout 0.2 --crash-dir /tmp/pf-corpus-crashes
```
Result: success (`cases` executed, `crashes: 0`).

## Completeness verdict
- **Runner compatibility**: COMPLETE (current `pf` fuzzing paths accept and run with `./corpus/` as-is).
- **Corpus curation/readability**: PARTIAL.
  - The directory contains hashed/binary seeds whose provenance/purpose is not fully described in-repo.
  - This does not break current runner execution, but it is not self-documenting.

### Marked follow-up (not required to keep runner working)
To make corpus curation fully complete in a future pass:
- Add a `corpus/README.md` that documents seed provenance and intended retention policy.
- Optionally classify files into curated human-readable seeds vs discovered/minimized fuzz artifacts.
