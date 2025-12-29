# Creating GitHub Issues from Test Documentation

This guide explains how to create the 5 GitHub issues from the provided markdown files.

## Overview

We have created 5 comprehensive issue documents that need to be converted into GitHub issues. Each document contains all the information needed for a complete issue.

## Issue Files

1. `ISSUE_1_CORE_INSTALL_FILES.md` - Core installation files testing
2. `ISSUE_2_ALWAYS_ON_INSTALL_FILES.md` - Always-on files testing
3. `ISSUE_3_TOOL_INSTALL_FILES.md` - Tool installation testing
4. `ISSUE_4_PACKAGE_CONTAINER_FILES.md` - Package/container testing
5. `ISSUE_5_SECURITY_TUI_FILES.md` - Security/TUI testing

## Method 1: Manual Creation via GitHub UI

### Steps for Each Issue

1. **Navigate to GitHub**
   - Go to: https://github.com/HyperionGray/pf-web-poly-compile-helper-runner/issues/new

2. **Copy Issue Title**
   - From the markdown file's first heading (e.g., "Test Core Installation .pf Files")

3. **Copy Issue Body**
   - Copy the entire content from the markdown file
   - Paste into the issue body

4. **Add Labels**
   - `testing` - For all issues
   - `documentation` - For documentation-related aspects
   - `high-priority` - For Issues #1 and #2
   - `medium-priority` - For Issues #3, #4, and #5

5. **Set Priority Emojis**
   - Issues #1 and #2: 🔴 High
   - Issues #3, #4, and #5: 🟡 Medium

6. **Create Issue**
   - Click "Submit new issue"

## Method 2: Using GitHub CLI (gh)

If you have GitHub CLI installed, you can create issues quickly:

```bash
# Install gh CLI if needed
# https://cli.github.com/

# Navigate to repository
cd /home/runner/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner

# Create Issue #1
gh issue create \
  --title "Test Core Installation .pf Files" \
  --body-file ISSUE_1_CORE_INSTALL_FILES.md \
  --label "testing,high-priority"

# Create Issue #2
gh issue create \
  --title "Test Always-On Installation .pf Files" \
  --body-file ISSUE_2_ALWAYS_ON_INSTALL_FILES.md \
  --label "testing,high-priority"

# Create Issue #3
gh issue create \
  --title "Test Tool Installation .pf Files" \
  --body-file ISSUE_3_TOOL_INSTALL_FILES.md \
  --label "testing,medium-priority"

# Create Issue #4
gh issue create \
  --title "Test Package Manager and Container Installation .pf Files" \
  --body-file ISSUE_4_PACKAGE_CONTAINER_FILES.md \
  --label "testing,medium-priority"

# Create Issue #5
gh issue create \
  --title "Test Security and TUI Installation .pf Files" \
  --body-file ISSUE_5_SECURITY_TUI_FILES.md \
  --label "testing,medium-priority"
```

## Method 3: Using GitHub API

You can also use the GitHub API with curl:

```bash
# Set your GitHub token
GITHUB_TOKEN="your_github_token"
REPO="HyperionGray/pf-web-poly-compile-helper-runner"

# Create Issue #1
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/$REPO/issues \
  -d @- << EOF
{
  "title": "Test Core Installation .pf Files",
  "body": "$(cat ISSUE_1_CORE_INSTALL_FILES.md)",
  "labels": ["testing", "high-priority"]
}
EOF

# Repeat for Issues #2-5...
```

## Issue Summary

### Issue #1: Core Installation Files
- **Priority:** 🔴 High
- **Labels:** testing, high-priority
- **Files:** Pfyfile.always-available.pf, Pfyfile.pf
- **Tasks:** 37 installation tasks

### Issue #2: Always-On Installation Files
- **Priority:** 🔴 High
- **Labels:** testing, high-priority
- **Files:** pf-runner/Pfyfile.always-on-*.pf (4 files)
- **Tasks:** 14 installation tasks

### Issue #3: Tool Installation Files
- **Priority:** 🟡 Medium
- **Labels:** testing, medium-priority
- **Files:** Pfyfile.debug-tools.pf, Pfyfile.exploit.pf, etc. (4 files)
- **Tasks:** 17 installation tasks

### Issue #4: Package Manager and Container Files
- **Priority:** 🟡 Medium
- **Labels:** testing, medium-priority
- **Files:** Pfyfile.package-manager.pf, Pfyfile.containers.pf, etc. (3 files)
- **Tasks:** 12 installation tasks

### Issue #5: Security and TUI Files
- **Priority:** 🟡 Medium
- **Labels:** testing, medium-priority
- **Files:** Pfyfile.security.pf, Pfyfile.tui.pf, etc. (5 files)
- **Tasks:** 8 installation tasks

## After Creating Issues

1. **Link Issues Together**
   - Add references between related issues
   - Link to the main testing documentation

2. **Add to Project Board** (if applicable)
   - Create a "Installation Testing" project
   - Add all 5 issues to the project
   - Set up columns: To Do, In Progress, Done

3. **Assign Team Members**
   - Assign appropriate team members to each issue
   - Distribute based on expertise

4. **Set Milestones** (optional)
   - Create a milestone for "Installation Testing Q1 2025"
   - Assign all 5 issues to this milestone

5. **Update Documentation**
   - Link the created issues in README.md
   - Update TESTING_INSTALL_PF_FILES.md with issue numbers

## Verification Checklist

After creating all issues:

- [ ] All 5 issues are created
- [ ] Titles match the markdown file headings
- [ ] Bodies contain full markdown content
- [ ] Labels are applied correctly
- [ ] Priorities are set appropriately
- [ ] Issues are linked to this PR
- [ ] Team members are assigned (if applicable)
- [ ] Issues are added to project board (if applicable)

## Example: Issue #1 Details

When created, Issue #1 should look like:

```
Title: Test Core Installation .pf Files

Labels: testing, high-priority

Body:
# Issue #1: Test Core Installation .pf Files

## Summary
Test and validate core installation .pf files to ensure all install tasks work correctly.

[... rest of markdown content ...]
```

## Troubleshooting

### Issue Body Too Long
If the markdown content exceeds GitHub's limit:
1. Create a shorter summary for the issue body
2. Link to the full markdown file in the repository

### Labels Don't Exist
If the labels don't exist in your repository:
1. Go to Issues → Labels
2. Create the necessary labels:
   - `testing` (color: #1d76db)
   - `high-priority` (color: #d73a4a)
   - `medium-priority` (color: #fbca04)

### Permission Issues
If you can't create issues:
1. Check you have write access to the repository
2. Verify your GitHub token has `repo` scope
3. Contact repository administrator for permissions

## Related Documentation

- [TESTING_INSTALL_PF_FILES.md](TESTING_INSTALL_PF_FILES.md) - Master testing documentation
- [TEST_RESULTS_INSTALL_PF_FILES.md](TEST_RESULTS_INSTALL_PF_FILES.md) - Test results
- [test_install_pf_files.sh](test_install_pf_files.sh) - Automated test script

## Questions?

If you have questions about creating these issues:
1. Check the individual issue markdown files for details
2. Review the test results in TEST_RESULTS_INSTALL_PF_FILES.md
3. Run the test script: `./test_install_pf_files.sh`
4. Refer to the main documentation: TESTING_INSTALL_PF_FILES.md

---

**Note:** The issue markdown files contain all the information needed. You're simply copying them into GitHub's issue system.
