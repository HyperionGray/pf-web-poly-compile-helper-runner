# Installer Test Suite

## Overview

Installer validation lives in:

```text
tests/installation/test_installer_comprehensive.py
```

The suite is aligned with the current repository layout (`pf-runner-full/`) and validates:

- Direct source execution (`pf_main.py`)
- `install-static.sh --mode python`
- `install-static.sh --mode static` (when `pf-runner-full/pf-static` exists)
- Direct static executable behavior (when built)

## Run the Tests

### One command

```bash
tests/installation/run_installer_tests.sh -v
```

### Or with pytest directly

```bash
pytest tests/installation/test_installer_comprehensive.py -v
```

### Useful subsets

```bash
pytest tests/installation/test_installer_comprehensive.py::TestDirectExecution -v
pytest tests/installation/test_installer_comprehensive.py::TestPythonModeInstall -v
pytest tests/installation/test_installer_comprehensive.py::TestStaticModeInstall -v
```

## Static Binary Notes

Static-mode tests are skipped automatically unless `pf-runner-full/pf-static` exists.

To build it:

```bash
cd pf-runner-full
make build-static
```

## What is Verified

- Installer exits successfully
- Installed `pf` executable is present and executable
- Python-mode install copies runtime files (`pf_main.py`, `pf.lark`, `pf-files/`)
- Static-mode install can run:
  - `pf -V`
  - `pf <path-to-test.pf> list`
  - `pf <path-to-test.pf> hello`

## Notes

- The suite intentionally avoids asserting distribution/package-manager-specific install paths.
- It focuses on portable functionality and installer correctness for local prefix installs.
