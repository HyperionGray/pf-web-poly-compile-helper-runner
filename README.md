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
pf help
pf pe usage
pf --file pf-files/Pfyfile.pe.pf list
```
## Pfyfile dependency directives
Declare runtime dependencies once at the top of a Pfyfile (outside tasks):
```pf
dep apt curl jq
dep github owner/repo@main
dep pip "requests>=2.31"
```
These are installed automatically before task execution.
## Repository layout
- `pf-files/` — task modules and module entrypoints
- `pf-files/Pfyfile.pf` — base runner install flow + module includes
- `pf-runner-full/` — canonical Python runner implementation
- `docs/` — guides, feature documentation, CI/CD notes, and reviews
- `bak/` — tracked archive for historical results and deprecated material
- `tests/` — automated validation for the runner and task surface
## Cleanup notes
- GitHub-specific markdown docs now live in `docs/github/`
- historical task-audit output now lives in `bak/task-audit/`
- generated root-level report artifacts were moved into `bak/reports/`
