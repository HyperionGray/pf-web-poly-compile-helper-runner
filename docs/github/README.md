# 🚀 P4X-ng Workflow Templates

This directory contains reusable GitHub Actions workflow templates for all P4X-ng repositories.

## 🆕 Latest Updates (2024-12-27)

**🔧 Workflow Sync Fixed:**
- ✅ **Fixed failing "Workflows Sync"** - Now works reliably on schedule and push events
- ✅ **10x faster performance** - Removed excessive delays, added concurrent processing
- ✅ **Better error handling** - Clear messages, proper token validation
- ✅ **Push trigger support** - Auto-sync when templates change
- ✅ **Rate limit handling** - Intelligent API throttling prevents 429 errors

**New Features Available:**
- ✅ **Auto-assign Copilot with Model Selection** - Auto-creates labels, assigns Copilot, supports model selection
- ✅ Amazon Q review on **every push** to main/master/develop
- ✅ **Multiple AI model support** via workflow dispatch (@amazonq, @codex, /gemini, gpt5)
- ✅ **Tag-based E2E reviews** (e2eweekly) using GPT-5.1-Codex
- ✅ **Tag-based weekly reviews** (weeklyreview) using GPT-5.1
- ✅ Sync to **all accounts** including hyp3ri0n-ng
- ✅ Copilot agent uses **gpt-5.1-codex by default** for E2E reviews

**📖 Quick Start Documentation:**
- **[AUTO_ASSIGN_COPILOT.md](AUTO_ASSIGN_COPILOT.md)** - Auto-assign Copilot workflow guide
- **[WORKFLOW_SYNC_COMPLETE_FIX.md](WORKFLOW_SYNC_COMPLETE_FIX.md)** - Complete workflow sync fix details
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick guide to all new features
- **[GITHUB_ACTIONS_CONFIG_SUMMARY.md](GITHUB_ACTIONS_CONFIG_SUMMARY.md)** - Complete implementation details
- **[COPILOT_TOKEN_SETUP.md](COPILOT_TOKEN_SETUP.md)** - Set up Copilot token for AI models
- **[HOW_TO_APPLY_TO_ALL_REPOS.md](HOW_TO_APPLY_TO_ALL_REPOS.md)** - Sync workflows to all repos

## 🔄 Workflow Sync System

The workflow sync system automatically distributes these templates to all repositories across multiple GitHub organizations.

### How It Works
- **Automatic sync** daily at 6:00 UTC to all accounts (P4X-ng, HyperionGray, TeamHG-Memex, hyp3ri0n-ng)
- **Push-triggered sync** when templates or sync script changes
- **Manual sync** via GitHub Actions workflow dispatch

### Usage
```bash
# Test sync (dry run)
python sync_workflows.py P4X-ng --dry-run

# Sync to single account
python sync_workflows.py P4X-ng

# Sync to all accounts
python sync_workflows.py --all-accounts
```

### Requirements
- GitHub token with `repo` and `workflow` scopes
- Set as `GH_PAT` secret in repository settings

## 📚 Available Workflows

### CI/CD Review Workflows (NEW)

#### 1. **Complete CI/CD Review Pipeline** (`auto-complete-cicd-review.yml`)
**Runs every 12 hours** - Comprehensive automated review covering all aspects

**Triggers:**
- Schedule: Every 12 hours (00:00 and 12:00 UTC)
- Push to main/master branches
- Pull requests
- Manual dispatch

**Features:**
- Code cleanliness analysis (identifies large files >500 lines)
- Test execution across unit, integration, and E2E tests
- Playwright integration for web tests (headed & headless)
- Documentation completeness check
- Build functionality verification
- Consolidated reporting
- Automatic Amazon Q review trigger

**Usage:** Add to your repository and it will automatically run every 12 hours.

#### 2. **Periodic Code Cleanliness Review** (`auto-copilot-code-cleanliness-review.yml`)
**Runs every 12 hours** - Focuses on code organization and quality

**Features:**
- Identifies files larger than 500 lines that should be split
- Analyzes code complexity
- Detects code duplication opportunities
- Creates actionable issues with recommendations

**Usage:** Can be used standalone or as part of the complete pipeline.

