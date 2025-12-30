# Issue #1: Test Core Installation .pf Files

## Summary
Test and validate core installation .pf files to ensure all install tasks work correctly.

## Description
This issue tracks testing of the primary .pf files that contain core installation functionality:

### Files to Test
1. **Pfyfile.always-available.pf** - Main installation tasks file with general OS tasks
2. **Pfyfile.pf** - Root configuration file that includes all other modules

### Tasks to Validate
- [ ] `install` - Main installation task
- [ ] `install-base` - Base installation
- [ ] `install-web` - Web development tools installation
- [ ] `install-container` - Container mode installation
- [ ] `install-full` - Full system setup
- [ ] `install-native` - Native mode installation
- [ ] `install-system` - System-wide installation

### Testing Requirements
1. **Syntax Validation**
   - [ ] Parse Pfyfile.always-available.pf without errors
   - [ ] Parse Pfyfile.pf without errors
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
pf --file Pfyfile.always-available.pf list
pf --file Pfyfile.pf list

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
- `Pfyfile.always-available.pf`
- `Pfyfile.pf`
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
