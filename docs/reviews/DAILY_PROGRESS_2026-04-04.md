# Daily Progress: 2026-04-04

## 1) Natural project direction (from current repo state)

Based on recent commit history (`#498` merged), current open issues/PRs, and README/docs focus, the project direction is:

1. Stabilize the **base `pf` runner UX** and predictable task execution semantics.
2. Expand **polyglot runtime coverage** while preserving a single, shared task environment.
3. Improve **test reliability and automation quality**, especially API and package-manager paths.
4. Continue simplifying toward a **canonical Debian installer** flow.

## 2) Next logical improvements/features

1. Land a reusable **Playwright abstraction layer** for common web checks (404/502/XHR/interaction flows).
2. Close known installer friction (`debian/changelog` packaging path expectations).
3. Reduce runner noise/friction for daily use (task discoverability, grouped defaults vs file-defined tasks).
4. Strengthen CI confidence by converting currently failing suites into green, deterministic checks.

## 3) Actionable tasks aligned to goals

### P0 — Quick wins (incremental, high leverage)

1. **Clean up this directory/task surface first**: confirm docs/task references are discoverable and avoid duplicate guidance paths.
2. Fix and re-enable the currently failing unit suites:
   - `tests/api/api-server.test.mjs`
   - `tests/package-manager/package-manager.test.mjs`
3. Add one concise troubleshooting section to docs for local test prerequisites (`.venv-dev`, required tools).

### P1 — Near-term feature progress

4. Implement first-cut Playwright abstraction helpers with focused tests for:
   - page availability checks (no 404/502)
   - basic interaction primitives
   - expected XHR trigger verification
5. Add/expand polyglot execution tests for requested language matrix with explicit shared-env assertions.

### P2 — Follow-on hardening

6. Finish Debian installer streamlining and remove stale/duplicate packaging flow ambiguity in docs/scripts.
7. Add a small CI health report artifact that summarizes suite pass/fail deltas across recent runs.

## 4) Prioritized execution order

1. Stabilize failing tests (P0.2)  
2. Ship Playwright abstraction MVP (P1.4)  
3. Harden polyglot shared-env validation (P1.5)  
4. Complete Debian installer cleanup (P2.6)  
5. Add CI health trend summary (P2.7)

## Evidence reviewed

- Repo README and docs index (`README.md`, `docs/README.md`, `docs/development/CONTRIBUTING.md`)
- Recent local history (branch head + latest merged commit)
- Recent open issues (language expansion, Playwright abstraction, installer fixes)
- Recent open PRs for daily progress, language work, and installer work
- Current test baseline (`npm run build`, `npm run test:unit`)
