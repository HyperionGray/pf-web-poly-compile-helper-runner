# Feature Installer Script Flags

The feature installers in `scripts/` now share a consistent command-line UX:

- `--help` prints usage and exits.
- `--dry-run` prints installation actions without making changes.

## Updated Installers

- `scripts/injection/install-injection-tools.sh`
- `scripts/gitops/install-git-filter-repo.sh`
- `scripts/gitops/install-pr-tools.sh`

## Why this was added

This makes installers safer to run in CI and easier for users to understand before making system changes.

## Examples

```bash
# Show usage
./scripts/injection/install-injection-tools.sh --help

# Preview package-manager commands only
./scripts/gitops/install-pr-tools.sh --dry-run

# Preview pip installation only
./scripts/gitops/install-git-filter-repo.sh --dry-run
```

## Validation

Run:

```bash
tests/installation/test_feature_installer_cli.sh
```

This verifies each updated installer:

1. returns success for `--help`
2. includes usage text and `--dry-run` option
3. returns success for `--dry-run`
4. emits `[DRY-RUN]` markers

