# Full review: `./compose/` vs current pf runner

Date: 2026-04-16  
Repository: `HyperionGray/pf-web-poly-compile-helper-runner`

## Scope reviewed

- Root runtime entrypoints used by the current pf runner:
  - `/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/podman-compose.yml`
  - `/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/pf-files/containers/Pfyfile.containers.pf`
  - `/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/containers/scripts/run-dev.sh`
- Compose area:
  - `/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/compose/docker-compose.yml`
  - `/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/compose/docker-compose.gpu.yml`
  - `/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/compose/quadlet/*`

## What was fixed in this round

1. `compose/docker-compose.yml`
   - Updated `build.context` from `.` to `..` for all services so Dockerfiles under `containers/*` resolve from repo root.
   - Updated bind mounts from `./...` to `../...` where they are intended to mount repository-root content.
   - Updated dev service `PYTHONPATH` from `/workspace/pf-runner` to `/workspace/pf-runner-full` to match the current repository layout.
2. `compose/quadlet/pf-dev-service.container`
   - Updated `PYTHONPATH` to `/workspace/pf-runner-full:${PYTHONPATH}` for the same runner-path alignment.
3. `compose/quadlet/README.md`
   - Corrected pod names and GPU file references to match the actual files present in `compose/quadlet/`.
   - Corrected copy command path to use `compose/quadlet/`.

## Review results (complete vs pending)

### Complete in this round

- Path/layout correctness for compose files relative to repo root.
- pf-runner Python path alignment (`pf-runner-full`) in compose + quadlet dev service.
- Quadlet README accuracy for existing local quadlet filenames.

### Marked pending (cannot be fully closed in one round here)

1. **Runtime execution validation for `compose/` files**
   - The sandbox does not currently provide `podman-compose` (`command not found`), so live `up/down/config` execution for `compose/docker-compose*.yml` could not be run in this environment.
2. **Direct wiring to pf task commands**
   - Current pf tasks (`compose-up`, `compose-down`, etc.) use root `podman-compose.yml`, not `compose/docker-compose.yml`.
   - `compose/` now has corrected paths and runner references, but is still a parallel stack and not the active pf task target.

## Suggested follow-up (next round)

- If `compose/` should be the active stack, update pf tasks/scripts to target `compose/docker-compose.yml` (or add a dedicated `pf compose2-*` command set), then run end-to-end container smoke tests.
- If root `podman-compose.yml` is the intended single source of truth, document `compose/` as legacy/alternate to avoid operator confusion.
