# Installer Test Suite

This directory contains the maintained installer test suite for the current
repository layout.

## Scope

The tests validate:

- Native installer flow (`./install.sh`)
- Static installer flow (`./install-static.sh`)
- Direct execution (`pf-runner-full/pf_main.py`)
- Basic post-install usability (`pf -V`, `pf list`, task execution)

## Test Files

- `test_installer_comprehensive.py` - Python/pytest integration suite
- `test_installer_round3.sh` - Shell smoke checks for installer scripts
- `test-native-install.sh` - Native install flow test helper
- `run_installer_tests.sh` - Standard test runner entrypoint

## Prerequisites

```bash
python3 -m pip install pytest lark fabric typer json5
```

## Run Tests

Run the maintained installer suite:

```bash
./tests/installation/run_installer_tests.sh -v
```

Run only a subset:

```bash
./tests/installation/run_installer_tests.sh --direct
./tests/installation/run_installer_tests.sh --native
./tests/installation/run_installer_tests.sh --static
```

Run pytest directly:

```bash
python3 -m pytest tests/installation/test_installer_comprehensive.py -v
```

## Static Installer Notes

Static tests are skipped automatically unless `pf-runner-full/pf-static` exists.
Build it with:

```bash
cd pf-runner-full
make build-static
```

## Compatibility Entry Points

For backward compatibility, root-level wrappers are available:

- `./install.sh` -> `./scripts/install.sh`
- `./quick-install.sh` -> `./scripts/quick-install.sh`
- `./test_installers.sh` -> `./tests/installation/run_installer_tests.sh`
