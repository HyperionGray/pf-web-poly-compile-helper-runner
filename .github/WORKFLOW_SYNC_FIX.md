# Workflow Sync Fix Summary

## Problem
The "Workflows Sync" workflow in `.github/workflows/workflows-sync.yml` was failing with a **"startup_failure"** error. The root cause was that the workflow was trying to use a non-existent GitHub Action: `wow-actions/workflows-sync@main`.

## Error Details
- **Error Type**: startup_failure
- **Cause**: Non-existent GitHub Action reference
- **Impact**: All workflow sync runs were failing immediately at startup
- **Affected Workflow**: `.github/workflows/workflows-sync.yml`

## Solution

### 1. Created Custom Sync Script (`sync_workflows.py`)
Instead of relying on a third-party action that doesn't exist, we created a custom Python script that:

- **Fetches all P4X-ng repositories** dynamically using the GitHub API
- **Syncs workflow template files** from `workflow-templates/` to `.github/workflows/` in each repository
- **Handles file creation and updates** using the GitHub Contents API
- **Supports dry-run mode** for testing without making changes
- **Excludes archived repositories** by default
- **Skips the .github repository** itself to avoid circular syncing

**Usage:**
```bash
# Sync to all repositories
python sync_workflows.py P4X-ng

# Dry run (see what would be synced)
python sync_workflows.py P4X-ng --dry-run

# Include archived repositories
python sync_workflows.py P4X-ng --include-archived
```

### 2. Updated Workflow Configuration
The `workflows-sync.yml` workflow now:

1. **Checks out the repository** using `actions/checkout@main`
2. **Sets up Python** using `actions/setup-python@main`
3. **Installs dependencies** (requests library)
4. **Runs the custom sync script** with the GH_PAT secret for authentication

### 3. Standardized Action Versions
Updated all GitHub Actions across 15 workflow template files to use `@main` instead of version tags:

- ✅ `actions/checkout@main` (was @v4)
- ✅ `actions/setup-python@main` (was @v5)
- ✅ `actions/setup-node@main` (was @v4)
- ✅ `actions/github-script@main` (was @v7)
- ✅ And 14+ other actions

This ensures:
- Consistency across all workflow templates
- Always using the latest stable version
- Simplified maintenance

### 4. Cleaned Up Repository Structure
- Moved `workflow-templates/workflows-sync.yml` to `workflows-sync-template-backup.yml`
- This workflow is specific to the .github repository and shouldn't be synced to other repos

## Testing
To verify the fix works:

1. Go to the **Actions** tab in the P4X-ng/.github repository
2. Select **"Workflows Sync"**
3. Click **"Run workflow"**
4. The workflow should now complete successfully instead of failing at startup

## Files Changed
- `.github/workflows/workflows-sync.yml` - Updated to use custom script
- `sync_workflows.py` - New custom sync script (271 lines)
- `README.md` - Added documentation for the new script
- 15 workflow template files - Updated to use @main for actions
- `workflows-sync-template-backup.yml` - Moved from workflow-templates/

## Requirements
The workflow requires a GitHub Personal Access Token (PAT) stored as `GH_PAT` secret with:
- ✅ `repo` scope - Full control of private repositories
- ✅ `workflow` scope - Update GitHub Action workflows

## Benefits
1. **No dependency on non-existent actions** - We control the sync logic
2. **Dynamic repository discovery** - Automatically includes all P4X-ng repos
3. **Better error handling** - Clear output showing which files synced successfully
4. **Flexible configuration** - Easy to customize sync behavior
5. **Consistent action versions** - All workflows use @main for simplicity
