# Installer Prerequisites Check

Use `pf install-prerequisites-check` before running installer tasks to confirm your environment is ready.

## Why this exists

Installer tasks can fail for avoidable reasons (missing `python3`, `git`, or shell tooling).  
This check gives a quick preflight result so users can fix prerequisites first.

## Command

```bash
pf install-prerequisites-check
# alias:
pf install-check
```

## What it validates

- **Required commands**: `python3`, `git`, `bash`
- **Optional helper commands** (recommended depending on install path):  
  `sudo`, `dpkg`, `apt-get`, `curl`, `podman`

If required commands are missing, the task exits non-zero and prints actionable guidance.

## Recommended installer flow

```bash
pf install-prerequisites-check
pf install-help
pf install prefix=~/.local
```

For CI or packaging verification:

```bash
pf install-smoke-test
```
