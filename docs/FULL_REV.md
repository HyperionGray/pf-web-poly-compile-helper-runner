# Full review: `containers/` + root integration

Date: 2026-04-16

## Scope reviewed

- `/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/containers/**`
- `/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/pf-files/containers/Pfyfile.containers.pf`
- `/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/pf-files/distro-switching/Pfyfile.os-containers.pf`
- `/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/pf-files/distro-switching/Pfyfile.distro-switch.pf`
- `/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/pf-files/mult-exec/Pfyfile.pe-containers.pf`
- `/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/podman-compose.yml`
- `/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/Pfyfile.pf` (root include path)

## What was validated

- [x] Container-related pf modules parse and list tasks when `PF_PYTHON` is set.
- [x] Root Pfyfile delegates to `pf-files/Pfyfile.pf`, which includes container modules.
- [x] `podman-compose.yml` service names align with container tasks (`api-server`, `pf-runner`, build/debug services).
- [x] Missing quadlet installer script path in task definitions was fixed (see changes below).
- [x] Baseline project build/tests were run before changes (`npm run build`, `npm run test:unit`).

## Issue found and fixed

### Broken task wiring for quadlets

`pf quadlet-install` (and related tasks) called:

- `/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/containers/scripts/install-quadlets.sh`

That file did not exist, causing exit code 127.

### Change made

- Added executable script:
  - `/home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/containers/scripts/install-quadlets.sh`

This script now supports:

- `--install`
- `--remove`
- `--list`
- `--status`

and safely handles environments where `systemctl`/user systemd is unavailable.

## Post-change verification

- [x] `PF_PYTHON=/usr/bin/python3 ./pf.sh --file pf-files/containers/Pfyfile.containers.pf quadlet-install`
- [x] `PF_PYTHON=/usr/bin/python3 ./pf.sh --file pf-files/containers/Pfyfile.containers.pf quadlet-list`
- [x] `PF_PYTHON=/usr/bin/python3 ./pf.sh --file pf-files/containers/Pfyfile.containers.pf quadlet-status`
- [x] `PF_PYTHON=/usr/bin/python3 ./pf.sh --file pf-files/containers/Pfyfile.containers.pf quadlet-remove`

## Completion status

- [x] `containers/` reviewed against current pf runner wiring.
- [x] Concrete breakage fixed in this round.
- [x] Work documented in this file.
- [ ] Full container image build matrix (`os` and `pe`) executed end-to-end in this CI sandbox (not completed here due runtime/time and host virtualization dependencies).
