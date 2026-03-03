# Issue #2: Test Always-On .pf File

## Summary
Test and validate the always-on .pf file that manages background services and always-on workflows.

## Description
This issue tracks testing of the always-on service management tasks.

### Files to Test
1. **pf-files/always-available/Pfyfile.always-on.pf** - Always-on service management and unit installation

### Tasks to Validate
#### Always-On Orchestration
- [ ] `always-on-status` - Show status of all always-on services
- [ ] `always-on-start-all` - Start all always-on services
- [ ] `always-on-stop-all` - Stop all always-on services
- [ ] `always-on-restart-all` - Restart all always-on services

#### Unit Installation
- [ ] `always-on-install-all` - Install all always-on service units

#### Individual Services
- [ ] `security-monitor-on/off/dev` - Security monitor controls
- [ ] `build-watch-on/off/dev` - Build watcher controls
- [ ] `container-health-on/off` - Container health monitor controls
- [ ] `dev-proxy-on/off` - Development proxy controls
- [ ] `log-aggregator-on/off` - Log aggregation controls
- [ ] `file-watch-on/off` - File watch controls

### Testing Requirements
1. **Syntax Validation**
   - [ ] Always-on .pf file parses without errors
   - [ ] Tasks are properly formatted
   - [ ] No syntax issues with shell commands

2. **Task Availability**
   - [ ] Tasks are available from any directory (always-on behavior)
   - [ ] Tasks appear in `pf list` output
   - [ ] Aliases work (where defined)

3. **Execution Testing**
   - [ ] Service start/stop tasks can be invoked safely
   - [ ] Proper error messages for missing prerequisites
   - [ ] `always-on-install-all` points at the correct service unit locations

4. **Documentation**
   - [ ] All tasks have descriptions
   - [ ] Help commands work properly
   - [ ] Usage examples are accurate

### Test Commands
```bash
# Test always-on file syntax
pf --file pf-files/always-available/Pfyfile.always-on.pf list

# Test orchestration (non-invasive)
pf always-on-status

# (Optional) show help (if implemented)
pf always-on-install-all --help 2>/dev/null || true
```

### Expected Results
- Always-on .pf file parses successfully
- Always-on tasks are discoverable from any directory
- Task descriptions are clear
- No syntax or parsing errors

### Priority
🔴 **High** - Always-on tasks are a key feature for user convenience

### Related Files
- `pf-files/always-available/Pfyfile.always-on.pf`
- `docs/ALWAYS-ON-TASKS.md`

### Test Script
Run the automated test:
```bash
./test_install_pf_files.sh
```

### Acceptance Criteria
- [ ] All always-on .pf files pass syntax validation
- [ ] All install tasks are accessible
- [ ] Task descriptions are accurate
- [ ] Category help works correctly
- [ ] No parsing or execution errors