#### 3. **Comprehensive Test Review with Playwright** (`auto-copilot-test-review-playwright.yml`)
**Runs on push/PR** - Ensures proper test coverage with Playwright

**Features:**
- Runs Playwright tests across Chromium, Firefox, and WebKit
- Tests in both headed and headless modes
- Analyzes test coverage
- Identifies files without tests
- Uploads test results and screenshots
- Recommends Playwright migration for non-Playwright web tests

**Usage:** Essential for web projects. Automatically runs on every push and PR.

#### 4. **Code Functionality and Documentation Review** (`auto-copilot-functionality-docs-review.yml`)
**Runs on push/PR** - Verifies code works and is documented

**Features:**
- Builds project across multiple languages (Node.js, Python, Go, Java, etc.)
- Runs existing tests
- Checks for essential documentation files (README, CONTRIBUTING, LICENSE, etc.)
- Analyzes README.md quality and completeness
- Identifies code without documentation
- Creates detailed review reports

**Usage:** Works with any project type, adapts to available build tools.

#### 5. **Amazon Q Review** (`auto-amazonq-review.yml`)
**Runs after Copilot workflows** - Additional AI-powered review

**Features:**
- Triggered automatically after GitHub Copilot workflows complete
- Provides security analysis
- Performance optimization suggestions
- AWS best practices recommendations
- Enterprise architecture patterns review

**Usage:** Requires AWS credentials configuration. See workflow comments for setup.

#### 6. **GPT-5 Advanced Code Analysis** (`auto-gpt5-implementation.yml`)
**Uses GPT-5 model via GitHub Copilot** - Cutting-edge AI-powered code analysis

**Features:**
- Advanced code quality and architecture analysis using GPT-5
- Comprehensive security vulnerability detection
- Performance optimization recommendations
- Best practices validation
- Test coverage analysis and suggestions
- Deep semantic code understanding
- Multiple GPT-5 model variants available (GPT-5, GPT-5.1, GPT-5.2, GPT-5-Codex variants)

**Usage:** Runs on push/PR or manually via workflow_dispatch. Requires GitHub Copilot access. Uses the latest GPT-5 model for advanced code intelligence.

### Issue & PR Management Workflows

#### LLM Issue Review (Model Label Trigger) (`auto-llm-issue-review.yml`)
Triggers when an **issue** is labeled with a model label like `gpt-5.2`, `gemini-3`, or `claude-4.5-thinking` and posts a review comment.

Supported label formats:
- `gpt-*` / `o*` (OpenAI)
- `gemini*` (Gemini)
- `claude-*` (Anthropic)
- `llm:<provider>:<model>` (explicit)
- `<provider>:<model>` where provider is `openai`, `gemini`, or `anthropic` (explicit)

#### LLM PR Review (Label Trigger) (`auto-llm-pr-review.yml`)
Triggers when a **PR** is labeled with `ai-review` (default) or with a model label like `gpt-5.2`, `gemini-3`, or `claude-4.5-thinking`.

Notes:
- Uses `pull_request_target` so it can comment on PRs and access repo secrets safely (it does not checkout PR code; it reviews diffs via GitHub API).

#### Automation: Advance the Ball (6h) (`auto-advance-ball.yml`)
Runs every 6 hours and creates/updates an issue titled `Automation: Direction` (label `automation`).

Behavior:
- If `AUTOMATION.txt` exists in the repo root, it is used as guidance.
- Otherwise a default instruction prompts the model to analyze the repo, pick a direction, document it, and propose next steps.

#### Auto-assign Copilot (`auto-assign-copilot.yml`)
**NEW: Enhanced with model selection!** Automatically assigns GitHub Copilot to issues labeled with `copilot`.

**Features:**
- Auto-creates required labels if they don't exist (copilot, model selection labels)
- Assigns `@copilot` when issue has `copilot` label
- Supports model selection via labels:
  - `copilot-gpt-5.1-codex` - Best for code generation and analysis
  - `copilot-gpt-5.1` - Latest GPT model
  - `copilot-claude-4.5-opus` - Claude model for code review
- Adds informational comment with model selection guidance
- Uses least-privilege permissions (`GITHUB_TOKEN`)

