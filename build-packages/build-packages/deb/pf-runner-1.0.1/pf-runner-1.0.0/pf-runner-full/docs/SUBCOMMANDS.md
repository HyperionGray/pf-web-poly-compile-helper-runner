# Subcommands (Task Grouping)

`pf` can organize tasks into **subcommands** based on which `.pf` file a task comes from.

## How it works

- Your main Pfyfile (`pf-files/core/Pfyfile.pf` in this repo) can `include` other `Pfyfile.*.pf` files.
- Each included file becomes a **subcommand group** (derived from the included file’s basename).
- Tasks from that file can be invoked either **directly** or via the **group prefix**.

## Examples

If `pf-files/core/Pfyfile.pf` includes `pf-files/shells/Pfyfile.shells.pf`:

- Direct: `pf bash-cli code="echo hi"`
- Grouped: `pf shells bash-cli code="echo hi"`

If it includes `pf-files/tests/Pfyfile.tests.pf`:

- Direct: `pf test-basic`
- Grouped: `pf tests test-basic`

## Why use subcommands?

- Avoid huge `pf list` output by grouping tasks.
- Keep similarly named tasks in different files while still presenting a clean CLI.
- Make completions and discovery nicer (`pf shells <TAB>`, `pf tests <TAB>`, etc.).
