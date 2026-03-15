# Installer Testing Suite - Test Coverage and Findings

## Overview

This document describes the comprehensive installer testing suite created to verify that pf-runner installers work correctly and that the installed software functions as expected.

## Test Suite Location

The main test suite is located at:
```
tests/installation/test_installer_comprehensive.py
```

## Running the Tests

### Prerequisites

Install required Python packages:
```bash
pip install pytest lark fabric typer json5
```

### Run All Installer Tests

```bash
# Run all installer tests
pytest tests/installation/test_installer_comprehensive.py -v

# Run specific test classes
pytest tests/installation/test_installer_comprehensive.py::TestDirectExecution -v
pytest tests/installation/test_installer_comprehensive.py::TestStaticInstall -v
pytest tests/installation/test_installer_comprehensive.py::TestNativeInstall -v
```

### Run with Integration Marker

```bash
pytest -m integration tests/installation/ -v
```

## Test Coverage

### 1. Direct Execution Tests (TestDirectExecution)
**Status**: ✅ All Passing

Tests direct execution of `pf_main.py` without installation:
- ✅ `test_direct_version` - Verifies `pf_main.py -V` works
- ✅ `test_direct_list` - Verifies task listing works
- ✅ `test_direct_run_task` - Verifies task execution works
- ✅ `test_direct_parameter_passing` - Verifies parameter passing works

**Example Run:**
```bash
$ pytest tests/installation/test_installer_comprehensive.py::TestDirectExecution -v
================================================= test session starts ==================================================
tests/installation/test_installer_comprehensive.py::TestDirectExecution::test_direct_version PASSED              [ 25%]
tests/installation/test_installer_comprehensive.py::TestDirectExecution::test_direct_list PASSED                 [ 50%]
tests/installation/test_installer_comprehensive.py::TestDirectExecution::test_direct_run_task PASSED             [ 75%]
tests/installation/test_installer_comprehensive.py::TestDirectExecution::test_direct_parameter_passing PASSED    [100%]
============================================ 4 passed in 1.16s =============================================
```

### 2. Static Executable Tests (TestStaticExecutable)
**Status**: ⏭️ Skipped (Static executable not built)

Tests the pre-built static executable `pf-runner-full/pf-static` (or legacy fallback `pf-runner/pf-static`):
- `test_static_exe_version` - Verifies version command
- `test_static_exe_list` - Verifies task listing
- `test_static_exe_run_task` - Verifies task execution

**Note**: Tests are automatically skipped if no `pf-static` binary is present. Build it first with:
```bash
cd pf-runner-full && make build-static
```

### 3. Static Installation Tests (TestStaticInstall)
**Status**: ⏭️ Skipped (Static executable not built)

Tests the `install-static.sh` installer:
- `test_install_static` - Verifies installation succeeds
- `test_static_version` - Tests installed executable version
- `test_static_list` - Tests task listing
- `test_static_run_task` - Tests task execution

**Functionality Tested:**
- Installation to custom prefix
- Executable permissions
- Binary functionality
- Task execution

### 4. Native Installation Tests (TestNativeInstall)
**Status**: ❌ Expected Failure (install.sh has known bugs)

Tests the `install.sh` native installer:
- `test_install_native` - Verifies installation succeeds

**Known Issues** (Marked as `xfail`):
The native installer `install.sh` currently has several critical bugs:

1. **Syntax Error at Line 284**: Unclosed heredoc
   ```bash
   write_wrapper() {
     local pf_files="${PF_FILES_DIR:-${PREFIX}/lib/pf-files}"
     log "Installing wrapper to ${PREFIX}/bin/pf"
     cat > "${PREFIX}/bin/pf" <<EOF
   # EOF is never provided, rest of file is inside heredoc
   ```

2. **Missing Functions**: The following functions are called but not defined:
   - `check_prerequisites`
   - `install_pf_runner`
   - `validate_installation`

3. **Uninitialized Variable**: `PREFIX_SET` variable is used but never initialized

**Verification**:
```bash
$ bash -n install.sh
install.sh: line 427: warning: here-document at line 284 delimited by end-of-file (wanted `EOF')
install.sh: line 428: syntax error: unexpected end of file
```

**When Fixed**: Remove the `@pytest.mark.xfail` decorator from the test class to enable these tests.

## Test Architecture

### Base Test Class: `InstallerTest`

Provides common functionality testing methods:
- `test_version()` - Verifies pf --version works
- `test_list_tasks()` - Verifies pf can list tasks
- `test_run_simple_task()` - Verifies pf can execute tasks
- `test_parameter_passing()` - Verifies parameter passing works
- `test_help_output()` - Verifies help system works

### Test Structure

Each installer test class follows this pattern:
1. **Setup**: Create temporary test directory
2. **Install**: Run the installer to the test directory
3. **Verify Installation**: Check files were created correctly
4. **Test Functionality**: Run the base test methods
5. **Cleanup**: Remove test directory

## What These Tests Validate

### Installation Validation
- ✅ Installer completes without errors
- ✅ Files are placed in correct locations
- ✅ Executables have proper permissions
- ✅ Virtual environments created (where applicable)
- ✅ Dependencies installed (where applicable)

### Functionality Validation
- ✅ `pf -V` returns version information
- ✅ `pf list` shows available tasks
- ✅ `pf <task>` executes tasks successfully
- ✅ `pf <task> param=value` passes parameters correctly
- ✅ `pf --help` displays usage information

### Task Execution Testing

Uses `pf-runner/test.pf` which contains:
```pf
env name="test-app"

