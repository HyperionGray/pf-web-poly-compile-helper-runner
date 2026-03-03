# Quick Reference: Testing .pf Installation Files

## Test Execution

```bash
# Run all tests
./test_install_pf_files.sh

# Expected output: All 30 tests pass ✅
```

## The 5 Issues

| # | Title | Priority | Files | Tasks | Status |
|---|-------|----------|-------|-------|--------|
| 1 | Test Core Installation .pf Files | 🔴 High | 2 | 5 | Ready to create |
| 2 | Test Always-On Installation .pf Files | 🔴 High | 1 | 1 | Ready to create |
| 3 | Test Tool Installation .pf Files | 🟡 Medium | 4 | 19 | Ready to create |
| 4 | Test Package Manager and Container Files | 🟡 Medium | 3 | 7 | Ready to create |
| 5 | Test Security and TUI Files | 🟡 Medium | 5 | 6 | Ready to create |

**Total:** 15 files, 38 tasks matching `task.*install`, 350 total tasks

## Quick Create with gh CLI

```bash
gh issue create --title "Test Core Installation .pf Files" \
  --body-file ISSUE_1_CORE_INSTALL_FILES.md --label "testing,high-priority"

gh issue create --title "Test Always-On Installation .pf Files" \
  --body-file ISSUE_2_ALWAYS_ON_INSTALL_FILES.md --label "testing,high-priority"

gh issue create --title "Test Tool Installation .pf Files" \
  --body-file ISSUE_3_TOOL_INSTALL_FILES.md --label "testing,medium-priority"

gh issue create --title "Test Package Manager and Container Installation .pf Files" \
  --body-file ISSUE_4_PACKAGE_CONTAINER_FILES.md --label "testing,medium-priority"

gh issue create --title "Test Security and TUI Installation .pf Files" \
  --body-file ISSUE_5_SECURITY_TUI_FILES.md --label "testing,medium-priority"
```

## Files Overview

### Documentation
- `TESTING_INSTALL_PF_FILES.md` - Master testing documentation
- `TEST_RESULTS_INSTALL_PF_FILES.md` - Detailed test results
- `CREATING_GITHUB_ISSUES.md` - Guide for creating issues
- `QUICK_REFERENCE_TESTING.md` - This file

### Test Infrastructure
- `test_install_pf_files.sh` - Automated test script (executable)

### Issue Documents
- `ISSUE_1_CORE_INSTALL_FILES.md` - Issue #1 content
- `ISSUE_2_ALWAYS_ON_INSTALL_FILES.md` - Issue #2 content
- `ISSUE_3_TOOL_INSTALL_FILES.md` - Issue #3 content
- `ISSUE_4_PACKAGE_CONTAINER_FILES.md` - Issue #4 content
- `ISSUE_5_SECURITY_TUI_FILES.md` - Issue #5 content

## Test Results Summary

✅ **100% Success Rate**
- 30/30 tests passed
- 0 failures
- 0 skipped
- All syntax valid
- All tasks discoverable

## Key Statistics

| Category | Value |
|----------|-------|
| .pf Files Tested | 15 |
| Total Tasks | 350 |
| Install Tasks | 38 |
| Test Groups | 5 |
| Tests Run | 30 |
| Success Rate | 100% |

## Issue Categories

### Group 1: Core Installation (High Priority 🔴)
Files: `pf-files/always-available/Pfyfile.always-available.pf`, `pf-files/Pfyfile.pf`
- Main install task
- Help and full install flow
- Smoke test after install

### Group 2: Always-On Tasks (High Priority 🔴)
Files: `pf-files/always-available/Pfyfile.always-on.pf` (1 file)
- Service status/orchestration
- Unit installation (`always-on-install-all`)

### Group 3: Tool Installation (Medium Priority 🟡)
Files: `pf-files/debugging/Pfyfile.debug-tools.pf`, `pf-files/exploit-writing/Pfyfile.exploit.pf`, etc.
- Radare2, Ghidra, Snowman
- pwntools, ROPgadget, checksec
- AFL++, libfuzzer, sanitizers

### Group 4: Package/Container (Medium Priority 🟡)
Files: `pf-files/distro-switching/Pfyfile.package-manager.pf`, `pf-files/containers/Pfyfile.containers.pf`, etc.
- Package format conversion
- Container image builds
- Multi-distro management

### Group 5: Security/TUI (Medium Priority 🟡)
Files: `pf-files/vuln-hunting/Pfyfile.security.pf`, `pf-files/always-available/Pfyfile.tui.pf`, etc.
- Security scanning
- TUI interface
- Git cleanup
- Binary lifting/injection

## Next Actions

1. ✅ Test script created and validated
2. ✅ All documentation written
3. ✅ Issue documents prepared
4. ⏳ Create 5 GitHub issues (use CREATING_GITHUB_ISSUES.md)
5. ⏳ Assign team members
6. ⏳ Link issues to PR
7. ⏳ Add to project board (optional)

## Commands Reference

```bash
# View test results
cat TEST_RESULTS_INSTALL_PF_FILES.md

# View specific issue
cat ISSUE_1_CORE_INSTALL_FILES.md

# View detailed testing docs
cat TESTING_INSTALL_PF_FILES.md

# Create issues guide
cat CREATING_GITHUB_ISSUES.md

# Run tests again
./test_install_pf_files.sh

# Check syntax of specific file
grep -c "^task " pf-files/always-available/Pfyfile.always-available.pf
grep -c "^end" pf-files/always-available/Pfyfile.always-available.pf

# Count all install tasks
grep -r "^task.*install" --include="*.pf" | wc -l
```

## Success Criteria

- [x] Test script created
- [x] All tests pass
- [x] Documentation complete
- [x] 5 issue documents ready
- [ ] Issues created on GitHub
- [ ] Labels applied
- [ ] Team assigned
- [ ] Linked to PR

## Related Links

- Main Repo: https://github.com/HyperionGray/pf-web-poly-compile-helper-runner
- Issues: https://github.com/HyperionGray/pf-web-poly-compile-helper-runner/issues
- This PR: (link will be added when created)

---

**Quick Start:** Run `./test_install_pf_files.sh` to validate all .pf files ✅
