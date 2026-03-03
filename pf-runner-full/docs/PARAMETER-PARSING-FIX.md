# Parameter Parsing Fix - Implementation Summary

## Issue
Tasks defined with parameters like `task vx-pfs-up remote-addr=""` were being registered with the full definition including parameters as the task name, rather than just the task name itself. This caused task lookup failures when users tried to run tasks with parameters.

## Problem Example
Before the fix:
- Task definition: `task vx-pfs-up remote-addr=""`
- Registered as: `vx-pfs-up remote-addr=""` (full line)
- User tries: `pf vx-pfs-up remote-addr=100.98.73.70`
- Result: ❌ Error: "no such task: vx-pfs-up"

## Solution
Modified the task parser to:
1. Extract task name separately from parameter definitions
2. Store default parameter values in the Task object
3. Match tasks by name only (ignoring parameters)
4. Merge default parameters with user-provided parameters at runtime

## Implementation Changes

### 1. Task Class Enhancement
```python
class Task:
    def __init__(self, name: str, source_file: Optional[str] = None, params: Optional[Dict[str, str]] = None):
        self.name = name
        self.lines: List[str] = []
        self.description: Optional[str] = None
        self.source_file = source_file
        self.params: Dict[str, str] = params or {}  # Default parameter values
```

### 2. New Parser Function
Added `_parse_task_definition()` to split task definitions:
```python
def _parse_task_definition(line: str) -> Tuple[str, Dict[str, str]]:
    """
    Parse a task definition line to extract task name and parameters.
    
    Examples:
        "task my-task" -> ("my-task", {})
        "task my-task param1=value1" -> ("my-task", {"param1": "value1"})
        "task my-task param1=\"\" param2=default" -> ("my-task", {"param1": "", "param2": "default"})
    """
```

### 3. Variable Interpolation Fix
Updated regex to support hyphens in parameter names:
```python
# Before: _VAR_RE = re.compile(r"\$(\w+)|\$\{(\w+)\}")
# After:  _VAR_RE = re.compile(r"\$([a-zA-Z_][\w-]*)|\$\{([a-zA-Z_][\w-]*)\}")
```

### 4. Parameter Merging at Runtime
When executing tasks, default parameters are merged with user-provided parameters:
```python
# Start with default parameters from task definition
merged_params = dict(task_obj.params)
# Override with provided parameters
merged_params.update(params)
params = merged_params
```

## Supported Syntax

After the fix, all these syntaxes work correctly:

1. **Basic parameter passing:**
   ```bash
   pf vx-pfs-up remote-addr=100.98.73.70
   ```

2. **Double-dash prefix:**
   ```bash
   pf vx-pfs-up --remote-addr=100.98.73.70
   ```

3. **Using default values:**
   ```bash
   pf vx-pfs-up  # Uses remote-addr=""
   ```

4. **Multiple parameters:**
   ```bash
   pf task-name param1=value1 param2=value2 param3=value3
   ```

5. **Partial overrides:**
   ```bash
   pf task-name param2=custom  # param1 and param3 use defaults
   ```

## Testing

Created comprehensive test suite:
- `test_params.pf`: 10 test tasks covering various scenarios
- `test_params.sh`: Automated test script with 20 test cases
- `test_issue_scenario.pf`: Exact reproduction of the reported issue

All tests pass successfully.

## Backward Compatibility

✅ Fully backward compatible:
- Existing tasks without parameters work unchanged
- Existing parameter passing syntax continues to work
- No breaking changes to the DSL

## Benefits

1. **Cleaner task definitions:** Parameters are visually separated from task name
2. **Better task discovery:** Tasks are listed by name only in `pf list`
3. **Type safety:** Parameters have explicit default values
4. **More intuitive:** Matches user expectations for parameter passing
5. **Flexible:** Both `param=value` and `--param=value` syntaxes work

## Files Modified

- `pf-runner/pf_parser.py`: Core implementation changes
- `pf-runner/test_params.pf`: New test file
- `pf-runner/test_params.sh`: New test script
- `pf-runner/test_issue_scenario.pf`: Issue reproduction test

## Security

✅ CodeQL scan: No security vulnerabilities detected
✅ Code review: All feedback addressed