task hello
  describe Say hello to the world
  shell echo "Hello from ${name}!"
  shell date
end

task vars name="default"
  describe Test variable substitution  
  shell echo "Task parameter: ${name}"
end
```

## Findings and Recommendations

### ✅ What Works
1. **Direct Execution**: Running `pf_main.py` directly works perfectly
2. **Static Installer Syntax**: `install-static.sh` has no syntax errors
3. **Test Files**: `test.pf` provides good test coverage for basic functionality

### ❌ What Needs Fixing
1. **Static Executable**: Needs to be built for full test coverage
   - Run `cd pf-runner-full && make build-static`

### 📋 Future Enhancements

1. **Additional Test Coverage**:
   - Shell completion installation tests
   - Debian package (.deb) tests
   - RPM package tests
   - Arch package (PKGBUILD) tests
   - Makefile target tests

2. **CI/CD Integration**:
   - Add to GitHub Actions workflow
   - Run on multiple operating systems
   - Test different Python versions

3. **Advanced Functionality Tests**:
   - Remote execution tests (fabric/SSH)
   - Complex task dependencies
   - Error handling and recovery
   - Configuration file parsing

## Integration with Existing Tests

This test suite complements existing installation tests:

- **Existing**: `tests/installation/test-native-install.sh` (Bash-based)
- **New**: `tests/installation/test_installer_comprehensive.py` (Python-based)
- **Existing**: `test_installers.sh` (Root-level comprehensive bash tests)

The Python-based suite provides:
- Better integration with pytest framework
- Easier to extend and maintain
- More detailed assertions
- Better error reporting
- Automatic cleanup

## Example Test Output

```
$ pytest tests/installation/test_installer_comprehensive.py -v
================================================= test session starts ==================================================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0
collecting ... collected 12 items                                                                                                      

tests/installation/test_installer_comprehensive.py::TestNativeInstall::test_install_native XFAIL              [  8%]
tests/installation/test_installer_comprehensive.py::TestStaticInstall::test_install_static SKIPPED           [ 16%]
tests/installation/test_installer_comprehensive.py::TestStaticInstall::test_static_version SKIPPED           [ 25%]
tests/installation/test_installer_comprehensive.py::TestStaticInstall::test_static_list SKIPPED              [ 33%]
tests/installation/test_installer_comprehensive.py::TestStaticInstall::test_static_run_task SKIPPED          [ 41%]
tests/installation/test_installer_comprehensive.py::TestDirectExecution::test_direct_version PASSED          [ 50%]
tests/installation/test_installer_comprehensive.py::TestDirectExecution::test_direct_list PASSED             [ 58%]
tests/installation/test_installer_comprehensive.py::TestDirectExecution::test_direct_run_task PASSED         [ 66%]
tests/installation/test_installer_comprehensive.py::TestDirectExecution::test_direct_parameter_passing PASSED [ 75%]
tests/installation/test_installer_comprehensive.py::TestStaticExecutable::test_static_exe_version SKIPPED    [ 83%]
tests/installation/test_installer_comprehensive.py::TestStaticExecutable::test_static_exe_list SKIPPED       [ 91%]
tests/installation/test_installer_comprehensive.py::TestStaticExecutable::test_static_exe_run_task SKIPPED   [100%]

============================================ 4 passed, 7 skipped, 1 xfailed in 1.5s =============================================
```

## Conclusion

This comprehensive test suite successfully:
1. ✅ Validates direct pf_main.py execution
2. ⏭️ Provides framework for testing static installations (ready when built)
3. ❌ Identifies critical bugs in install.sh (documented and marked as xfail)

The test suite is ready for CI/CD integration and will automatically validate when the native installer is fixed.

## Next Steps

1. **For Developers**: Fix install.sh bugs identified in this document
2. **For CI/CD**: Integrate these tests into the build pipeline
3. **For Maintainers**: Build static executable to enable full test coverage
4. **For Testing**: Add additional test cases as installers are improved

---

**Test Suite Created**: March 2, 2026  
**Status**: Ready for use  
**Test Framework**: pytest  
**Integration**: pytest.ini configured  
