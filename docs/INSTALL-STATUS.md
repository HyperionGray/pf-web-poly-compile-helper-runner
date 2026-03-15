# Install Status Report (`pf install-status`)

`pf install-status` provides a fast, categorized post-install health report so users can verify what is installed and what is still missing.

## What it checks

- **Core runtime**: `pf`, `python3`, `node`
- **Exploit toolchain**: `pwntools`, `checksec`, `ROPgadget`, `ropper`
- **Debugging / RE tools**: `oryx`, `binsider`, `r2`, `snowman`, `rustnet`, `sysz`, `gdb`, `lldb`
- **Injection utilities**: `patchelf`, `nasm`, `wasm-opt`, `wat2wasm`
- **Fuzzing toolchain**: `afl-fuzz`, `clang`
- **Package managers**: `dpkg`, `rpm`, `flatpak`, `snap`, `pacman`

## Usage

```bash
pf install-status
```

The command prints:

1. Per-tool status with `[OK]` / `[NO]`
2. A summary ratio and percentage
3. Recommended next-step installer tasks based on missing categories

Example follow-up actions:

- `pf install-exploit-tools`
- `pf install-all-debug-tools`
- `pf install-injection-tools`
- `pf install-fuzzing-tools`
- `pf install-pkg-tools`

## Why this exists

Recent installer work improved post-install guidance for individual installers.  
`install-status` closes the loop by giving users a single command to validate the whole environment and quickly see what to run next.
