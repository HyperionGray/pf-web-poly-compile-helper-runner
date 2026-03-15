# 🤖 Copilot Auto-Assignment System

This repository includes an automated system for assigning GitHub Copilot to issues with model selection capabilities.

## How It Works

### Automatic Assignment
When an issue is created or labeled with the `copilot` label, it will be automatically assigned to the `copilot` user account.

### Model Selection
You can specify which Copilot model to use for the task through labels:

#### Available Models
- **`copilot-gpt-5.1`** - General purpose model (default)
- **`copilot-gpt-5.1-codex`** - Specialized for code generation and analysis
- **`copilot-claude-4.5-opus`** - Advanced reasoning and analysis

## Usage Methods

### Method 1: Issue Template (Recommended)
1. Create a new issue using the "🤖 Copilot Task" template
2. Select your preferred model from the dropdown
3. Fill in the task details
4. Submit the issue

The system will automatically:
- Add the `copilot` label
- Add the appropriate `copilot-model:` label
- Assign the issue to Copilot
- Add a comment with model information

### Method 2: Manual Labels
Add these labels to any issue:
- `copilot` (required) - Triggers auto-assignment
- `copilot-model:copilot-gpt-5.1-codex` (optional) - Specifies model

Example label combinations:
```
copilot, copilot-model:copilot-gpt-5.1-codex
copilot, copilot-model:copilot-claude-4.5-opus
copilot  # Uses default model (copilot-gpt-5.1)
```

### Method 3: Add Labels to Existing Issues
You can add the `copilot` label to any existing issue to trigger assignment.

## Workflows

### `auto-assign-copilot.yml`
- **Triggers:** Issue opened or labeled
- **Condition:** Issue has `copilot` label
- **Actions:**
  - Assigns issue to `copilot` user
  - Detects model selection from labels
  - Adds informational comment
  - Handles assignment errors gracefully

### `process-copilot-form.yml`
- **Triggers:** Issue opened
- **Condition:** Issue has `copilot` label
- **Actions:**
  - Extracts model selection from issue form
  - Adds appropriate `copilot-model:` label

## Model Selection Guide

### When to Use Each Model

#### `copilot-gpt-5.1` (Default)
- General programming questions
- Code explanations
- Basic debugging
- Documentation tasks

#### `copilot-gpt-5.1-codex`
- Code generation
- Complex algorithms
- Code refactoring
- Performance optimization
- API integrations

#### `copilot-claude-4.5-opus`
- Architecture decisions
- Complex problem analysis
- Code reviews requiring deep reasoning
- Security analysis
- System design

## Setup Requirements

### Repository Configuration
1. Ensure the `copilot` user has access to your repository
2. The `copilot` user must have a Copilot seat assigned
3. Repository must have Issues enabled

### Permissions
The workflows use `GITHUB_TOKEN` with these permissions:
- `issues: write` - To assign issues and add comments
- `contents: read` - To access repository content

## Troubleshooting

### Assignment Fails
If Copilot assignment fails, check:
1. Does the `copilot` user exist in your organization?
2. Does the `copilot` user have a Copilot seat?
3. Does the `copilot` user have access to the repository?

### Model Labels Not Working
1. Ensure labels follow the exact format: `copilot-model:model-name`
2. Check that the model name is one of the allowed values
3. Verify the issue has the base `copilot` label

### Issue Template Not Showing
1. Check that the file is at `.github/ISSUE_TEMPLATE/copilot-task.yml`
2. Ensure the YAML syntax is valid
3. Repository must have Issues enabled

## Examples

### Example Issue Creation
```markdown
Title: [COPILOT] Optimize database queries in user service

Labels: copilot, copilot-model:copilot-gpt-5.1-codex

Description:
Need help optimizing the database queries in the user service. 
The current queries are slow and causing performance issues.

Files involved:
- src/services/user-service.js
- src/models/user.js
```

### Example Label Addition
To convert an existing issue to a Copilot task:
1. Add the `copilot` label
2. Optionally add a model label like `copilot-model:copilot-claude-4.5-opus`
3. The workflow will trigger automatically

## Advanced Usage

### Custom Model Selection
If you need to use a different model or have special requirements, you can:
1. Create a custom label following the pattern `copilot-model:your-model`
2. Update the workflow's `allowedModels` array
3. Document the new model in this README

### Integration with Other Workflows
The Copilot assignment system works alongside other repository automation:
- Issues can have multiple labels
- Other workflows can also process Copilot-assigned issues
- The system respects existing assignees (won't duplicate assignments)

## Monitoring and Analytics

The workflows provide detailed logging:
- Model selection decisions
- Assignment success/failure
- Error handling and recovery

Check the Actions tab to monitor workflow execution and troubleshoot issues.