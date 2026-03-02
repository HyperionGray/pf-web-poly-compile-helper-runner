# Testing .pf Files Involved in Installation

This document outlines the comprehensive testing strategy for all .pf files that contain installation tasks.

## Overview

The pf-runner system uses multiple .pf files to organize installation tasks for different tools and components. This testing initiative ensures that:

1. All .pf files parse correctly without syntax errors
2. All installation tasks are discoverable and documented
3. Task descriptions are accurate and helpful
4. Installation workflows are properly tested
5. Dependencies are correctly specified

## Test Infrastructure

### Automated Test Script

Run the comprehensive test suite:
```bash
./test_install_pf_files.sh
```

This script:
- Tests syntax of all .pf files with install tasks
- Validates task discovery and listing
- Checks for proper descriptions
- Verifies task structure
- Reports results with pass/fail status

### Test Results

The test script provides:
- ✓ Passed tests (green)
- ✗ Failed tests (red)
- ⚠ Skipped tests (yellow)
- Summary with total counts

## Test Issues

We have created 5 GitHub issues to systematically test all installation-related .pf files:

### Issue #1: Core Installation Files
**Files:** `pf-files/always-available/Pfyfile.always-available.pf`, `pf-files/Pfyfile.pf`

Tests the primary installation tasks that users run first:
- Main `install` task
- `install-help` - Usage and guidance
- `install-all` - Run the full install flow
- `install-smoke-test` - Quick validation after installation

**Priority:** 🔴 High - Critical for all users

**Details:** See [ISSUE_1_CORE_INSTALL_FILES.md](ISSUE_1_CORE_INSTALL_FILES.md)

### Issue #2: Always-On Installation Files
**Files:** `pf-files/always-available/Pfyfile.always-on.pf`

Tests always-on tasks available from any directory:
- Service status and orchestration
- Unit installation (`always-on-install-all`)
- Individual service start/stop tasks

**Priority:** 🔴 High - Key feature for user convenience

**Details:** See [ISSUE_2_ALWAYS_ON_INSTALL_FILES.md](ISSUE_2_ALWAYS_ON_INSTALL_FILES.md)

### Issue #3: Tool Installation Files
**Files:** `pf-files/debugging/Pfyfile.debug-tools.pf`, `pf-files/exploit-writing/Pfyfile.exploit.pf`, `pf-files/vuln-hunting/Pfyfile.fuzzing.pf`, etc.

Tests specialized tool installations:
- Debugging and reverse engineering tools (Radare2, Ghidra, Snowman)
- Exploit development tools (pwntools, ROPgadget, checksec)
- Fuzzing tools (AFL++, libfuzzer, sanitizers)
- Binary analysis tools

**Priority:** 🟡 Medium - Important for advanced users

**Details:** See [ISSUE_3_TOOL_INSTALL_FILES.md](ISSUE_3_TOOL_INSTALL_FILES.md)

### Issue #4: Package Manager and Container Files
**Files:** `pf-files/distro-switching/Pfyfile.package-manager.pf`, `pf-files/containers/Pfyfile.containers.pf`, `pf-files/distro-switching/Pfyfile.distro-switch.pf`

Tests package and container management:
- Package format conversion (deb, rpm, flatpak, snap, pacman)
- Container image building
- Multi-distro package installation
- OS-specific containers

**Priority:** 🟡 Medium - Important for multi-platform support

**Details:** See [ISSUE_4_PACKAGE_CONTAINER_FILES.md](ISSUE_4_PACKAGE_CONTAINER_FILES.md)

### Issue #5: Security and TUI Files
**Files:** `pf-files/vuln-hunting/Pfyfile.security.pf`, `pf-files/always-available/Pfyfile.tui.pf`, `pf-files/gitops/Pfyfile.git-cleanup.pf`, etc.

Tests security and additional tools:
- Web security scanning
- TUI dependencies and interface
- Git cleanup tools
- Binary lifting (RetDec, McSema)
- Binary injection tools

**Priority:** 🟡 Medium - Important for security and usability

**Details:** See [ISSUE_5_SECURITY_TUI_FILES.md](ISSUE_5_SECURITY_TUI_FILES.md)

## Complete File List

### Core Installation Files
- `pf-files/always-available/Pfyfile.always-available.pf` - Main installation tasks
- `pf-files/Pfyfile.pf` - Root configuration with includes

