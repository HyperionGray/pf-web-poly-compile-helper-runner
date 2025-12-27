# Known Issues in pf_parser.py (Pre-existing)

This document tracks known issues in pf_parser.py that were present before the current PR and require future work.

## Critical Missing Definitions

### 1. PFY_EMBED Variable
**Lines affected**: 816, 819
**Issue**: Variable `PFY_EMBED` is referenced but not defined
**Impact**: Will cause NameError when fallback Pfyfile is needed
**Priority**: High
**Suggested fix**: Define PFY_EMBED with a default embedded Pfyfile content string

### 2. BUILTINS Variable  
**Lines affected**: 1117, 1232
**Issue**: Variable `BUILTINS` is referenced but not defined
**Impact**: Will cause NameError when checking for built-in tasks
**Priority**: High
**Suggested fix**: Define BUILTINS dict with default built-in tasks

### 3. Missing textwrap Import
**Line affected**: 226
**Issue**: `textwrap` module used but not imported
**Impact**: Will cause NameError when text wrapping is needed
**Priority**: Medium
**Suggested fix**: Add `import textwrap` at file top

## Missing Utility Functions

The following functions are imported by pf_main.py but not defined in pf_parser.py:

1. `_normalize_hosts()` - Normalize host specifications
2. `_merge_env_hosts()` - Merge environment-based host lists
3. `_dedupe_preserve_order()` - Remove duplicates while preserving order
4. `_parse_host()` - Parse individual host specifications
5. `_c_for()` - Create connection for host
6. `_exec_line_fabric()` - Execute line using Fabric
7. `list_dsl_tasks_with_desc()` - List tasks with descriptions  
8. `get_alias_map()` - Get task alias mappings

**Impact**: Unit tests fail, advanced features unavailable
**Priority**: High  
**Estimated effort**: Medium (2-4 hours to implement all)

## Recommendations

### Immediate (Block current functionality)
1. Define PFY_EMBED with minimal default tasks
2. Define BUILTINS with standard built-in commands
3. Add textwrap import

### Short-term (Enable full testing)
1. Implement all missing utility functions
2. Verify pf_main.py can import successfully
3. Re-enable full unit test suite

### Long-term (Architecture)
1. Consider splitting pf_parser.py into smaller, focused modules
2. Add comprehensive unit tests for each function
3. Establish CI/CD to catch missing definitions early

## Notes

- These issues pre-dated the current PR (commit dad4407)
- The current PR focused on minimal changes to enable E2E testing
- E2E tests pass because they use higher-level interfaces that don't trigger these issues
- Full resolution requires dedicated refactoring effort

---
**Document Created**: December 26, 2025  
**Context**: Testing initiative - "test it all again" x3  
**Status**: Known issues documented for future work
