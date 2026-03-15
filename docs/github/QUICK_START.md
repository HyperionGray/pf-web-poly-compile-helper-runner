# Quick Start: Trigger Workflows on All Repos

## ⚡ 5-Minute Setup

### Step 1: Create Token (2 min)
1. Go to: https://github.com/settings/tokens/new
2. Name: `P4X-ng Workflow Dispatcher`
3. Select scopes:
   - ✅ `repo` (access private repos)
   - ✅ `workflow` (trigger workflows)
   - ⚠️ Skip `read:org` (P4X-ng is a user account, not an organization)
4. Click "Generate token"
5. **Copy the token** (you won't see it again!)

### Step 2: Add Secret (1 min)
1. Go to: https://github.com/P4X-ng/.github/settings/secrets/actions
2. Click "New repository secret"
3. Name: `GH_PAT`
4. Value: Paste your token
5. Click "Add secret"

### Step 3: Test (2 min)
1. Go to: https://github.com/P4X-ng/.github/actions
2. Click "Trigger Workflow on All Repos"
3. Click "Run workflow"
4. Set:
   - Workflow file: `workflows-sync.yml`
   - Check only: ✅ **YES** (just testing)
5. Click "Run workflow"
6. Wait ~30 seconds
7. Click on the workflow run
8. Check logs - should show **~19 repositories**

### Step 4: Use It! ✨
Now you can trigger any workflow across all repos:

**Sync workflows to all repos:**
- Workflow file: `workflows-sync.yml`
- Check only: ❌ NO

**Run security scans:**
- Workflow file: `auto-sec-scan.yml`
- Check only: ❌ NO

**Run tests:**
- Workflow file: `playwright-tests.yml`
- Check only: ❌ NO

---

## 🚨 Troubleshooting

**Still seeing only 3 repos?**
→ For user accounts (P4X-ng), only need `repo` and `workflow` scopes (NOT `read:org`)

**"Workflow not found" errors?**
→ Run `workflows-sync.yml` first to distribute workflow files

**"401 Unauthorized"?**
→ Verify `GH_PAT` secret is set correctly

---

## 📖 Full Documentation

Need more details? See:
- **Complete Guide**: [HOW_TO_APPLY_TO_ALL_REPOS.md](HOW_TO_APPLY_TO_ALL_REPOS.md)
- **Setup Guide**: [GH_PAT_SETUP.md](GH_PAT_SETUP.md)
- **Usage Guide**: [TRIGGER_WORKFLOWS_GUIDE.md](TRIGGER_WORKFLOWS_GUIDE.md)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Overview**: [README.md](README.md)

---

## 💡 Common Tasks

```bash
# Check which repos have a workflow
python trigger_workflow_all_repos.py P4X-ng workflows-sync.yml --check-only

# Trigger security scan on all repos
python trigger_workflow_all_repos.py P4X-ng auto-sec-scan.yml

# Trigger with specific branch
python trigger_workflow_all_repos.py P4X-ng test.yml --ref develop
```

---

**Quick Reference:**
- **For user accounts:** Token scopes: `repo`, `workflow` (NOT `read:org`)
- **For organizations:** Token scopes: `repo`, `workflow`, `read:org`
- Secret name: `GH_PAT`
- Test workflow: `workflows-sync.yml` with check-only
- Expected repos: ~19
