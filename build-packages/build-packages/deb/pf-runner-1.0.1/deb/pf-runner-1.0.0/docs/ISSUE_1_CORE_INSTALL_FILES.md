# Issue #1: Test Core Installation .pf Files

## Summary
Test and validate core installation .pf files to ensure all install tasks work correctly.

## Description
This issue tracks testing of the primary .pf files that contain core installation functionality:

### Files to Test
1. **pf-files/always-available/Pfyfile.always-available.pf** - Always-available help and utility tasks (loaded automatically)
2. **pf-files/Pfyfile.pf** - Root configuration file that includes all other modules

### Tasks to Validate
- [ ] `install` - Main installation task
- [ ] `install-help` - Installation help and guidance
- [ ] `install-all` - Run the full install flow
- [ ] `install-smoke-test` - Quick validation after install
- [ ] `category-installation-help` - Always-available installation category help

### Testing Requirements
1. **Syntax Validation**
   - [ ] Parse pf-files/always-available/Pfyfile.always-available.pf without errors
   - [ ] Parse pf-files/Pfyfile.pf without errors
   - [ ] All tasks have proper syntax

2. **Task Discovery**
   - [ ] All install tasks are listed via `pf list`
   - [ ] Task descriptions are present and meaningful
   - [ ] Task dependencies are properly declared

3. **Execution Testing**
   - [ ] `pf install --help` shows usage information
   - [ ] Tasks can execute in dry-run mode (if supported)
   - [ ] Error handling is present for missing dependencies

4. **Documentation**
   - [ ] Each install task has a `describe` statement
   - [ ] Documentation matches actual behavior
   - [ ] Usage examples are accurate

### Test Commands
```bash
# Test syntax
pf --file pf-files/always-available/Pfyfile.always-available.pf list
pf --file pf-files/Pfyfile.pf list

# Test task discovery
pf list | grep install

# Test specific tasks (read-only checks)
pf install --help 2>/dev/null || echo "No help available"
```

### Expected Results
- All .pf files parse successfully
- All install tasks are discoverable
- Task descriptions are clear and accurate
- No syntax errors or parsing failures

### Priority
🔴 **High** - Core installation functionality is critical for all users

### Related Files
- `pf-files/always-available/Pfyfile.always-available.pf`
- `pf-files/Pfyfile.pf`
- `install.sh`
- `INSTALLER_GUIDE.md`

### Test Script
Run the automated test:
```bash
./test_install_pf_files.sh
```

### Acceptance Criteria
- [ ] All syntax tests pass
- [ ] All install tasks are properly defined
- [ ] Task descriptions are present
- [ ] No parsing errors occur
- [ ] Documentation is accurate
