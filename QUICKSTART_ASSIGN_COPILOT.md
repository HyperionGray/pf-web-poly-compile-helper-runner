# Quick Start: Assign All Issues to Copilot

This guide explains how to quickly assign all remaining open issues to GitHub Copilot.

## What Was Created

Three new tools were added to help with bulk assignment:

1. **GitHub Actions Workflow** - Easy button-click solution
2. **Bash Script** - Command-line tool for advanced users
3. **Documentation** - Complete guide with all details

## Quickest Method (Recommended)

### Using GitHub Actions (No setup required!)

1. Go to your repository on GitHub
2. Click the **"Actions"** tab at the top
3. In the left sidebar, click **"Bulk Assign Copilot to All Open Issues"**
4. Click the **"Run workflow"** button on the right
5. Select `dry_run: true` for the first run (to see what would happen)
6. Click the green **"Run workflow"** button
7. Wait for it to complete and review the output
8. If everything looks good, run it again with `dry_run: false`

**That's it!** The workflow will:
- Find all open issues
- Add the `copilot` label to issues that don't have it
- The existing auto-assign workflow will then assign the Copilot bot user

## Current Issue Status

Based on the analysis, these issues need the copilot label:
- Issue #299: "Complete CI/CD Review - 2025-12-26"
- Issue #300: "Amazon Q Code Review - 2025-12-26"

All other open issues already have the copilot label.

## Alternative Method (Command Line)

If you prefer using the command line:

```bash
# Set your GitHub token
export GITHUB_TOKEN="ghp_your_token_here"

# Run the script
./scripts/assign-issues-to-copilot.sh
```

## More Information

For complete documentation, see:
- [docs/BULK_ASSIGN_COPILOT.md](docs/BULK_ASSIGN_COPILOT.md) - Full guide with troubleshooting
- [.github/workflows/bulk-assign-copilot.yml](.github/workflows/bulk-assign-copilot.yml) - The workflow file
- [scripts/assign-issues-to-copilot.sh](scripts/assign-issues-to-copilot.sh) - The bash script

## What Happens Next

After the copilot label is added to an issue:
1. The existing `.github/workflows/auto-assign-copilot.yml` workflow triggers automatically
2. It assigns the GitHub Copilot bot (username: `copilot`) to the issue
3. GitHub Copilot can then work on resolving the issue

## Notes

- The workflow is safe to run multiple times (it won't duplicate labels)
- Dry-run mode lets you preview changes before applying them
- Pull requests are automatically skipped (only issues are processed)
- The script handles pagination, so it works for repositories with any number of issues
