# How to Apply Workflows to All P4X-ng Repositories

This guide provides **step-by-step instructions** for applying and triggering workflows across all P4X-ng repositories and related accounts.

> **Important Note:** This system supports multiple accounts: P4X-ng (user), HyperionGray (org), TeamHG-Memex (org), and hyp3ri0n-ng (user/org). For user accounts, you only need `repo` and `workflow` token scopes - the `read:org` scope is only required for organization accounts.

## 📋 Prerequisites

### 1. Ensure GH_PAT Secret is Configured

The `GH_PAT` (GitHub Personal Access Token) secret must be configured with the correct permissions.

#### Check if GH_PAT is already set:
1. Go to https://github.com/P4X-ng/.github/settings/secrets/actions
2. Look for a secret named `GH_PAT`
3. If it exists, verify it has the correct scopes (see below)

#### If GH_PAT doesn't exist or needs updating:
1. **Generate a new token:**
   - Go to https://github.com/settings/tokens/new
   - Name: `P4X-ng Workflow Manager`
   - Expiration: Choose appropriate duration (90 days, 1 year, or no expiration)
   - **Select these scopes:**
     - ✅ `repo` (Full control of private repositories)
     - ✅ `workflow` (Update GitHub Action workflows)
     - ✅ `read:org` (Optional - only needed if P4X-ng is an organization; can be skipped for user accounts)
   - Click "Generate token"
   - **Copy the token immediately** (you won't see it again!)
   
   > **Note:** P4X-ng is a user account, not an organization. The `read:org` scope is optional and only needed if you have organization repositories. For user accounts, only `repo` and `workflow` scopes are required.

2. **Add the token as a secret:**
   - Go to https://github.com/P4X-ng/.github/settings/secrets/actions
   - Click "New repository secret" (or "Update" if updating existing)
   - Name: `GH_PAT`
   - Value: Paste your token
   - Click "Add secret" or "Update secret"

## 🚀 Method 1: Apply All Workflows to All Repos (Recommended First Step)

This is the **primary method** to distribute workflow templates to all repositories.

### Via GitHub Actions UI (Easiest)

1. **Navigate to Actions:**
   - Go to https://github.com/P4X-ng/.github/actions

2. **Select Workflows Sync:**
   - In the left sidebar, click on **"Workflows Sync"**

3. **Run the workflow:**
   - Click the **"Run workflow"** button (top right)
   - Keep defaults (branch: main)
   - Click **"Run workflow"** (confirm)

4. **Monitor progress:**
   - Click on the workflow run that just started
   - Watch the logs to see it copying workflows to each repository
   - Expected duration: 2-5 minutes for ~19 repositories

5. **Verify success:**
   - Check that the workflow completed successfully (green checkmark)
   - Look at the logs to see which repos received the workflows

### Via Command Line

```bash
# Set your GitHub token
export GITHUB_TOKEN="ghp_your_token_here"

# Navigate to the .github repo
cd /path/to/.github

# Trigger workflows-sync on all repos across ALL accounts (recommended)
python trigger_workflow_all_repos.py workflows-sync.yml --all-accounts

# Or trigger for a single account
python trigger_workflow_all_repos.py P4X-ng workflows-sync.yml

# Or check which repos will be affected first (dry-run)
python trigger_workflow_all_repos.py workflows-sync.yml --all-accounts --check-only
```

### What This Does

- Copies all workflow files from `workflow-templates/` in this repo
- To `.github/workflows/` in each repository
- With `--all-accounts`: Affects P4X-ng, HyperionGray, TeamHG-Memex, and hyp3ri0n-ng repositories
- Creates/updates workflows in each repo with a commit message: "Sync workflow files from .github repo"

### What Gets Synced

All workflow templates including:
- `auto-complete-cicd-review.yml` - Complete CI/CD review every 12 hours
- `auto-copilot-code-cleanliness-review.yml` - Code cleanliness review
- `auto-copilot-test-review-playwright.yml` - Playwright test review
- `auto-copilot-functionality-docs-review.yml` - Functionality and docs review
- `auto-amazonq-review.yml` - Amazon Q review
- `auto-sec-scan.yml` - Security scanning
- `auto-assign-copilot.yml` - Auto-assign issues to Copilot
- `auto-label.yml` - Auto-label issues
- And many more...

## ⚡ Method 2: Trigger a Specific Workflow on All Repos

After workflows are synced (Method 1), you can trigger any specific workflow across all repositories.

### Via GitHub Actions UI

1. **Navigate to Actions:**
   - Go to https://github.com/P4X-ng/.github/actions

2. **Select Trigger Workflow on All Repos:**
   - In the left sidebar, click on **"Trigger Workflow on All Repos"**

3. **Configure and run:**
   - Click **"Run workflow"**
   - **Workflow file:** Enter the workflow filename (e.g., `auto-sec-scan.yml`)
   - **Git reference:** Leave as `main` (or specify a branch/tag)
   - **Include archived:** Leave unchecked (unless you want archived repos)
   - **Check only:** Check this to see which repos have the workflow without triggering
   - Click **"Run workflow"**

4. **Monitor progress:**
   - Click on the workflow run
   - Watch the logs to see each repository being triggered

### Via Command Line

```bash
# Set your GitHub token
export GITHUB_TOKEN="ghp_your_token_here"

# Trigger security scan on all accounts (recommended)
python trigger_workflow_all_repos.py auto-sec-scan.yml --all-accounts

# Or trigger on a single account
python trigger_workflow_all_repos.py P4X-ng auto-sec-scan.yml

# Trigger with specific branch
python trigger_workflow_all_repos.py auto-sec-scan.yml --all-accounts --ref develop

# Check which repos have the workflow (without triggering)
python trigger_workflow_all_repos.py auto-sec-scan.yml --all-accounts --check-only

# Include archived repositories
python trigger_workflow_all_repos.py auto-sec-scan.yml --all-accounts --include-archived
```

### The --all-accounts Flag

The `--all-accounts` flag automatically processes all four accounts in one run:
- **P4X-ng** (personal account)
- **HyperionGray** (organization)
- **TeamHG-Memex** (organization)
- **hyp3ri0n-ng** (personal account)

This is the **recommended approach** as it:
- Simplifies maintenance (one command instead of three)
- Provides consolidated summary across all accounts
- Maintains proper billing separation (each account billed separately)

### Common Workflows to Trigger

| Workflow File | Purpose | When to Use |
|--------------|---------|-------------|
| `auto-sec-scan.yml` | Security scanning | After new code or periodically |
| `auto-complete-cicd-review.yml` | Complete CI/CD review | To run comprehensive review now |
| `auto-copilot-code-cleanliness-review.yml` | Code cleanliness check | To identify large files to split |
| `auto-copilot-test-review-playwright.yml` | Playwright test review | To check test coverage |
| `playwright-tests.yml` | Run Playwright tests | To execute tests across all repos |
| `python-tests.yml` | Run Python tests | To execute Python tests |

## 📅 Automatic Scheduling

Workflows are automatically triggered on schedules defined in each workflow file:

- **Workflows Sync** - Daily at 6:00 UTC
- **Complete CI/CD Review** - Every 12 hours (00:00 and 12:00 UTC)
- **Code Cleanliness Review** - Every 12 hours

You don't need to manually trigger these unless you want to run them immediately.

## 🔍 Verification

### Check if workflows were synced successfully:

```bash
# Check a specific repo
python trigger_workflow_all_repos.py P4X-ng auto-sec-scan.yml --check-only

# Expected output:
# ✓ P4X-ng/repo1  - Workflow exists
# ✓ P4X-ng/repo2  - Workflow exists
# ...
```

### View workflow runs:
1. Go to any P4X-ng repository
2. Click the **Actions** tab
3. You should see the synced workflows in the left sidebar

## 🚨 Troubleshooting

### Issue: "Only 3 repos found instead of ~19"

**Cause:** Token doesn't have access to private repositories, or the API call is using the wrong endpoint.

**Solution for User Accounts (like P4X-ng):**
1. Go to https://github.com/settings/tokens
2. Find your token or create a new one
3. Ensure these scopes are selected:
   - ✅ `repo` (Full control of private repositories - **this is the critical one**)
   - ✅ `workflow` (Update GitHub Action workflows)
4. Update the `GH_PAT` secret in repository settings
5. The script automatically tries user endpoint if organization endpoint fails

**Note:** The `read:org` scope is NOT needed for user accounts, only for organizations.

### Issue: "Workflow not found" for most repositories

**Cause:** The workflow file doesn't exist in those repositories yet.

**Solution:**
1. Run **Workflows Sync** first (Method 1 above)
2. Wait for sync to complete (check Actions tab)
3. Verify sync succeeded
4. Then trigger the specific workflow

### Issue: "403 Forbidden" or "401 Unauthorized"

**Cause:** Token doesn't have required permissions or has expired.

**Solution:**
1. Verify token has correct scopes
2. Check token hasn't expired
3. Regenerate token if needed
4. Update `GH_PAT` secret

### Issue: Rate limiting

**Cause:** GitHub API has rate limits (5000 requests/hour for authenticated requests).

**Solution:**
- The script includes a delay between requests (default 1.5 seconds)
- Wait a bit and try again
- For command line, increase delay: `--delay 2.0`

## 💡 Best Practices

1. **Always sync first:** Run Workflows Sync before triggering specific workflows
2. **Use check-only:** Test with `--check-only` to see what will be affected
3. **Monitor the Actions tab:** Watch for any errors or issues
4. **Keep token secure:** Never commit tokens to repositories
5. **Rotate tokens regularly:** For security, regenerate tokens periodically
6. **Review workflow runs:** Check individual repos to ensure workflows ran successfully

## 📚 Additional Resources

- **[README.md](README.md)** - Overview and quick start
- **[TRIGGER_WORKFLOWS_GUIDE.md](TRIGGER_WORKFLOWS_GUIDE.md)** - Detailed triggering guide
- **[QUICK_START.md](QUICK_START.md)** - 5-minute setup guide
- **[workflow-templates/README.md](workflow-templates/README.md)** - Available workflow templates
- **[GH_PAT_SETUP.md](GH_PAT_SETUP.md)** - Token setup guide

## 🎯 Quick Reference

**To apply all workflows to all repos:**
```
Actions → Workflows Sync → Run workflow
```

**To trigger a specific workflow on all repos:**
```
Actions → Trigger Workflow on All Repos → Run workflow → Enter workflow filename
```

**Token requirements:**
- Secret name: `GH_PAT`
- Required scopes: `repo`, `workflow`, `read:org`

**Expected results:**
- ~19 repositories affected
- Workflows appear in each repo's `.github/workflows/` directory
- Automatic sync happens daily at 6:00 UTC
