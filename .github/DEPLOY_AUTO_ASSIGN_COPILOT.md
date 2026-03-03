# Deployment Guide: Auto-Assign Copilot Workflow

## Quick Deploy (Recommended)

### Deploy to All Repositories

```bash
# Deploy to all accounts (P4X-ng, HyperionGray, TeamHG-Memex, hyp3ri0n-ng)
python trigger_workflow_all_repos.py --all-accounts workflows-sync.yml
```

This will:
1. Trigger the workflows-sync workflow in all repositories
2. The workflow template `workflow-templates/auto-assign-copilot.yml` will be copied to `.github/workflows/`
3. The workflow will be active immediately

### Verify Deployment

```bash
# Check which repos have the workflow
python trigger_auto_assign_copilot.py --all-accounts --check-only

# Check with label verification
python trigger_auto_assign_copilot.py --all-accounts --check-labels
```

## Manual Deploy (Single Repository)

If you need to deploy to a specific repository manually:

```bash
# 1. Navigate to the repository
cd /path/to/your/repo

# 2. Create workflows directory if it doesn't exist
mkdir -p .github/workflows

# 3. Copy the workflow
cp /path/to/.github/workflow-templates/auto-assign-copilot.yml .github/workflows/

# 4. Commit and push
git add .github/workflows/auto-assign-copilot.yml
git commit -m "Add auto-assign-copilot workflow"
git push
```

## Testing the Workflow

### In This Repository (P4X-ng/.github)

The workflow is already active! Test it:

1. Open a new issue
2. Add the label `copilot`
3. Check the Actions tab to see the workflow run
4. Verify:
   - Labels were created (copilot, copilot-gpt-5.1-codex, etc.)
   - @copilot was assigned
   - An informational comment was added

### In Other Repositories

After deployment via workflows-sync:

1. Wait for workflows-sync to complete (~5-10 minutes)
2. Open an issue in any repository
3. Add the `copilot` label
4. Verify the workflow runs

## Monitoring Deployment

### Check Workflow Sync Status

```bash
# See recent workflow sync runs
gh run list --repo P4X-ng/.github --workflow workflows-sync.yml --limit 5
```

### Check Individual Repository

```bash
# Check if workflow exists in a specific repo
gh api repos/P4X-ng/REPO_NAME/actions/workflows | jq '.workflows[] | select(.name == "Auto Assign Copilot to Issues")'
```

## Troubleshooting

### Workflow Not Appearing

**Problem:** Workflow doesn't appear in repository after sync

**Solution:**
1. Check workflows-sync ran successfully
2. Manually verify workflow template exists: `workflow-templates/auto-assign-copilot.yml`
3. Run workflows-sync again if needed
4. Deploy manually as fallback

### Labels Not Created

**Problem:** Workflow runs but labels aren't created

**Solution:**
1. Check workflow permissions in repo settings
2. Ensure workflow has `issues: write` permission
3. Check Actions logs for error messages
4. Verify GITHUB_TOKEN has necessary permissions

### @copilot Not Assigned

**Problem:** Labels created but @copilot not assigned

**Solution:**
1. Verify your organization has GitHub Copilot Business/Enterprise
2. Check that @copilot user exists in your organization
3. Ensure Copilot seat is assigned
4. Check workflow logs for error messages

### Model Label Not Detected

**Problem:** Model label exists but not mentioned in comment

**Solution:**
1. Comment is only added once - check if it already exists
2. Add model label before adding copilot label
3. Workflow detects the first model label it finds
4. Remove and re-add copilot label to trigger again

## Advanced: Custom Configuration

### Change Label Colors

Edit `workflow-templates/auto-assign-copilot.yml`:

```yaml
const requiredLabels = [
  {
    name: 'copilot',
    color: '0E8A16',  # Change this hex color
    description: 'Assign this issue to GitHub Copilot'
  },
  # ...
];
```

### Change Copilot Username

If your organization uses a different username:

```yaml
const copilotUsername = "copilot";  # Change this
```

### Add More Model Labels

Add to the `requiredLabels` array and `modelLabels` array:

```yaml
{
  name: 'copilot-custom-model',
  color: 'FF5733',
  description: 'Use custom model for Copilot'
}
```

### After Configuration Changes

Re-deploy the workflow:

```bash
# Re-sync to all repos
python trigger_workflow_all_repos.py --all-accounts workflows-sync.yml
```

## Rollback

If you need to remove the workflow:

### Remove from All Repositories

Currently there's no automated way to remove workflows. Manual steps:

1. Delete `.github/workflows/auto-assign-copilot.yml` from each repo
2. Commit and push
3. Or create a script to automate deletion across repos

### Remove from Single Repository

```bash
git rm .github/workflows/auto-assign-copilot.yml
git commit -m "Remove auto-assign-copilot workflow"
git push
```

## Maintenance

### Updating the Workflow

1. Edit `workflow-templates/auto-assign-copilot.yml`
2. Test in a single repo first
3. Deploy to all repos via workflows-sync
4. Verify deployment with checker script

### Monitoring Usage

Check workflow runs:

```bash
# See recent runs in a repo
gh run list --repo P4X-ng/REPO_NAME --workflow auto-assign-copilot.yml --limit 10
```

### Check Label Usage

```bash
# See issues with copilot label
gh issue list --repo P4X-ng/REPO_NAME --label copilot
```

## Documentation References

- **Comprehensive Guide:** [AUTO_ASSIGN_COPILOT.md](AUTO_ASSIGN_COPILOT.md)
- **Quick Start:** [QUICK_START_AUTO_ASSIGN_COPILOT.md](QUICK_START_AUTO_ASSIGN_COPILOT.md)
- **Implementation Notes:** [IMPLEMENTATION_NOTES_AUTO_ASSIGN.md](IMPLEMENTATION_NOTES_AUTO_ASSIGN.md)
- **General Workflow Sync:** [HOW_TO_APPLY_TO_ALL_REPOS.md](HOW_TO_APPLY_TO_ALL_REPOS.md)

## Support

For issues or questions:
1. Check the [AUTO_ASSIGN_COPILOT.md](AUTO_ASSIGN_COPILOT.md) troubleshooting section
2. Review workflow logs in Actions tab
3. Check this deployment guide
4. Open an issue in P4X-ng/.github repository
