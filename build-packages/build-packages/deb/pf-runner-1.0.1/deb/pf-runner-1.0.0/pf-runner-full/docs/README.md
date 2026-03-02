# pf-runner

`pf` is a tiny Fabric-based task runner with a readable, symbol-free DSL and optional subcommands.

## Where tasks live

- Main entrypoint: `pf-files/core/Pfyfile.pf` (recommended) or `Pfyfile.pf` (legacy fallback)
- Included task files: `pf-files/<category>/Pfyfile.<name>.pf`

## Quick start

```bash
./pf list
./pf run default-task
```

## Subcommands

If you split tasks into `Pfyfile.<name>.pf` files and `include` them, pf can expose them as subcommands:

- Docs: `docs/SUBCOMMANDS.md`
