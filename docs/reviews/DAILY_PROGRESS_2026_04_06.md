# Daily Progress: 2026-04-06

## Scope
This note captures the current project direction and the next incremental tasks, based on:
- recent issues and PRs
- README/documentation state
- open/planned work markers in the repository

## Natural project direction
Recent work points to a clear direction: make `pf` a stable base runner with modular task packs, predictable polyglot execution, and simpler installation/distribution.

### Signals from recent issues/PRs
1. **Base + modules architecture is the core direction**
   - Issues #493, #495, #497 focus on restructuring and reducing confusion between default tasks and file-defined tasks.
2. **Predictable multi-language runtime is a top priority**
   - Issue #489 and open work in #501/#503/#505 plus PRs #500/#502/#504 emphasize one shared environment and deterministic behavior across languages.
3. **Installer simplification is active and user-facing**
   - Issue #486 and PR #513 focus on making `.deb` the canonical stable installer path.
4. **Automation-first maintenance loop is established**
   - Daily progress issues and automation labels indicate ongoing small-batch repository steering.

## Gaps and incomplete areas
1. **Packaging reliability gap**
   - `.deb` build failure context in #486 (`debian/changelog` path handling) still needs closure.
2. **Runner UX gap in task discovery/listing**
   - #497 identifies confusing default-task mixing behavior.
3. **Web test ergonomics gap**
   - #505 requests a practical Playwright abstraction layer.
4. **Documented planned items not yet closed**
   - `docs/CHANGELOG.md` lists planned work: FastAPI/Uvicorn API path, typo-tolerant help, subcommand grouping, multiline bash continuation.

## Prioritized next improvements

### Quick wins (do now)
1. **Clean up this directory**
   - Confirm no stray/generated artifacts are tracked in active task directories before each change set.
2. **Fix `.deb` changelog lookup in packaging flow**
   - Add a guarded path-resolution check and fail-fast message with exact expected path.
3. **Split and label task-list output sources**
   - Show "core/default" tasks separately from Pfyfile-sourced tasks.
4. **Land focused env-consistency tests for polyglot execution**
   - Prioritize small deterministic tests that verify shared env behavior across key languages.

### Near-term incremental features (next)
1. **Playwright pf abstraction primitives**
   - Add reusable commands for common flows (click/fill/assert/no-404/no-502/network expectations).
2. **Subcommand/help UX improvements**
   - Implement typo-tolerant help and grouped subcommands from planned backlog.
3. **Stabilize API modernization path**
   - Define minimal migration plan toward FastAPI/Uvicorn without breaking current endpoints.

## Actionable task list
- [ ] clean up this directory
- [ ] patch `debian` packaging scripts to resolve `debian/changelog` robustly and add regression coverage for path resolution
- [ ] implement categorized task listing (core vs Pfyfile source) and update help text/examples
- [ ] merge/complete shared-environment polyglot tests (language matrix + deterministic output ordering)
- [ ] add first Playwright abstraction tasks in `pf-files` and include file-upload + HTTP error checks (404/502)
- [ ] draft a short API migration note (current REST API -> optional FastAPI/Uvicorn path)

## Suggested execution order
1. Packaging fix (`.deb` reliability)
2. Task-list UX clarity
3. Polyglot env-consistency test completion
4. Playwright abstraction starter tasks
5. API modernization planning note

This sequence keeps progress incremental and user-visible while reducing risk.
