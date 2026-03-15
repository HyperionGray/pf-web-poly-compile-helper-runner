# Solution: Triggering Workflows Across All Repositories

## Problem
- User asked: "how do we trigger the workflow on all repos?"
- Follow-up: "there should be approximately 19 repos - is this a permissions issue?"
- Only 3 repositories were visible via standard GitHub API searches

## Root Cause
The GitHub API search endpoints only return:
- Public repositories
- Private repositories the token has explicit access to

Without proper authentication, private repositories in the P4X-ng organization (approximately 16 out of 19) were not visible.

## Solution Implemented

### 1. Python Script: `trigger_workflow_all_repos.py`
A comprehensive command-line tool that:
- Uses the Organization API endpoint (`/orgs/{org}/repos`) to access ALL repositories
- Supports both public and private repositories with proper token
- Can trigger any workflow across all repos in the organization
- Includes check mode to verify workflow existence without triggering
- Has built-in rate limiting and error handling
- Provides detailed progress and summary output

**Key Features:**
- ✅ Discovers all repositories (public + private) with proper token
- ✅ Checks if workflow exists before attempting to trigger
- ✅ Supports workflow inputs for parameterized workflows
- ✅ Can include or exclude archived repositories
- ✅ Dry-run mode with `--check-only` flag
- ✅ Configurable delays for rate limiting

### 2. GitHub Actions Workflow: `trigger-all-repos.yml`
A user-friendly web interface to trigger workflows:
- Located in both `workflows/` and `workflow-templates/`
- Accessible via Actions tab → "Run workflow" button
- Provides input fields for all parameters
- Uses the Python script internally
- Generates workflow summary with results

**Inputs:**
- Workflow file name (required)
- Git reference (default: main)
- Include archived repos (checkbox)
- Check only mode (checkbox)

### 3. Comprehensive Documentation

#### `TRIGGER_WORKFLOWS_GUIDE.md`
Complete user guide covering:
- Overview of the solution
- The permissions issue explained
- Required token scopes
- Method 1: GitHub Actions workflow (UI)
- Method 2: Command-line script
- Common workflows to trigger
- Troubleshooting guide
- Automation options
- Best practices
- Security considerations

#### `GH_PAT_SETUP.md`
Step-by-step setup guide:
- Why the token is needed
- Token creation walkthrough
- Adding token to repository secrets
- Verification steps
- Troubleshooting common issues
- Security best practices
- Token rotation schedule

#### `README.md`
Quick reference guide:
- Repository overview
- Quick start instructions
- Structure and organization
- Common tasks
- Troubleshooting quick tips

### 4. Supporting Files
- `.gitignore` - Excludes Python cache and build artifacts
- `workflow-templates/trigger-all-repos.properties.json` - Workflow metadata

## Technical Details

### Required GitHub Token Scopes
```
✅ repo          - Full control of private repositories
✅ workflow      - Update GitHub Action workflows
✅ read:org      - Read organization membership and repositories
```

### API Endpoints Used
```
GET /orgs/{org}/repos                                    # List all org repos
GET /repos/{owner}/{repo}/actions/workflows/{workflow}   # Check workflow exists
POST /repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches  # Trigger workflow
```

### Token Storage
- Token stored as `GH_PAT` secret in repository settings
- Never exposed in logs or outputs
- Used only by the workflow runner

## Usage Examples

### Via GitHub Actions UI
1. Navigate to Actions tab
2. Select "Trigger Workflow on All Repos"
3. Click "Run workflow"
4. Fill in parameters
5. View results in workflow run logs

### Via Command Line
```bash
# List all repositories
python trigger_workflow_all_repos.py P4X-ng workflows-sync.yml --check-only

# Trigger workflow on all repos
export GITHUB_TOKEN="ghp_your_token_here"
python trigger_workflow_all_repos.py P4X-ng security-scan.yml

# Trigger with specific branch
python trigger_workflow_all_repos.py P4X-ng test.yml --ref develop

# Trigger with inputs
python trigger_workflow_all_repos.py P4X-ng deploy.yml \
  --input environment=production \
  --input version=1.2.3
```

## Validation

### Security
- ✅ CodeQL scan: 0 vulnerabilities found
- ✅ No hardcoded credentials
- ✅ Token obtained from environment/secret
- ✅ Input validation on all parameters
- ✅ Rate limiting implemented

### Functionality
- ✅ Python syntax validation passed
- ✅ YAML syntax validation passed
- ✅ Import tests passed
- ✅ Help output verified
- ✅ Error handling tested

### Code Quality
- ✅ Type hints on function signatures
- ✅ Comprehensive docstrings
- ✅ Clear variable names
- ✅ Proper error messages
- ✅ User-friendly output formatting

## Files Created/Modified

```
.gitignore                                           # New - Python/IDE exclusions
GH_PAT_SETUP.md                                      # New - Token setup guide
README.md                                            # Modified - Added quick start
TRIGGER_WORKFLOWS_GUIDE.md                           # New - Complete usage guide
trigger_workflow_all_repos.py                        # New - Main script
workflow-templates/trigger-all-repos.properties.json # New - Workflow metadata
workflow-templates/trigger-all-repos.yml             # New - Template version
workflows/trigger-all-repos.yml                      # New - Active workflow
```

## Impact

### Before
- ❌ Could only see 3 public repositories
- ❌ No way to trigger workflows across all repos
- ❌ Manual process required for each repository
- ❌ Private repositories invisible to API

### After
- ✅ Can see all ~19 repositories (with proper token)
- ✅ One-click workflow triggering via UI
- ✅ Automated bulk operations possible
- ✅ Full visibility into organization

## Next Steps for User

1. **Setup Token** (5 minutes)
   - Follow `GH_PAT_SETUP.md` instructions
   - Create PAT with required scopes
   - Add as `GH_PAT` secret

2. **Verify Setup** (2 minutes)
   - Run workflow with `check-only` enabled
   - Confirm all ~19 repos are listed
   - Verify workflow detection works

3. **Start Using** (immediate)
   - Trigger workflows across all repos
   - Automate organization-wide updates
   - Streamline DevOps processes

## Benefits

### For Operations
- ⚡ Trigger security scans org-wide
- ⚡ Deploy updates to all repos
- ⚡ Run tests across entire codebase
- ⚡ Sync configurations automatically

### For Developers
- 🎯 Simple UI-based triggering
- 🎯 Command-line option for automation
- 🎯 Clear documentation and examples
- 🎯 Built-in safety features

### For Security
- 🔒 Token-based authentication
- 🔒 Audit trail via GitHub Actions
- 🔒 No hardcoded credentials
- 🔒 Rate limiting prevents abuse

## Maintenance

### Regular Tasks
- Rotate `GH_PAT` token every 90 days
- Review triggered workflow logs
- Update documentation as needed
- Monitor for API changes

### Monitoring
- Check Actions tab for workflow runs
- Review rate limit headers if errors occur
- Verify all repos remain accessible
- Update token scopes if GitHub changes requirements

## Support Resources

- **Primary Guide**: `TRIGGER_WORKFLOWS_GUIDE.md`
- **Setup Help**: `GH_PAT_SETUP.md`
- **Quick Reference**: `README.md`
- **Script Help**: `python trigger_workflow_all_repos.py --help`

---

**Implementation Date**: 2025-11-14  
**PR**: #7 - Trigger workflow for all repositories  
**Status**: ✅ Complete - Ready for testing with proper token
