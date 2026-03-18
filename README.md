# pf-web-poly-compile-helper-runner
A `pf`-driven task runner and polyglot helper repository with WebAssembly, reverse-engineering, fuzzing, container, and staged execution workflows.
## Start here
- [`QUICKSTART.md`](QUICKSTART.md) — fastest path to running and writing `pf` tasks
- [`docs/README.md`](docs/README.md) — documentation index and feature map
- [`docs/installation/INSTALL.md`](docs/installation/INSTALL.md) — installation reference
- [`docs/PE-EXECUTION.md`](docs/PE-EXECUTION.md) — Windows PE, ReactOS, VMKit, and macOS execution guide
## Useful commands
```bash
pf list
pf modules
pf help
pf pe usage
pf --file pf-files/Pfyfile.pe.pf list
```
## Repository layout
- `pf-files/` — task modules and module entrypoints
- `pf-runner-full/` — canonical Python runner implementation
- `docs/` — guides, feature documentation, CI/CD notes, and reviews
- `bak/` — tracked archive for historical results and deprecated material
- `tests/` — automated validation for the runner and task surface
## Cleanup notes
- GitHub-specific markdown docs now live in `docs/github/`
- historical task-audit output now lives in `bak/task-audit/`
- generated root-level report artifacts were moved into `bak/reports/`
