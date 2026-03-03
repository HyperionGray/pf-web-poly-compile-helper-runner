# Auto-Assign Copilot Workflow Documentation

## Overview

The `auto-assign-copilot.yml` workflow automatically assigns GitHub Copilot to issues labeled with `copilot` and provides model selection capabilities through additional labels.

## Features

### 1. Automatic Label Creation
When the workflow runs, it automatically creates the following labels in your repository if they don't exist:

- **`copilot`** (Green: #0E8A16)
  - Description: "Assign this issue to GitHub Copilot"
  - Purpose: Triggers Copilot assignment

- **`copilot-gpt-5.1-codex`** (Blue: #1D76DB)
  - Description: "Use GPT-5.1-Codex model for Copilot"
  - Purpose: Best for code generation and analysis

- **`copilot-gpt-5.1`** (Purple: #5319E7)
  - Description: "Use GPT-5.1 model for Copilot"
  - Purpose: Latest GPT model

- **`copilot-claude-4.5-opus`** (Orange: #D93F0B)
  - Description: "Use Claude 4.5 Opus model for Copilot"
  - Purpose: Claude model for code review

### 2. Automatic Assignment
When an issue is labeled with `copilot`, the workflow:
- Assigns the issue to the `@copilot` user
- Adds an informational comment explaining the process
- Lists available model selection options

### 3. Model Selection
You can specify which Copilot model to use by adding one of the model labels:
- Add `copilot-gpt-5.1-codex` for code-focused tasks
- Add `copilot-gpt-5.1` for general AI assistance
- Add `copilot-claude-4.5-opus` for code review tasks

The workflow will detect which model label is present and mention it in the informational comment.

## Installation

### Option 1: Via Workflows Sync (Recommended)
The workflow template is located at `workflow-templates/auto-assign-copilot.yml` and can be distributed to all repositories using the workflows-sync mechanism:

```bash
# Sync to all repos in P4X-ng
python trigger_workflow_all_repos.py P4X-ng workflows-sync.yml

# Sync to all accounts (P4X-ng, HyperionGray, TeamHG-Memex, hyp3ri0n-ng)
python trigger_workflow_all_repos.py --all-accounts workflows-sync.yml
```

### Option 2: Manual Installation
Copy the workflow file to your repository:

```bash
mkdir -p .github/workflows
cp workflow-templates/auto-assign-copilot.yml .github/workflows/
git add .github/workflows/auto-assign-copilot.yml
git commit -m "Add auto-assign-copilot workflow"
git push
```

## Usage

### Basic Usage
1. Open a new issue in any repository with the workflow installed
2. Add the `copilot` label to the issue
3. The workflow will:
   - Create all required labels (if they don't exist)
   - Assign `@copilot` to the issue
   - Add an informational comment

### With Model Selection
1. Open a new issue
2. Add the `copilot` label
3. Add one of the model labels (e.g., `copilot-gpt-5.1-codex`)
4. The workflow will note the selected model in its comment

### Checking Deployment Status

Use the included Python script to check which repositories have the workflow:

```bash
# Check P4X-ng repositories
python trigger_auto_assign_copilot.py P4X-ng --check-only

# Check all accounts
python trigger_auto_assign_copilot.py --all-accounts --check-only

# Check with label status
python trigger_auto_assign_copilot.py P4X-ng --check-labels
```

## How It Works

### Workflow Triggers
The workflow runs on two issue events:
- `opened`: When a new issue is created (if it has the `copilot` label)
- `labeled`: When any label is added to an issue (checks for `copilot` label)

### Job Flow

#### Job 1: ensure-labels
- **Purpose**: Creates required labels if they don't exist
- **When**: Runs on issue opened or when `copilot` label is added
- **Permissions**: `issues: write`
- **Actions**:
  - Lists all existing labels in the repository
  - Creates any missing labels from the required set
  - Logs creation status

#### Job 2: auto-assign
- **Purpose**: Assigns Copilot and adds informational comment
- **Depends on**: ensure-labels
- **When**: Only if issue has `copilot` label
- **Permissions**: `issues: write`
- **Actions**:
  1. Check if `@copilot` is already assigned
  2. Assign `@copilot` if not already assigned
  3. Detect which model label (if any) is present
  4. Add informational comment (only once)

## Permissions

The workflow uses minimal required permissions:
- `issues: write` - To create labels, assign issues, and add comments
- Uses `GITHUB_TOKEN` (automatically provided by GitHub Actions)

## Requirements

### Repository Requirements
- GitHub Actions must be enabled
- The repository must have GitHub Copilot access (for assignment to work)

### Organization Requirements
- A Copilot seat must be assigned to your organization/account
- The `@copilot` user must be accessible in your organization

## Troubleshooting

### Issue: "Failed to assign Copilot"
**Cause**: The repository doesn't have Copilot access or Copilot seat not assigned.

**Solution**: 
- Ensure your organization has GitHub Copilot Business/Enterprise
- Verify Copilot seat is assigned to your org
- Check that the repository has Copilot enabled

### Issue: Labels not created
**Cause**: Insufficient permissions or workflow didn't run.

**Solution**:
- Check that GitHub Actions has `issues: write` permission
- Verify the workflow ran (check Actions tab)
- Check workflow logs for error messages

### Issue: Workflow doesn't trigger
**Cause**: Workflow file not in `.github/workflows/` or syntax error.

**Solution**:
- Verify file is at `.github/workflows/auto-assign-copilot.yml`
- Check workflow syntax with: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/auto-assign-copilot.yml'))"`
- Look for errors in Actions tab

## Advanced Configuration

### Customizing Labels
Edit the workflow file to modify label colors, names, or descriptions:

```yaml
const requiredLabels = [
  {
    name: 'copilot',
    color: '0E8A16',  # Change color (hex without #)
    description: 'Your description'
  },
  # Add more labels...
];
```

### Changing Assignee
If your organization uses a different username for Copilot, update:

```yaml
const copilotUsername = "copilot";  # Change to your username
```

### Customizing Comment
Edit the comment template in the workflow:

```yaml
let message = '🤖 **GitHub Copilot has been assigned to this issue!**\n\n';
# Modify as needed...
```

## Examples

### Example 1: Basic Issue with Copilot
```
Title: Fix authentication bug
Labels: bug, copilot

Result:
- @copilot assigned
- Comment added with model selection options
```

### Example 2: Issue with Model Selection
```
Title: Refactor user service
Labels: refactor, copilot, copilot-gpt-5.1-codex

Result:
- @copilot assigned
- Comment mentions GPT-5.1-Codex selected
```

### Example 3: Multiple Model Labels
```
Title: Code review needed
Labels: copilot, copilot-claude-4.5-opus

Result:
- @copilot assigned
- Comment mentions Claude 4.5 Opus selected
- (First model label found is used)
```

## Integration with Other Workflows

This workflow complements other Copilot workflows in the organization:
- Works alongside code review workflows
- Compatible with issue templates
- Integrates with project automation
- Can be combined with auto-labeling workflows

## Related Files

- **Workflow**: `.github/workflows/auto-assign-copilot.yml`
- **Template**: `workflow-templates/auto-assign-copilot.yml`
- **Checker Script**: `trigger_auto_assign_copilot.py`
- **General Trigger Script**: `trigger_workflow_all_repos.py`

## Further Reading

- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)
- [GitHub Actions Workflows](https://docs.github.com/en/actions/using-workflows)
- [Issue Labels API](https://docs.github.com/en/rest/issues/labels)
- [HOW_TO_APPLY_TO_ALL_REPOS.md](./HOW_TO_APPLY_TO_ALL_REPOS.md) - Workflow sync guide
- [TRIGGER_WORKFLOWS_GUIDE.md](./TRIGGER_WORKFLOWS_GUIDE.md) - Workflow triggering guide
