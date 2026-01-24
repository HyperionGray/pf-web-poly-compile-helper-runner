# Copilot Issue Reconciler

## Overview

The Copilot Issue Reconciler is a scheduled GitHub Actions workflow that ensures all issues labeled with `copilot` are properly assigned to the Copilot user and have appropriate model selection labels.

## Features

- **Scheduled Execution**: Runs automatically every 5 minutes
- **Manual Trigger**: Can be triggered manually via `workflow_dispatch`
- **Dry Run Mode**: Test mode that shows what would be changed without making actual modifications
- **Rate Limit Aware**: Includes delays and pagination to respect GitHub API limits
- **Comprehensive Logging**: Detailed logs for monitoring and debugging
- **Idempotent**: Safe to run multiple times without causing issues

## Workflow File

Location: `.github/workflows/copilot-issue-reconciler.yml`

## Triggers

### Automatic Schedule
- **Frequency**: Every 5 minutes (`*/5 * * * *`)
- **Purpose**: Catch issues that may have been missed by event-driven triggers

### Manual Dispatch
- **Trigger**: `workflow_dispatch` in GitHub Actions UI
- **Parameters**:
  - `dry_run` (boolean, default: false): Run in test mode without making changes
  - `max_issues` (string, default: "20"): Maximum number of issues to process per run

## What It Does

### 1. Issue Assignment
- Queries for all open issues with the `copilot` label
- Identifies issues not assigned to the `copilot` user
- Assigns the `copilot` user to those issues

### 2. Model Selection
- Checks for existing model labels on copilot issues
- Adds default model label if none exists
- Uses label format: `model:copilot-gpt-5.1-codex`

### Supported Models
- `copilot-gpt-5.1-codex` (default)
- `copilot-gpt-5.1`
- `copilot-claude-4.5-opus`

## Configuration

### Required Permissions
```yaml
permissions:
  issues: write
  contents: read
```

### Required Secrets
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions

### Configurable Parameters
- **Copilot Username**: Currently hardcoded as `"copilot"`
- **Default Model**: Currently set to `"copilot-gpt-5.1-codex"`
- **Max Issues Per Run**: Default 20, configurable via workflow input
- **Rate Limit Delays**: 100ms between API calls

## Usage Examples

### Manual Execution (Dry Run)
1. Go to Actions tab in GitHub repository
2. Select "Copilot Issue Reconciler" workflow
3. Click "Run workflow"
4. Set `dry_run` to `true`
5. Click "Run workflow"

### Manual Execution (Live)
1. Go to Actions tab in GitHub repository
2. Select "Copilot Issue Reconciler" workflow
3. Click "Run workflow"
4. Leave `dry_run` as `false` (default)
5. Optionally adjust `max_issues`
6. Click "Run workflow"

## Monitoring

### Log Output
The workflow provides detailed logging including:
- Number of issues found and processed
- Assignment actions taken
- Model labeling actions taken
- Error messages and counts
- Summary statistics

### Example Log Output
```
🔄 Starting Copilot Issue Reconciler...
📊 Max issues to process: 20
🧪 Dry run mode: false
👤 Target assignee: copilot
🤖 Allowed models: copilot-gpt-5.1-codex, copilot-gpt-5.1, copilot-claude-4.5-opus
🎯 Default model: copilot-gpt-5.1-codex

🔍 Querying for open issues with 'copilot' label...
📋 Found 3 open issues with 'copilot' label
🎯 Processing 3 issues (limited by max_issues: 20)

--- Processing Issue #123: "Add new feature" ---
👥 Current assignees: none
🏷️  Current labels: copilot, enhancement
❓ Needs assignment: true
❓ Has model label: false
✅ Assigned @copilot to issue #123
✅ Added model label 'model:copilot-gpt-5.1-codex' to issue #123

📊 === Reconciliation Summary ===
🔢 Issues processed: 3
👤 Issues assigned to copilot: 2
🏷️  Issues labeled with model: 2
❌ Errors encountered: 0
🧪 Dry run mode: false
✅ Reconciliation completed successfully with changes applied.
```

## Error Handling

### Common Issues and Solutions

#### Copilot User Not Found
- **Error**: "not found" when assigning copilot
- **Solution**: Ensure the `copilot` user exists and has access to the repository

#### Rate Limiting
- **Behavior**: Automatic delays between API calls
- **Mitigation**: Workflow processes maximum 20 issues per run by default

#### Permission Issues
- **Error**: Insufficient permissions
- **Solution**: Verify workflow has `issues: write` permission

## Integration with Existing Workflows

This reconciler complements the existing event-driven assignment workflow (`auto-assign-copilot.yml`):

- **Event-driven**: Handles issues immediately when labeled
- **Scheduled reconciler**: Catches any missed issues and ensures consistency

Both workflows are idempotent and safe to run together.

## Customization

### Changing the Copilot Username
Edit line 32 in the workflow file:
```javascript
const copilotUsername = "your-copilot-username";
```

### Changing the Default Model
Edit line 38 in the workflow file:
```javascript
const defaultModel = "copilot-gpt-5.1"; // or other allowed model
```

### Adding New Models
Edit the `allowedModels` array on lines 33-37:
```javascript
const allowedModels = [
  "copilot-gpt-5.1-codex",
  "copilot-gpt-5.1", 
  "copilot-claude-4.5-opus",
  "your-new-model"
];
```

### Changing the Schedule
Edit the cron expression on line 5:
```yaml
- cron: '*/10 * * * *' # Every 10 minutes instead of 5
```

## Troubleshooting

### Workflow Not Running
1. Check if the workflow file is in the correct location
2. Verify the cron syntax is valid
3. Ensure the repository has Actions enabled

### No Issues Being Processed
1. Verify issues have the exact label `copilot`
2. Check if issues are in `open` state
3. Review the workflow logs for query results

### Assignment Failures
1. Confirm the copilot user exists
2. Check repository permissions for the copilot user
3. Verify the `GITHUB_TOKEN` has sufficient permissions

## Security Considerations

- Uses only the built-in `GITHUB_TOKEN`
- No external API calls or third-party actions
- Minimal permissions required (`issues: write`, `contents: read`)
- All operations are logged for audit purposes