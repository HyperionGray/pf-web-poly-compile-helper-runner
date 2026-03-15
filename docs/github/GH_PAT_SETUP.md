# Setting Up GH_PAT for Organization-Wide Workflow Triggers

## Why You Need This

To trigger workflows across **all 19+ repositories** in the P4X-ng organization (including private repos), you need a Personal Access Token (PAT) with organization-level permissions.

## Current Situation

Without proper permissions, only **3 public repositories** are visible:
- ✓ PhoenixBoot (public)
- ✓ pf-runner (public)  
- ✓ .github (private, but you own it)

The other **~16 private repositories** are hidden due to API permissions.

## Step-by-Step Setup

### 1. Create a Personal Access Token

1. Go to GitHub: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Fill in the form:
   - **Note**: `P4X-ng Org Workflow Dispatcher`
   - **Expiration**: Choose based on your security policy (recommend 90 days with rotation)
   - **Select scopes**:
     - ✅ `repo` - Full control of private repositories
       - This includes: `repo:status`, `repo_deployment`, `public_repo`, `repo:invite`, `security_events`
     - ✅ `workflow` - Update GitHub Action workflows
     - ✅ `read:org` - Read organization membership and teams

4. Click **"Generate token"**
5. **Copy the token immediately** (you won't see it again!)

### 2. Add Token to Repository Secrets

1. Go to the `.github` repository: https://github.com/P4X-ng/.github
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Fill in:
   - **Name**: `GH_PAT`
   - **Secret**: Paste the token you just created
5. Click **"Add secret"**

### 3. Verify the Setup

#### Option A: Using GitHub Actions UI

1. Go to **Actions** tab in the `.github` repository
2. Click **"Trigger Workflow on All Repos"** workflow
3. Click **"Run workflow"**
4. Set parameters:
   - Workflow file: `workflows-sync.yml`
   - Check only: **✓** (enable this to test without triggering)
5. Click **"Run workflow"**
6. Wait for completion and check the logs
7. You should see **~19 repositories** listed

#### Option B: Using Command Line

```bash
# Set your token
export GITHUB_TOKEN="ghp_your_token_here"

# Check how many repos are visible
python trigger_workflow_all_repos.py P4X-ng workflows-sync.yml --check-only
```

**Expected output:**
```
Fetching repositories for P4X-ng...
Found 19 repositories

Checking which repositories have workflow 'workflows-sync.yml':
--------------------------------------------------------------------------------
✓ P4X-ng/repo1                           - Workflow exists
✓ P4X-ng/repo2                           - Workflow exists
...
(should show ~19 repositories)
```

## Troubleshooting

### Still Only Seeing 3 Repositories?

**Problem**: Token doesn't have `read:org` scope or organization access

**Solutions**:
1. **Regenerate the token** with all required scopes
2. **For organization accounts**: Ensure the token has organization access
   - Go to: https://github.com/settings/tokens
   - Click on your token → **Configure SSO** (if applicable)
   - **Authorize** for P4X-ng organization
3. **Update the secret** in repository settings with the new token

### "Resource not accessible by integration"

**Problem**: Using `GITHUB_TOKEN` instead of `GH_PAT`

**Solution**: The default `GITHUB_TOKEN` doesn't have org-wide permissions. Must use `GH_PAT` secret.

### Token Expired

**Problem**: Token has expired based on expiration date

**Solution**: 
1. Generate a new token following steps above
2. Update `GH_PAT` secret with new token

## Security Best Practices

### Do's ✅
- ✅ Use token expiration (30-90 days recommended)
- ✅ Set up calendar reminders to rotate tokens
- ✅ Use the minimum required scopes
- ✅ Store token only in GitHub Secrets
- ✅ Audit workflow runs regularly

### Don'ts ❌
- ❌ Never commit the token to any repository
- ❌ Don't share the token via Slack, email, or other channels
- ❌ Don't use tokens with excessive permissions
- ❌ Don't set "no expiration" for production tokens
- ❌ Don't reuse tokens across multiple purposes

## Token Rotation Schedule

Recommended rotation schedule:

| Token Age | Action |
|-----------|--------|
| 0-60 days | ✅ Active, no action needed |
| 60-75 days | ⚠️ Plan rotation, create reminder |
| 75-85 days | 🟡 Generate new token, test in staging |
| 85-90 days | 🔴 Update secret before expiration |
| 90+ days | ❌ Token expired, workflows will fail |

## Alternative: Fine-Grained Personal Access Tokens (Beta)

GitHub now offers fine-grained PATs with better security:

1. Go to: https://github.com/settings/personal-access-tokens/new
2. Choose specific repositories or "All repositories" 
3. Set repository permissions:
   - **Actions**: Read and write
   - **Contents**: Read
   - **Metadata**: Read
4. Set organization permissions:
   - **Members**: Read

**Note**: Fine-grained tokens are still in beta and may have limitations.

## Getting Help

If you continue to have issues:

1. Verify token scopes at: https://github.com/settings/tokens
2. Check workflow run logs in the Actions tab
3. Review the [TRIGGER_WORKFLOWS_GUIDE.md](TRIGGER_WORKFLOWS_GUIDE.md)
4. Test with the `--check-only` flag first

## Quick Reference

```bash
# Required scopes
repo          # Access private repositories
workflow      # Trigger workflows  
read:org      # List all org repositories

# Test command
python trigger_workflow_all_repos.py P4X-ng workflows-sync.yml --check-only

# Expected result
Found 19 repositories  # (or close to it)
```

## Next Steps

Once you've verified the token works and sees all repositories:

1. ✅ Run `workflows-sync.yml` to distribute workflow files to all repos
2. ✅ Trigger security scans: `auto-sec-scan.yml`
3. ✅ Set up scheduled workflow dispatches
4. ✅ Configure other automation as needed

---

**Last Updated**: 2025-11-14  
**Required Scopes**: `repo`, `workflow`, `read:org`  
**Secret Name**: `GH_PAT`
