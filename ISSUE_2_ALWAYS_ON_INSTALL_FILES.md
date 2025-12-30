# Issue #2: Test Always-On Installation .pf Files

## Summary
Test and validate always-on .pf files that provide system-wide installation tasks available from any directory.

## Description
This issue tracks testing of the always-on .pf files in the pf-runner directory that contain installation functionality:

### Files to Test
1. **pf-runner/Pfyfile.always-on-packages.pf** - Package management installation
2. **pf-runner/Pfyfile.always-on-debug.pf** - Debugging tools installation
3. **pf-runner/Pfyfile.always-on-exploit.pf** - Exploit development tools installation
4. **pf-runner/Pfyfile.always-on-tui.pf** - TUI dependencies installation
5. **pf-runner/Pfyfile.always-on-git.pf** - Git-related tool installation
6. **pf-runner/Pfyfile.always-on-os.pf** - OS-level tool installation
7. **pf-runner/Pfyfile.pf** - Main pf-runner configuration

### Tasks to Validate

#### Package Management
- [ ] `install-pkg-tools` - Install package conversion tools
- [ ] `install-flatpak` - Install Flatpak package manager
- [ ] `install-snap` - Install Snapd

#### Debugging Tools
- [ ] `install-all-debug-tools` - Install all debugging tools
- [ ] `install-oryx` - Install oryx binary explorer
- [ ] `install-binsider` - Install binsider binary analyzer
- [ ] `install-radare2` - Install Radare2
- [ ] `install-ghidra` - Install Ghidra
- [ ] `install-snowman` - Install Snowman decompiler
- [ ] `install-debuggers` - Install GDB, LLDB, pwndbg

#### Exploit Development
- [ ] `install-exploit-tools` - Install all exploit tools
- [ ] `install-checksec` - Install checksec
- [ ] `install-pwntools` - Install pwntools
- [ ] `install-ropgadget` - Install ROPgadget
- [ ] `install-ropper` - Install ropper

#### TUI and Interface
- [ ] `install-tui-deps` - Install TUI dependencies (rich library)

#### Git and Version Control
- [ ] `install-git-filter-repo` - Install git-filter-repo

### Testing Requirements
1. **Syntax Validation**
   - [ ] All always-on .pf files parse without errors
   - [ ] Tasks are properly formatted
   - [ ] No syntax issues with shell commands

2. **Task Availability**
   - [ ] Tasks are available from any directory (always-on behavior)
   - [ ] Tasks appear in `pf list` output
   - [ ] Subcommands are properly organized

3. **Execution Testing**
   - [ ] Each install task can be invoked
   - [ ] Proper error messages for missing prerequisites
   - [ ] Installation paths are correct

4. **Documentation**
   - [ ] All tasks have descriptions
   - [ ] Help commands work properly
   - [ ] Category help is available

### Test Commands
```bash
# Test always-on files syntax
pf --file pf-runner/Pfyfile.always-on-packages.pf list
pf --file pf-runner/Pfyfile.always-on-debug.pf list
pf --file pf-runner/Pfyfile.always-on-exploit.pf list
pf --file pf-runner/Pfyfile.always-on-tui.pf list

# Test task discovery
pf list | grep install

# Test category help
pf category-installation-help
```

### Expected Results
- All always-on .pf files parse successfully
- All install tasks are discoverable from any directory
- Task descriptions are clear
- Subcommands are properly organized
- No syntax or parsing errors

### Priority
🔴 **High** - Always-on tasks are a key feature for user convenience

### Related Files
- `pf-runner/Pfyfile.always-on-packages.pf`
- `pf-runner/Pfyfile.always-on-debug.pf`
- `pf-runner/Pfyfile.always-on-exploit.pf`
- `pf-runner/Pfyfile.always-on-tui.pf`
- `pf-runner/Pfyfile.always-on-git.pf`
- `pf-runner/Pfyfile.always-on-os.pf`
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
