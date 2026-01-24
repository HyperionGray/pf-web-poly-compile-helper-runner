# Quick Start: Auto-Assign Copilot Workflow

## What This Does

Automatically assigns GitHub Copilot to issues and supports model selection via labels.

## Quick Usage

### Step 1: Deploy to All Repos
```bash
# Deploy to all P4X-ng repositories
python trigger_workflow_all_repos.py P4X-ng workflows-sync.yml

# Or deploy to all accounts
python trigger_workflow_all_repos.py --all-accounts workflows-sync.yml
```

### Step 2: Use It
1. Open a new issue in any repository
2. Add the `copilot` label
3. Optionally add a model label:
   - `copilot-gpt-5.1-codex` (for code tasks)
   - `copilot-gpt-5.1` (for general AI)
   - `copilot-claude-4.5-opus` (for code review)

### Step 3: What Happens
- ✅ All required labels are auto-created (if they don't exist)
- ✅ `@copilot` is assigned to the issue
- ✅ An informational comment is added with guidance

## Check Deployment Status

```bash
# Check which repos have the workflow
python trigger_auto_assign_copilot.py --all-accounts --check-only

# Check with label status
python trigger_auto_assign_copilot.py P4X-ng --check-labels
```

## Example Issue Flow

### Scenario 1: Basic Copilot Assignment
```
Title: "Fix authentication bug"
Labels: bug, copilot
Result: @copilot assigned, comment with model selection options
```

### Scenario 2: With Model Selection
```
Title: "Refactor user service"
Labels: refactor, copilot, copilot-gpt-5.1-codex
Result: @copilot assigned, comment mentions GPT-5.1-Codex selected
```

## Files Created

- `.github/workflows/auto-assign-copilot.yml` - Active workflow
- `workflow-templates/auto-assign-copilot.yml` - Template for distribution
- `trigger_auto_assign_copilot.py` - Python script to check deployment
- `AUTO_ASSIGN_COPILOT.md` - Full documentation

## Benefits

✅ **Automatic label creation** - No manual setup required  
✅ **Model selection** - Choose the right AI model for the task  
✅ **Least-privilege** - Uses only required permissions  
✅ **Self-documenting** - Adds helpful comments to issues  
✅ **Org-wide distribution** - Deploy to all repos at once  

## Next Steps

1. Deploy the workflow to all repositories
2. Test it by opening an issue with the `copilot` label
3. Check the Actions tab to see the workflow run
4. Review the informational comment added to the issue

For detailed documentation, see [AUTO_ASSIGN_COPILOT.md](AUTO_ASSIGN_COPILOT.md).
