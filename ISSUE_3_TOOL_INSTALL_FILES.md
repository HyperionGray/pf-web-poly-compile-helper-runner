# Issue #3: Test Tool Installation .pf Files

## Summary
Test and validate tool-specific installation .pf files for debugging, exploitation, and fuzzing tools.

## Description
This issue tracks testing of .pf files that provide installation functionality for specialized tools:

### Files to Test
1. **Pfyfile.debug-tools.pf** - Debugging and reverse engineering tools
2. **Pfyfile.exploit.pf** - Exploitation and binary analysis tools
3. **Pfyfile.fuzzing.pf** - Fuzzing and sanitizer tools
4. **Pfyfile.debugging.pf** - GDB, LLDB, and debugging workflow tools
5. **Pfyfile.sanitizers.pf** - Memory and behavior sanitizers

### Tasks to Validate

#### Debug Tools (Pfyfile.debug-tools.pf)
- [ ] `install-oryx` - Install oryx binary explorer
- [ ] `install-binsider` - Install binsider binary analyzer
- [ ] `install-rustnet` - Install rustnet network monitor
- [ ] `install-sysz` - Install sysz systemd viewer
- [ ] `install-radare2` - Install Radare2 RE framework
- [ ] `install-ghidra` - Install Ghidra decompiler
- [ ] `install-snowman` - Install Snowman decompiler
- [ ] `install-all-debug-tools` - Install all debugging tools
- [ ] `check-debug-tools` - Check tool installation status

#### Exploit Tools (Pfyfile.exploit.pf)
- [ ] `install-checksec` - Install checksec binary checker
- [ ] `install-pwntools` - Install pwntools framework
- [ ] `install-ropgadget` - Install ROPgadget tool
- [ ] `install-ropper` - Install ropper ROP tool
- [ ] `install-exploit-tools` - Install all exploit tools

#### Fuzzing Tools (Pfyfile.fuzzing.pf)
- [ ] `install-fuzzing-tools` - Install all fuzzing tools
- [ ] `install-sanitizers` - Install LLVM sanitizers
- [ ] `install-libfuzzer` - Install libfuzzer
- [ ] `install-aflplusplus` - Install AFL++
- [ ] `install-retdec` - Install RetDec binary lifter

#### Debugging (Pfyfile.debugging.pf)
- [ ] `install-debuggers` - Install GDB, LLDB, pwndbg

### Testing Requirements

1. **Syntax Validation**
   - [ ] All tool installation .pf files parse correctly
   - [ ] Shell commands have proper syntax
   - [ ] No undefined variables or commands

2. **Task Structure**
   - [ ] All install tasks follow naming convention
   - [ ] Tasks have proper descriptions
   - [ ] Dependencies are clearly specified

3. **Execution Testing**
   - [ ] Tasks check for existing installations
   - [ ] Proper error handling for failures
   - [ ] Success messages are displayed
   - [ ] Installation verification works

4. **Tool Integration**
   - [ ] Installed tools are accessible in PATH
   - [ ] Tools can be executed after installation
   - [ ] Version checks work when available

5. **Documentation**
   - [ ] Each tool has usage instructions
   - [ ] Help commands provide useful information
   - [ ] Installation prerequisites are documented

### Test Commands
```bash
# Test syntax
pf --file Pfyfile.debug-tools.pf list
pf --file Pfyfile.exploit.pf list
pf --file Pfyfile.fuzzing.pf list
pf --file Pfyfile.debugging.pf list

# Test task discovery
pf list | grep -E "install-(debug|exploit|fuzz|sanitizer)"

# Test help commands
pf debug-tools-help
pf fuzzing-help
pf injection-help

# Check tool status (non-invasive)
pf check-debug-tools
```

### Expected Results
- All tool installation .pf files parse successfully
- All install tasks are discoverable
- Task descriptions clearly explain what will be installed
- Error handling is appropriate
- Help commands work correctly

### Priority
🟡 **Medium** - Tool installation is important but not critical for basic functionality

### Related Files
- `Pfyfile.debug-tools.pf`
- `Pfyfile.exploit.pf`
- `Pfyfile.fuzzing.pf`
- `Pfyfile.debugging.pf`
- `Pfyfile.sanitizers.pf`
- `docs/FUZZING.md`
- `docs/KERNEL-DEBUGGING.md`
- `demos/debugging/README.md`
- `demos/rop-exploit/README.md`

### Test Script
Run the automated test:
```bash
./test_install_pf_files.sh
```

### Acceptance Criteria
- [ ] All tool installation .pf files pass syntax validation
- [ ] All install tasks are properly defined
- [ ] Task descriptions are accurate and helpful
- [ ] Help commands work correctly
- [ ] No parsing or syntax errors
- [ ] Tool verification commands work
