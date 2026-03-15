# Triggering Workflows Across All Repositories

This guide explains how to trigger workflows across all repositories in the P4X-ng organization.

## Overview

The P4X-ng organization has approximately 19 repositories (both public and private). To trigger workflows across all of them, you need proper permissions and the right tools.

## The Permissions Issue

By default, GitHub API searches only return **public repositories** unless you use an organization-level API endpoint with a properly scoped Personal Access Token (PAT).

### Required Token Scopes

To trigger workflows across all repositories (including private ones), your `GH_PAT` secret must have:

- ✅ **`repo`** - Full control of private repositories
- ✅ **`workflow`** - Update GitHub Action workflows
- ✅ **`read:org`** - Read organization membership and repositories

## Methods to Trigger Workflows

### Method 1: GitHub Actions Workflow (Recommended)

Use the `trigger-all-repos.yml` workflow to manually trigger any workflow across all repositories.

#### Setup

1. **Create a Personal Access Token (PAT)**
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Name: `P4X-ng Organization Workflow Trigger`
   - Select scopes: `repo`, `workflow`, `read:org`
   - Generate and copy the token

2. **Add the token as a secret**
   - Go to the `.github` repository settings
   - Secrets and variables → Actions → New repository secret
   - Name: `GH_PAT`
   - Value: Paste your PAT
   - Click "Add secret"

3. **Run the workflow**
   - Go to Actions tab in the `.github` repository
   - Select "Trigger Workflow on All Repos"
   - Click "Run workflow"
   - Fill in the parameters:
     - **Workflow file**: The workflow filename (e.g., `workflows-sync.yml`)
     - **Git reference**: Branch/tag to run from (default: `main`)
     - **Include archived**: Whether to include archived repos
     - **Check only**: Just check which repos have the workflow without triggering

#### Example Usage

**Trigger security scan on all repos:**
```
Workflow file: security-scan.yml
Git reference: main
```

**Check which repos have Playwright tests:**
```
Workflow file: playwright-tests.yml
Check only: true
```

### Method 2: Command Line Script

Use the Python script directly for more control.

#### Prerequisites

```bash
pip install requests
export GITHUB_TOKEN="ghp_your_token_here"  # or use --token flag
```

#### Usage Examples

**List all repositories:**
```bash
python trigger_workflow_all_repos.py P4X-ng workflows-sync.yml --check-only
```

**Trigger workflows-sync on all repos:**
```bash
python trigger_workflow_all_repos.py P4X-ng workflows-sync.yml
```

**Trigger on a specific branch:**
```bash
python trigger_workflow_all_repos.py P4X-ng security-scan.yml --ref develop
```

**Include archived repositories:**
```bash
python trigger_workflow_all_repos.py P4X-ng test.yml --include-archived
```

**Trigger with workflow inputs:**
```bash
python trigger_workflow_all_repos.py P4X-ng deploy.yml \
  --input environment=staging \
  --input version=1.2.3
```

#### Script Options

```
usage: trigger_workflow_all_repos.py [-h] [--ref REF] [--token TOKEN]
                                     [--input INPUTS] [--include-archived]
                                     [--check-only] [--delay DELAY]
                                     org workflow

Arguments:
  org                   Organization or user name (e.g., P4X-ng)
  workflow              Workflow file name (e.g., workflows-sync.yml)

Options:
  --ref REF            Git reference (branch/tag/SHA, default: main)
  --token TOKEN        GitHub token (or set GITHUB_TOKEN env var)
  --input KEY=VALUE    Workflow input (can be used multiple times)
  --include-archived   Include archived repositories
  --check-only         Only check which repos have the workflow
  --delay DELAY        Delay between API calls in seconds (default: 1.0)
```

## Common Workflows to Trigger

Here are workflows you might want to trigger across all repos:

| Workflow File | Purpose |
|--------------|---------|
| `workflows-sync.yml` | Sync workflow files from .github repo |
| `security-scan.yml` | Run security scanning |
| `playwright-tests.yml` | Run Playwright tests |
| `python-tests.yml` | Run Python tests |
| `auto-sec-scan.yml` | Automated security scan |

## Troubleshooting

### "Only 3 repos found instead of 19"

**Cause**: Your token doesn't have `read:org` scope or doesn't have access to private repositories.

**Solution**: 
1. Check your `GH_PAT` secret has all required scopes
2. Regenerate the token with correct scopes if needed
3. Update the secret in repository settings

### "Workflow not found" for most repos

**Cause**: The workflow file doesn't exist in those repositories yet.

**Solution**:
1. First run `workflows-sync.yml` to distribute the workflow files
2. Wait for the sync to complete (check Actions tab)
3. Then trigger the specific workflow

### "403 Forbidden" or "401 Unauthorized"

**Cause**: Token doesn't have required permissions.

**Solution**:
- For organization repos: Use a PAT with `repo`, `workflow`, `read:org` scopes
- For user repos: Use a PAT with `repo` and `workflow` scopes

### Rate Limiting

GitHub API has rate limits (5000 requests/hour for authenticated requests).

**Solution**:
- The script includes a delay between requests (default 1 second)
- Increase delay with `--delay 2.0` if you hit rate limits
- For GitHub Actions, the default 1.5s delay should be sufficient

## Automation

### Scheduled Triggers

To automatically trigger workflows on all repos on a schedule, modify the workflow:

```yaml
# In workflows/trigger-all-repos.yml
on:
  workflow_dispatch:
    # ... existing inputs ...
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
```

### Triggered by Events

To trigger workflows on all repos when something happens in .github:

```yaml
on:
  push:
    branches:
      - main
    paths:
      - 'workflow-templates/**'
```

## Best Practices

1. **Always test with `--check-only` first** to see which repos will be affected
2. **Use appropriate delays** to avoid rate limiting
3. **Monitor the Actions tab** to see the triggered workflows
4. **Keep your PAT secure** - never commit it to the repository
5. **Rotate your PAT regularly** for security
6. **Use specific refs** when triggering on non-default branches

## Security Considerations

- The `GH_PAT` secret has significant permissions - protect it carefully
- Only organization members with appropriate access should be able to trigger this workflow
- Consider using GitHub Apps instead of PATs for better security and auditing
- Regularly review what workflows are being triggered and by whom

## See Also

- [GitHub Actions workflow_dispatch documentation](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_dispatch)
- [GitHub REST API - Actions](https://docs.github.com/en/rest/actions/workflows)
- [Managing your personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
