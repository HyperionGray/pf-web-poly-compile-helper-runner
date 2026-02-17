# Bulk Assign Issues to Copilot

This directory contains tools to bulk-assign the `copilot` label to all open issues in the repository.

## Why This is Needed

The repository has an automated workflow (`.github/workflows/auto-assign-copilot.yml`) that automatically assigns the Copilot user to any issue that has the `copilot` label. However, some existing open issues may not have this label yet.

## Current Status

Based on the latest check, the following issues are open:
- Issue #306: ✅ Has copilot label (already assigned)
- Issue #304: ✅ Has copilot label (already assigned)
- Issue #303: ✅ Has copilot label (already assigned)
- Issue #302: ✅ Has copilot label (already assigned)
- Issue #301: ✅ Has copilot label (already assigned)
- Issue #300: ❌ Missing copilot label (needs assignment)
- Issue #299: ❌ Missing copilot label (needs assignment)
- Issue #297: ✅ Has copilot label (already assigned)

## Methods to Assign Issues

### Method 1: GitHub Actions Workflow (Recommended)

The easiest way is to use the GitHub Actions workflow:

1. Go to the **Actions** tab in the GitHub repository
2. Select **"Bulk Assign Copilot to All Open Issues"** workflow
3. Click **"Run workflow"**
4. Choose whether to run in dry-run mode (recommended first):
   - `dry_run: true` - Shows what would be done without making changes
   - `dry_run: false` - Actually adds the copilot label to issues
5. Click **"Run workflow"** button

**Advantages:**
- Easy to use (just click a button)
- Safe dry-run mode to preview changes
- Runs with proper GitHub permissions
- Shows clear progress and summary

### Method 2: Command-Line Script

For advanced users or CI/CD integration:

```bash
# Set your GitHub token
export GITHUB_TOKEN="ghp_your_token_here"

# Run the script
./scripts/assign-issues-to-copilot.sh
```

**Advantages:**
- Can be integrated into CI/CD pipelines
- Can be run locally
- Scriptable and automatable

**Getting a GitHub Token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with `repo` scope
3. Copy the token and set it as the `GITHUB_TOKEN` environment variable

### Method 3: Manual Assignment (For Small Numbers)

For just a few issues:

1. Go to each issue on GitHub
2. Add the `copilot` label manually
3. The auto-assign workflow will trigger automatically

## What Happens After Assignment

Once an issue has the `copilot` label:

1. The `.github/workflows/auto-assign-copilot.yml` workflow automatically triggers
2. It assigns the GitHub Copilot user (username: `copilot`) to the issue
   - Note: This refers to the GitHub Copilot bot user, not a human team member
3. GitHub Copilot can then work on addressing the issue automatically

## Workflow Files

- `.github/workflows/auto-assign-copilot.yml` - Automatic assignment when copilot label is added
- `.github/workflows/bulk-assign-copilot.yml` - Manual workflow to bulk-assign copilot label
- `scripts/assign-issues-to-copilot.sh` - Bash script for command-line bulk assignment

## Troubleshooting

### "Failed to assign Copilot" Error

This usually means:
- You need a GitHub Copilot seat assigned to your account/organization
- The GitHub token doesn't have sufficient permissions

### Rate Limiting

If you have many issues, the scripts include delays to avoid GitHub API rate limiting. Be patient and let them complete.

## Future Enhancements

Consider creating automation that:
- Automatically adds the copilot label to new issues based on certain criteria
- Bulk-removes copilot assignments from closed issues
- Reports on copilot assignment statistics
