# Critical File Corruption Issue in pf_parser.py

## Problem Summary

The file `pf-runner/pf_parser.py` contains a critical corruption that prevents both native and container installers from functioning. This corruption exists in the base repository commit and blocks all installation paths.

## Technical Details

### Location of Corruption
- **File**: `pf-runner/pf_parser.py`
- **Line**: 941 onwards
- **Function**: `parse_pfyfile_text()`

### What's Wrong

The `parse_pfyfile_text()` function (lines 941-1243) has had its implementation replaced with code that should be in a `main()` function. Specifically:

1. **Function signature is correct** (line 941-943):
   ```python
   def parse_pfyfile_text(
       text: str, task_sources: Optional[Dict[str, str]] = None
   ) -> Dict[str, Task]:
   ```

2. **Function body is wrong** (lines 950+): Contains command-line argument parsing code like:
   - `if tasks[0] == "debug-off":`
   - `if tasks[0] == "prune":`
   - Host resolution logic
   - Task execution logic
   - etc.

3. **Missing main() function**: The file ends with (line 1242-1243):
   ```python
   if __name__ == "__main__":
       sys.exit(main(sys.argv[1:]))
   ```
   But `main()` is never defined!

4. **Missing exported functions** that `pf_main.py` needs:
   - `_normalize_hosts`
   - `_merge_env_hosts`
   - `_dedupe_preserve_order`
   - `_parse_host`
   - `_c_for`
   - `list_dsl_tasks_with_desc`
   - `get_alias_map`

### What parse_pfyfile_text() Should Do

Based on its usage throughout the codebase, this function should:
- Parse Pfyfile DSL text into a dictionary of Task objects
- Handle line continuation (backslash)
- Extract task definitions with their parameters, descriptions, and commands
- Return `Dict[str, Task]` where keys are task names

### Impact

❌ **Native Installer**: Cannot execute `pf_parser.py` - fails with `NameError: name 'main' is not defined`

❌ **Container Installer**: Unknown - depends on whether containers have a working version

❌ **All pf Commands**: Cannot execute because the entry point doesn't work

## Root Cause

This corruption appears to have been introduced in the initial repository commit (dad4407). It suggests either:
1. An incomplete merge or rebase operation
2. A file copy/paste error during repository setup  
3. Accidental overwrite of the function body

## Evidence

### Test Results
Running the native installer test (`tests/installation/test-native-install.sh`):
```
[TEST ERROR] pf --version failed
NameError: name 'main' is not defined. Did you mean: 'min'?
```

### Import Errors
When trying to use `pf_main.py` (which has a proper `main()` function):
```
ImportError: cannot import name '_normalize_hosts' from 'pf_parser'
```

## Potential Solutions

### Option 1: Recover Original File (RECOMMENDED)
- Obtain the original, working version of `pf_parser.py` from the source
- This is the only way to guarantee full functionality

### Option 2: Reconstruct from Context
Reconstruct the missing functions by:
1. Analyzing what `parse_pfyfile_text()` should actually do
2. Extracting the misplaced `main()` function code
3. Implementing the missing helper functions
4. This is complex and error-prone

### Option 3: Use pf_lark_parser.py
- Check if `pf_lark_parser.py` can be used as a drop-in replacement
- Would require refactoring imports throughout the codebase

### Option 4: Container-Only Approach
- If containers have a working version internally, focus solely on container installation
- Update docs to state native install is not supported

## Workaround for Development

Until this is fixed, developers can:

1. **Use Container Mode Only**:
   ```bash
   ./install.sh --runtime podman --skip-build
   ```
   (Assumes container images are pre-built with working code)

2. **Manual Function Stubs** (temporary, not recommended):
   Add minimal stubs to make imports work, but functionality will be limited

## Files Affected

- `pf-runner/pf_parser.py` - Primary corruption
- `install.sh` - Cannot complete native installation
- `pf-runner/Makefile` - References corrupted pf_parser.py
- `pf-runner/pf_main.py` - Cannot import from pf_parser.py
- All tools that depend on pf_parser.py

## Testing

A comprehensive test script has been created at:
```
tests/installation/test-native-install.sh
```

This test will pass once pf_parser.py is fixed.

## Recommendation

**This issue MUST be resolved before the installers can be tested or fixed.** The repository owners need to:

1. Locate the original working version of `pf_parser.py`
2. Replace the corrupted version
3. Re-test all installation methods
4. Verify all pf commands work correctly

Until then, all installer work is blocked.

---

**Issue Created**: 2025-12-26
**Discovered During**: Testing native installer for issue "Test installer - container AND native native first"
**Severity**: **CRITICAL** - Blocks all installation methods
