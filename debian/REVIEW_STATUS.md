# debian/ review status

Status: **INCOMPLETE**

This directory was reviewed against the current repository state and current pf runner layout.

## What is present
- `control` (source + multi-binary package metadata)
- policy files (`AGENTS.md`, `rules.json5`, `.copilot_rules`)

## Blocking gaps
- Missing required Debian source package files for `dpkg-buildpackage` flow (for example `changelog`, `rules`, and related maintainer scripts).
- No package build entrypoint in `./debian/` (for example `build-deb.sh`), while the repository still has installer/test paths that reference `debian/build/*.deb`.
- Packaging logic known elsewhere in the repo (`deb/` and archived copies) does not cleanly match current pf runner layout without additional synchronization work.

## Next required completion work
1. Add/port a complete, runnable Debian packaging set into `./debian/`.
2. Validate package build with current pf runner tree.
3. Validate install and `pf -V`/`pf list` smoke checks.

See `/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/docs/FULL_REV.md` for the full review and root-level relationship analysis.
