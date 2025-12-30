# Issue #5: Test Security and TUI Installation .pf Files

## Summary
Test and validate security testing, TUI, and additional tool installation .pf files.

## Description
This issue tracks testing of .pf files that provide security testing tools, TUI functionality, and additional specialized installations:

### Files to Test
1. **Pfyfile.security.pf** - Web security scanning tools
2. **Pfyfile.tui.pf** - Terminal UI dependencies and tools
3. **Pfyfile.git-cleanup.pf** - Git repository cleanup tools
4. **Pfyfile.lifting.pf** - Binary lifting (RetDec, McSema)
5. **Pfyfile.injection.pf** - Binary injection tools
6. **Pfyfile.pr-management.pf** - PR and issue management tools

### Tasks to Validate

#### Security Tools (Pfyfile.security.pf)
- [ ] `install-security-tools` - Install web security scanners
- [ ] `install-zap` - Install OWASP ZAP (if available)
- [ ] `install-nikto` - Install Nikto web scanner
- [ ] `install-sqlmap` - Install sqlmap
- [ ] `security-scan` - Web vulnerability scanning
- [ ] `security-fuzz` - Web application fuzzing

#### TUI (Pfyfile.tui.pf)
- [ ] `install-tui-deps` - Install rich library
- [ ] `tui` - Launch interactive TUI
- [ ] `tui-help` - Show TUI usage

#### Git Cleanup (Pfyfile.git-cleanup.pf)
- [ ] `install-git-filter-repo` - Install git-filter-repo
- [ ] `git-cleanup` - Interactive cleanup tool
- [ ] `git-analyze-large-files` - Analyze repository

#### Binary Lifting (Pfyfile.lifting.pf)
- [ ] `install-retdec` - Install RetDec binary lifter
- [ ] `install-mcsema` - Install McSema (if available)
- [ ] `lift-binary-retdec` - Lift binary to LLVM IR

#### Binary Injection (Pfyfile.injection.pf)
- [ ] `install-injection-tools` - Install patchelf, nasm, binaryen
- [ ] `create-injection-payload-rust` - Create Rust injection library
- [ ] `create-injection-payload-c` - Create C injection library

### Testing Requirements

1. **Syntax Validation**
   - [ ] All security/TUI .pf files parse correctly
   - [ ] Python script invocations are valid
   - [ ] Shell commands have proper syntax

2. **Tool Installation**
   - [ ] Installation tasks check prerequisites
   - [ ] Tools are installed to appropriate locations
   - [ ] Version verification works

3. **Security Scanning**
   - [ ] Security tasks handle URLs correctly
   - [ ] Output formats are properly handled
   - [ ] Error messages are informative

4. **TUI Functionality**
   - [ ] TUI launches without errors
   - [ ] Dependencies are properly checked
   - [ ] Interface is usable

5. **Binary Tools**
   - [ ] Binary lifting tasks handle paths correctly
   - [ ] Injection tasks create proper payloads
   - [ ] Tool chains work together

### Test Commands
```bash
# Test syntax
pf --file Pfyfile.security.pf list
pf --file Pfyfile.tui.pf list
pf --file Pfyfile.git-cleanup.pf list
pf --file Pfyfile.lifting.pf list
pf --file Pfyfile.injection.pf list

# Test task discovery
pf list | grep -E "(security|tui|git-cleanup|lift|inject)"

# Test help commands
pf security-help
pf tui-help
pf git-cleanup-help
pf lifting-help
pf injection-help

# Non-invasive checks
pf check-debug-tools 2>/dev/null || echo "Check skipped"
```

### Expected Results
- All security/TUI .pf files parse successfully
- All install tasks are discoverable
- Security scanning tasks are properly structured
- TUI dependencies are correctly specified
- Binary tool chains are complete

### Priority
🟡 **Medium** - Important for security and usability but not core functionality

### Related Files
- `Pfyfile.security.pf`
- `Pfyfile.tui.pf`
- `Pfyfile.git-cleanup.pf`
- `Pfyfile.lifting.pf`
- `Pfyfile.injection.pf`
- `Pfyfile.pr-management.pf`
- `tools/security/security_scanner.py`
- `tools/tui/tui.py`
- `tools/git/git_cleanup_tui.py`
- `docs/SECURITY-TESTING.md`
- `docs/TUI.md`
- `docs/GIT-CLEANUP.md`
- `docs/LLVM-LIFTING.md`
- `docs/BINARY-INJECTION.md`

### Test Script
Run the automated test:
```bash
./test_install_pf_files.sh
```

### Acceptance Criteria
- [ ] All security/TUI .pf files pass syntax validation
- [ ] All install tasks are properly defined
- [ ] Security scanning tasks have proper error handling
- [ ] TUI launches without errors
- [ ] Binary tool tasks are functional
- [ ] Help commands work correctly
- [ ] No parsing or syntax errors
- [ ] Python tool wrappers are accessible

### Additional Testing Notes

#### Security Testing Considerations
- Security tasks should not actually scan external targets in tests
- Dry-run or local testing mode should be available
- Output should be structured and parseable

#### TUI Testing Considerations
- TUI should gracefully handle missing dependencies
- Keyboard navigation should be documented
- Terminal compatibility should be checked

#### Binary Tool Testing Considerations
- Binary lifting should handle multiple architectures
- Injection payloads should be validated
- Tool chains should be properly integrated
