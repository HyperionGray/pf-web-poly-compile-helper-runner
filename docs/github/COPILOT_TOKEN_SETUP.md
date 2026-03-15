# GitHub Copilot Token Setup Guide

This guide explains how to set up the required `COPILOT_TOKEN` secret for workflows that use GitHub Copilot CLI actions (such as `auto-gpt5-implementation.yml`).

## Why is COPILOT_TOKEN Required?

The default `GITHUB_TOKEN` provided in GitHub Actions workflows does not have access to GitHub Copilot's API. To use Copilot CLI actions in your workflows, you need to create a Personal Access Token (PAT) with Copilot access.

## Prerequisites

- You must have an active GitHub Copilot subscription (Individual, Business, or Enterprise)
- You need admin access to the repository where you want to use the workflow

## Step-by-Step Setup

### 1. Create a Personal Access Token

1. Go to GitHub Settings: https://github.com/settings/tokens
2. Click **"Developer settings"** in the left sidebar
3. Click **"Personal access tokens"** → **"Tokens (classic)"** or **"Fine-grained tokens"**
4. Click **"Generate new token"**

#### For Classic Tokens:
- Give your token a descriptive name (e.g., "Copilot CLI Workflow Token")
- Set an appropriate expiration (recommended: 90 days or less for security)
- Select the following scopes:
  - ✅ `repo` (Full control of private repositories) - if using in private repos
  - ✅ `workflow` (Update GitHub Action workflows)
  - ✅ `copilot` (Access GitHub Copilot)
- Click **"Generate token"**
- **IMPORTANT**: Copy the token immediately - you won't be able to see it again!

#### For Fine-grained Tokens:
- Give your token a descriptive name
- Select the resource owner (your account or organization)
- Set repository access (All repositories or Selected repositories)
- Set the following repository permissions:
  - Contents: Read and write
  - Pull requests: Read and write
  - Issues: Read and write
  - Workflows: Read and write
- Add Copilot access under Account permissions
- Click **"Generate token"**
- **IMPORTANT**: Copy the token immediately!

### 2. Add the Token as a Repository Secret

#### For a Single Repository:
1. Go to your repository on GitHub
2. Click **"Settings"** → **"Secrets and variables"** → **"Actions"**
3. Click **"New repository secret"**
4. Name: `COPILOT_TOKEN`
5. Value: Paste the token you just created
6. Click **"Add secret"**

#### For an Organization (applies to all repos):
1. Go to your organization settings
2. Click **"Secrets and variables"** → **"Actions"**
3. Click **"New organization secret"**
4. Name: `COPILOT_TOKEN`
5. Value: Paste the token
6. Select repository access (all repositories or selected)
7. Click **"Add secret"**

### 3. Verify the Setup

Once you've added the secret:
1. The workflow will automatically use `${{ secrets.COPILOT_TOKEN }}` 
2. No code changes are needed if the workflow is already configured correctly
3. Test by triggering the workflow manually or creating a PR

## Security Best Practices

- ✅ Use token expiration dates and rotate tokens regularly
- ✅ Grant minimum necessary permissions
- ✅ Use fine-grained tokens when possible (more secure)
- ✅ Never commit tokens directly in code
- ✅ Review token usage regularly in GitHub audit logs
- ✅ Revoke tokens immediately if compromised

## Troubleshooting

### Error: "Unable to resolve action github/copilot-cli-actions"
**Solution**: The workflow is using an incorrect action reference. Update to use `austenstone/copilot-cli-action@v2` instead.

### Error: "Authentication failed" or "401 Unauthorized"
**Solution**: 
- Verify the `COPILOT_TOKEN` secret is set correctly
- Ensure your token has the `copilot` scope
- Check that your Copilot subscription is active

### Error: "Resource not accessible by integration"
**Solution**: 
- Ensure the token has `repo` and `workflow` scopes
- For organization repos, verify the organization allows PATs

### Workflow runs but produces no output
**Solution**: 
- Check that you're using the correct parameter names (`prompt` not `query`, `copilot-token` not `GITHUB_TOKEN`)
- Verify the action version is `@v2` or later

## Related Workflows

The following workflows in this repository require `COPILOT_TOKEN`:
- `auto-gpt5-implementation.yml` - GPT-5 Advanced Code Analysis
- `auto-copilot-functionality-docs-review.yml` - Documentation Review
- `auto-copilot-code-cleanliness-review.yml` - Code Cleanliness Review
- `auto-copilot-test-review-playwright.yml` - Test Review with Playwright

## Additional Resources

- [GitHub Copilot CLI Documentation](https://docs.github.com/en/copilot/how-tos/use-copilot-agents/use-copilot-cli)
- [GitHub Copilot CLI Action (Marketplace)](https://github.com/marketplace/actions/github-copilot-cli)
- [Creating Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [Using Secrets in GitHub Actions](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
