# FULL review: `./debian/`

## Scope
- Reviewed `./debian/`
- Reviewed root-level packaging/build references that interact with Debian packaging

## Repository/context checks performed
- Root files and task runner entrypoints reviewed (`./README.md`, `./Pfyfile.pf`, `./pf-runner-full/Makefile`, `./scripts/build-packages.sh`, `./test_installers.sh`)
- Existing Debian packaging variants reviewed (`./debian/`, `./deb/`, `./third-party/archive/debian/`)
- Baseline validation executed before changes:
  - `npm run build` ✅

## `./debian/` file-by-file review

### `debian/control`
- Contains source stanza + split binary package metadata:
  - `pf-runner-core`
  - `pf-runner-langs`
  - `pf-runner-tools`
  - `pf-runner` (metapackage)
- This is metadata only and is **not sufficient by itself** to produce packages.

### `debian/AGENTS.md`, `debian/rules.json5`, `debian/.copilot_rules`
- Policy/instruction files only.
- Do not provide Debian build mechanics.

## Cross-repo compatibility findings
1. `./pf-runner-full/Makefile` still references Debian package artifacts including `./debian/build/pf-runner_*.deb` (from repo root context).
2. `./test_installers.sh` checks `./debian/build/pf-runner_1.0.0.deb` in its Debian package test section.
3. `./scripts/build-packages.sh` uses a `dpkg-buildpackage` flow and expects Debian source-package files such as `./debian/changelog`.
4. Current root `debian/` lacks required executable packaging files and therefore is not complete for current referenced flows.

## Completeness decision
Status: **INCOMPLETE (explicitly marked)**

A completion marker has been added at:
- `./debian/REVIEW_STATUS.md`

This fulfills the requirement to mark incompleteness when full completion cannot be safely delivered in one surgical round without broader packaging refactor/synchronization.

## What would be needed for full completion
1. Port a complete Debian packaging set into `./debian/` (including at least build rules and changelog, plus any required maintainer scripts).
2. Reconcile packaging paths/install layout with current pf runner structure (`pf-runner` symlink -> `pf-runner-full`, no `setup.py` in current runner tree).
3. Build package from `./debian/` and validate install/run smoke tests:
   - package build success
   - `pf -V`
   - `pf list`

## Notes on minimal-change approach taken
- Kept this PR surgical and documentation-focused for the requested review.
- Did not introduce broad packaging rewrites that could break existing parallel packaging paths (`deb/`, `build-packages/`, archived variants) without a dedicated migration round.