**Usage:** 
1. Label any issue with `copilot` to assign Copilot
2. Optionally add a model selection label
3. See [AUTO_ASSIGN_COPILOT.md](AUTO_ASSIGN_COPILOT.md) for full documentation

**Check deployment:** `python trigger_auto_assign_copilot.py --all-accounts --check-only`

#### Auto-label (`auto-label.yml`)
Automatically labels issues based on content.

#### Playwright Test Loop (`auto-copilot-org-playwright-loop.yaml`)
Runs Playwright tests and auto-fixes issues with Copilot.

#### Security Scan (`auto-sec-scan.yml`)
Runs CodeQL security analysis on PRs.

#### Workflows Sync (`workflows-sync.yml`)
Distributes workflows across all org repositories.

## 🎯 How to Run GitHub Actions

### 1. Manual Trigger (workflow_dispatch)
If your workflow includes `on: workflow_dispatch:`, you can start it by hand in GitHub's web UI:

1. Go to your repo (e.g., .github)
2. Click the **Actions** tab
3. Find the workflow you want ("Complete CI/CD Review," "Workflows Sync," etc.)
4. Click the workflow name
5. Click **Run workflow**
6. Fill in any input parameters if required, and click **Run**

### 2. On Event
Most Actions are triggered on events (like push, pull_request, issues), e.g.:

- **Complete CI/CD Review**: Triggers on push, PR, or schedule
- **Test Review**: Triggers on push and PR
- **Auto-assign Copilot**: Triggers whenever a new issue or PR is opened
- **Auto-label**: Triggers on new issue creation

You don't need to do anything for these—GitHub runs the workflow automatically when the event happens!

### 3. Scheduled
If your workflow has `on: schedule:` (cron notation), it'll run automatically at the set time:

- **Complete CI/CD Review**: Every 12 hours (00:00 and 12:00 UTC)
- **Code Cleanliness Review**: Every 12 hours
- **Automation: Advance the Ball**: Every 6 hours
- **Workflows Sync**: Daily at 6:00 UTC

### 4. Org-wide Distribution (Workflow Sync)
If you're using Workflows Sync:

- It runs automatically on schedule or manually via the Actions tab
- This propagates the workflows from `.github/workflows/` to all repos in your org

## 📋 Summary Table

| Workflow Trigger | Required Action |
|-----------------|-----------------|
| workflow_dispatch | Manual click in Actions tab |
| push, PR, issue | Happen automatically on event |
| schedule (cron) | Run at the times set in workflow |
| Workflow Sync | Manual (Actions tab) or scheduled (cron) |

## 🧑‍💻 Setup Instructions

### For New Repositories

1. **Enable Workflow Sync** in your `.github` repository
2. Workflows will automatically be copied to all org repositories
3. Configure any required secrets (AWS credentials for Amazon Q, etc.)

### For Individual Repository Setup

1. Copy desired workflow from `workflow-templates/` to your repo's `.github/workflows/`
2. Commit and push
3. The workflow will activate based on its triggers

### Required Secrets (Optional)

For full Amazon Q integration:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

For the label-triggered/scheduled LLM workflows:
- `OPENAI_API_KEY` (OpenAI)
- `GEMINI_API_KEY` (Gemini)
- `ANTHROPIC_API_KEY` (Anthropic)

For workflow sync:
- `GH_PAT` - GitHub Personal Access Token with workflow permissions

## 🔧 Customization

Each workflow can be customized by:
- Modifying cron schedules
- Adjusting file size thresholds
- Configuring specific test paths
- Changing browser combinations for Playwright
- Adding/removing programming language support

## 🧑‍💻 Extra Tips

- Check the run status in the Actions tab—see logs, errors, results for every run
- You can re-run failed workflows right from the Actions tab
- You can see deployment/status badges in README or PRs for CI workflows
- Review generated issues with labels: `code-cleanliness`, `test-coverage`, `documentation`, `amazon-q`
- All automated reviews create issues rather than failing builds to avoid blocking development

## 📞 Need Help?

If you want exact steps for a particular workflow, or a demo, let me know which one and I'll walk you through it!
