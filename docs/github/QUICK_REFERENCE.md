# Quick Reference: GitHub Actions Configuration

## 🚀 New Features Available

### 1. Amazon Q Review on Every Push
**Automatically runs** on every push to main, master, or develop branches.

No action needed - it's automatic!

### 2. Manual AI Model Selection
**Trigger any AI model** for code review:

1. Go to repository → Actions tab
2. Select "AmazonQ Review after GitHub Copilot"
3. Click "Run workflow"
4. Select AI model:
   - `amazonq` - Amazon Q Developer
   - `codex` - OpenAI Codex
   - `gemini` - Google Gemini
   - `gpt5` - GPT-5
5. Click "Run workflow"

### 3. Tag-based E2E Reviews
**Trigger comprehensive E2E reviews** with tags:

```bash
# Create and push e2eweekly tag for E2E review (uses GPT-5.1-Codex)
git tag e2eweekly
git push origin e2eweekly

# Or create custom E2E tag
git tag e2e-sprint-42
git push origin e2e-sprint-42
```

### 4. Tag-based Weekly Reviews
**Trigger weekly comprehensive reviews** with tags:

```bash
# Create and push weeklyreview tag for weekly review (uses GPT-5.1)
git tag weeklyreview
git push origin weeklyreview

# Or create date-specific review tag
git tag review-2024-12-27
git push origin review-2024-12-27
```

### 5. Manual Tag-based Review
**Manually trigger** with custom settings:

1. Go to repository → Actions tab
2. Select "Tag-based Code Review"
3. Click "Run workflow"
4. Select:
   - **Review type**: e2e, weekly, or full
   - **AI model**: gpt-5.1-codex, gpt-5.1, gpt-5, amazonq, codex, or gemini
5. Click "Run workflow"

## 🔄 Sync Workflows to All Accounts

### Automatic Sync (Recommended)
Runs daily at 6:00 UTC to all accounts:
- P4X-ng
- HyperionGray
- TeamHG-Memex
- hyp3ri0n-ng

### Manual Sync via GitHub UI
1. Go to https://github.com/P4X-ng/.github/actions
2. Click "Workflows Sync"
3. Click "Run workflow"
4. Keep defaults (syncs to all accounts)
5. Click "Run workflow"

### Manual Sync via Command Line
```bash
export GITHUB_TOKEN="your_token_here"
cd /path/to/.github
python sync_workflows.py --all-accounts
```

## 📋 Tag Naming Conventions

### E2E Reviews (GPT-5.1-Codex)
- `e2eweekly` - Standard weekly E2E
- `e2e-YYYY-MM` - Monthly E2E
- `e2e-sprint-N` - Sprint-based E2E
- `e2e-*` - Any custom E2E tag

### Weekly Reviews (GPT-5.1)
- `weeklyreview` - Standard weekly review
- `review-YYYY-MM-DD` - Date-specific review
- `review-*` - Any custom review tag

## 🔐 Required Secrets

### COPILOT_TOKEN (Required)
Set up in repository or organization settings:
1. Go to Settings → Secrets and variables → Actions
2. New secret: `COPILOT_TOKEN`
3. Value: Your GitHub Copilot token (see COPILOT_TOKEN_SETUP.md)

### GH_PAT (Already configured in .github repo)
Used for syncing workflows across accounts.

### AWS Credentials (Optional)
For full Amazon Q integration:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

## 📊 Workflow Triggers Summary

| Workflow | Automatic Triggers | Manual Trigger | Default Model |
|----------|-------------------|----------------|---------------|
| Amazon Q Review | Every push to main/master/develop | ✅ (with model selection) | amazonq |
| Tag-based Review | Tags: e2eweekly, weeklyreview, e2e-*, review-* | ✅ (with type & model selection) | gpt-5.1-codex (E2E), gpt-5.1 (weekly) |
| Complete CI/CD | Every 12 hours, push, PR | ✅ | N/A |
| GPT-5 Implementation | Push, PR | ✅ | gpt-5 |

## 🎯 Common Tasks

### Run E2E Review Now
```bash
git tag e2eweekly && git push origin e2eweekly
```

### Run Weekly Review Now
```bash
git tag weeklyreview && git push origin weeklyreview
```

### Review with Specific AI Model
1. Actions → Tag-based Code Review → Run workflow
2. Select review type and model
3. Run

### Sync All Workflows Now
1. Actions → Workflows Sync → Run workflow
2. Run

### Check Which Repos Have Workflow
```bash
python trigger_workflow_all_repos.py auto-sec-scan.yml --all-accounts --check-only
```

## 🆘 Troubleshooting

### Workflow doesn't appear in Actions tab
- Ensure workflows are synced to the repository
- Wait a few minutes after sync
- Refresh the page
- Check repository settings → Actions → General (ensure workflows are enabled)

### "Resource not accessible" error
- Verify `COPILOT_TOKEN` secret is set
- Ensure token has `copilot` scope
- Check Copilot subscription is active

### Tag trigger doesn't work
- Verify tag name matches patterns
- Check workflow is synced to repository
- Look for workflow runs in Actions tab
- Ensure workflows are enabled in repository settings

### hyp3ri0n-ng repos not syncing
- Verify `GH_PAT` token has access to hyp3ri0n-ng
- Ensure token has `repo` and `workflow` scopes
- Test with: `python sync_workflows.py --all-accounts --check-only`

## 📚 Documentation

- **GITHUB_ACTIONS_CONFIG_SUMMARY.md** - Complete implementation details
- **COPILOT_TOKEN_SETUP.md** - How to set up Copilot token
- **HOW_TO_APPLY_TO_ALL_REPOS.md** - Detailed syncing instructions
- **workflow-templates/README.md** - All available workflows
- **TRIGGER_WORKFLOWS_GUIDE.md** - Triggering workflows guide

## 💡 Tips

1. **Use tags for periodic reviews** - More reliable than scheduling
2. **Test in one repo first** - Before syncing to all repos
3. **Check Actions tab** - Monitor workflow runs and review issues created
4. **Use --check-only flag** - Test what would happen before syncing
5. **Set COPILOT_TOKEN at org level** - Applies to all repos automatically

---

*Last Updated: 2024-12-27*
*For detailed information, see GITHUB_ACTIONS_CONFIG_SUMMARY.md*