### Always-On Files
- `pf-files/always-available/Pfyfile.always-on.pf` - Always-on service management and unit installation

### Specialized Tool Files
- `pf-files/debugging/Pfyfile.debug-tools.pf` - Debugging tools (oryx, binsider, radare2, ghidra)
- `pf-files/exploit-writing/Pfyfile.exploit.pf` - Exploitation tools (pwntools, ROPgadget)
- `pf-files/vuln-hunting/Pfyfile.fuzzing.pf` - Fuzzing and sanitizers
- `pf-files/debugging/Pfyfile.debugging.pf` - GDB/LLDB/pwndbg
- `pf-files/vuln-hunting/Pfyfile.sanitizers.pf` - Memory sanitizers

### Package and Container Files
- `pf-files/distro-switching/Pfyfile.package-manager.pf` - Package conversion
- `pf-files/containers/Pfyfile.containers.pf` - Container builds
- `pf-files/distro-switching/Pfyfile.distro-switch.pf` - Multi-distro management
- `pf-files/distro-switching/Pfyfile.os-containers.pf` - OS containers
- `pf-files/mult-exec/Pfyfile.pe-containers.pf` - PE/Windows containers

### Security and Additional Files
- `pf-files/vuln-hunting/Pfyfile.security.pf` - Security scanning
- `pf-files/always-available/Pfyfile.tui.pf` - Terminal UI
- `pf-files/gitops/Pfyfile.git-cleanup.pf` - Git cleanup
- `pf-files/llvm-lifting/Pfyfile.lifting.pf` - Binary lifting
- `pf-files/vuln-hunting/Pfyfile.injection.pf` - Binary injection
- `pf-files/gitops/Pfyfile.pr-management.pf` - PR management

## Testing Methodology

### 1. Syntax Validation
```bash
# Test individual file
pf --file <file.pf> list

# Should exit with code 0 and list tasks
```

### 2. Task Discovery
```bash
# List all tasks
pf list

# Search for install tasks
pf list | grep install
```

### 3. Task Documentation
```bash
# Check descriptions
grep -A 1 "^task install" <file.pf> | grep describe
```

### 4. Help Commands
```bash
# Test category help
pf category-installation-help
pf debug-tools-help
pf security-help
# etc.
```

### 5. Non-Invasive Execution
```bash
# Check status without installing
pf check-debug-tools
pf distro-status
pf pkg-formats
```

## Expected Test Results

### All Tests Should Pass
- ✓ Syntax validation for all .pf files
- ✓ All install tasks are discoverable
- ✓ Tasks have descriptions
- ✓ Help commands work
- ✓ Task structure is consistent

### Common Issues to Watch For
- ❌ Syntax errors (missing `end`, bad shell commands)
- ❌ Missing descriptions
- ❌ Hardcoded paths
- ❌ Undefined variables
- ❌ Broken includes

## Running Tests

### Quick Test
```bash
# Run automated test suite
./test_install_pf_files.sh
```

### Manual Testing
```bash
# Test specific file
pf --file pf-files/always-available/Pfyfile.always-available.pf list

# Test specific task
pf install --help

# Check all install tasks
pf list | grep install | wc -l
```

### Comprehensive Testing
```bash
# Run all issue tests
for i in {1..5}; do
  echo "Testing Issue $i..."
  # Follow steps in ISSUE_${i}_*.md
done
```

## Success Criteria

All 5 issues should be resolved with:
- [x] All .pf files parse without errors
- [x] All install tasks are listed correctly
- [x] Task descriptions are present and accurate
- [x] Help commands work as expected
- [x] No broken includes or dependencies
- [x] Documentation matches implementation

## Related Documentation

- [INSTALLER_GUIDE.md](INSTALLER_GUIDE.md) - Installation guide
- [README.md](README.md) - Main documentation
- [pf-runner/README.md](pf-runner/README.md) - pf-runner documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide

## Contributing

When adding new installation tasks:
1. Add `describe` statement for documentation
2. Check prerequisites before installation
3. Provide clear error messages
4. Test syntax with `pf --file <file.pf> list`
5. Update relevant issue documentation
6. Run test suite to verify

## Maintenance

This testing infrastructure should be run:
- Before major releases
- After adding new .pf files
- When modifying installation tasks
- As part of CI/CD pipeline

---

**Last Updated:** 2025-12-29  
**Test Script:** `test_install_pf_files.sh`  
**Issues:** 5 comprehensive test issues created
