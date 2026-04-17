# FULL VMKit Images Review

Date: 2026-04-16
Repository: `HyperionGray/pf-web-poly-compile-helper-runner`
Scope: review of `./vmkit-images/` with root-level PF/PE integration checks.

## What was reviewed

- Root integration paths that consume `vmkit-images/`:
  - `scripts/pe/vmkit-setup.sh`
  - `scripts/pe/vmkit-run.sh`
  - `scripts/pe/vmkit-analyze.sh`
  - `pf-files/Pfyfile.pe.pf`
  - `pf-files/mult-exec/Pfyfile.pe-containers.pf`
  - `containers/dockerfiles/Dockerfile.pe-vmkit`
  - `docs/PE-EXECUTION.md`
- Directory contents in `vmkit-images/`:
  - `reactos.qcow2`
  - `minimal.qcow2`
  - `reactos-livecd.iso.REMOVED.git-id`

## Findings

1. `vmkit-images/` naming is aligned with the current VMKit runner expectations:
   - runtime default image: `/vmkit/images/reactos.qcow2`
   - setup creates/uses `reactos.qcow2` and `minimal.qcow2`
2. ReactOS ISO is intentionally not committed; this is explicitly marked by:
   - `vmkit-images/reactos-livecd.iso.REMOVED.git-id`
3. PF VMKit command surface is present and wired (`install-vmkit`, `setup-vmkit`, `run-vmkit`, `analyze-vmkit`).
4. Integration fix applied: VMKit helper scripts used by PF tasks were missing execute permissions:
   - `scripts/pe/vmkit-run.sh`
   - `scripts/pe/vmkit-analyze.sh`
   These now have executable permissions so PF task delegation works as intended.

## Completeness status for `vmkit-images/`

- `reactos.qcow2`: present
- `minimal.qcow2`: present
- `reactos-livecd.iso`: not present in git, **explicitly marked as removed** by `.REMOVED.git-id` marker

Status: **Complete for repository-tracked VMKit assets**, with ISO absence explicitly marked.

## Validation performed

- `npm run build` (pass)
- `npm run test:unit` (pre-existing unrelated failures exist in this repository baseline)
- `node tests/containerization/pe-containers.test.mjs` (contains pre-existing unrelated failures)
- `PF_PYTHON=/usr/bin/python3 ./pf.sh pe usage` (pass)
- Added focused review test:
  - `node tests/containerization/vmkit-images-review.test.mjs`

## Notes

- To regenerate/refresh VMKit images and fetch ReactOS ISO during setup flow, run:
  - `PF_PYTHON=/usr/bin/python3 ./pf.sh pe setup-vmkit`
