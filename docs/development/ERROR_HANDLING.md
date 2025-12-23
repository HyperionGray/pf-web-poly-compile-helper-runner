# PF Error Handling

## Overview

The pf runner includes comprehensive error handling that provides detailed context about failures to help users quickly diagnose and fix issues. The error handling philosophy is **transparency** - show users exactly what went wrong, where it happened, and what the environment looked like.

## Key Features

### 1. Custom Exception Classes

All pf-related errors use specialized exception classes that capture:
- Full Python tracebacks
- Environment variables at time of failure
- Execution context (container, subshell, platform, user)
- Task and command being executed
- Helpful suggestions for fixing the issue

### 2. Environment Context Detection

Every error message includes:
- **Container Detection**: Identifies Docker, Podman, Kubernetes, LXC containers
- **Subshell Depth**: Shows how many subshell levels deep you are
- **Platform Information**: OS, distribution, architecture, Python version
- **User Context**: Current user, working directory, privileges
- **Environment Variables**: Relevant variables like PATH, HOME, SHELL, etc.

### 3. Smart Error Suggestions

The error handler provides context-aware suggestions:
- **Task not found**: Shows similar task names you might have meant
- **Command failures**: Suggests checking PATH, permissions, or installation
- **PE executables on Linux**: Detects Windows binaries and suggests Wine
- **Syntax errors**: Points to the exact line and suggests fixes
- **Missing environment variables**: Identifies what's missing and how to set it

## Exception Types

### PFException (Base Class)
Base class for all pf-related exceptions with full context capture.

### PFSyntaxError
Raised for syntax errors in PF files:
- Unclosed blocks (task, if, for)
- Invalid operators
- Missing keywords
- Malformed task definitions

**Example:**
```
======================================================================
PF ERROR
======================================================================
Task: test-unclosed
File: /tmp/test.pf, line 2

Error: Unclosed 'task' block 'test-unclosed' - missing 'end'

Suggestion: Add 'end' to close the task block

Execution Context:
  Container: Not in a container
  Subshell: 1 level deep
  Platform: Ubuntu 24.04.3 LTS (x86_64)
  Python: 3.12.3
  CWD: /home/user/project
  User: UID 1000 (non-root)
======================================================================
```

### PFExecutionError
Raised when commands fail to execute:
- Non-zero exit codes
- Subprocess launch failures
- Remote command execution failures

**Example:**
```
======================================================================
PF ERROR
======================================================================
Task: install-deps
Command: npm install --production

Error: Command failed with exit code 127
Exit Code: 127

Suggestion: Command not found. Check that 'npm' is installed and in your PATH

Execution Context:
  Container: Not in a container
  Subshell: 1 level deep
  Platform: Ubuntu 24.04.3 LTS (x86_64)
  Python: 3.12.3
  CWD: /home/user/project
  User: UID 1000 (non-root)

Relevant Environment Variables:
  HOME=/home/user
  NODE_ENV=production
  PATH=/usr/local/bin:/usr/bin:/bin
======================================================================
```

### PFTaskNotFoundError
Raised when a requested task doesn't exist.

**Example:**
```
======================================================================
PF ERROR
======================================================================
Task: biuld

Error: Task 'biuld' not found

Suggestion: Run 'pf list' to see all available tasks

Execution Context:
  Container: Not in a container
  Subshell: 1 level deep
  Platform: Ubuntu 24.04.3 LTS (x86_64)
  Python: 3.12.3
  CWD: /home/user/project
  User: UID 1000 (non-root)
======================================================================
```

### PFConnectionError
Raised for SSH/remote connection failures.

### PFEnvironmentError
Raised for environment-related issues:
- Missing environment variables
- Failed environment variable expansion
- Path resolution failures

## Special Error Detection

### PE Executable Detection
When trying to run Windows executables on Linux, pf automatically detects this and provides helpful suggestions:

```
======================================================================
PF ERROR
======================================================================
Task: run-windows-app
Command: ./app.exe

Error: Command failed with exit code 126
Exit Code: 126

Suggestion: You appear to be trying to execute a Windows PE executable 
(./app.exe) on Linux. Consider using Wine or running this in a 
Windows environment.
======================================================================
```

### Container Environment Detection
pf automatically detects when running inside containers and includes this in error messages:

```
Execution Context:
  Container: Running in docker container
  Subshell: 2 levels deep
  Platform: Ubuntu 24.04.3 LTS (x86_64)
  Python: 3.12.3
  CWD: /app
  User: UID 0 (root)
```

### Subshell Environment Issues
When environment variables don't propagate correctly in subshells, pf alerts you:

```
Note: You are 3 subshell levels deep. Environment variables may not 
have propagated correctly.
```

## Best Practices

### 1. Always Check the Full Error Output
Don't just look at the error message - the environment context often reveals the real issue.

### 2. Pay Attention to Suggestions
The error handler provides context-aware suggestions. These are based on the specific error and environment.

### 3. Use Debug Mode for Development
Enable debug mode to see full tracebacks:
```bash
pf debug-on
```

Disable when done:
```bash
pf debug-off
```

### 4. Use pf prune for Syntax Checking
Before running tasks, check syntax:
```bash
pf prune -v
```

This will show all syntax errors with full context.

### 5. Check Container/Environment Context
If a command works outside pf but fails inside, check:
- Are you in a container?
- How deep are you in subshells?
- Are environment variables set correctly?

## Debugging Tips

### Issue: Command works in shell but not in pf

**Check:**
1. Environment variables - run `env` in your shell vs in pf
2. Working directory - pf runs from the Pfyfile location
3. PATH - especially in containers or when using sudo

### Issue: Task not found

**Check:**
1. Run `pf list` to see all available tasks
2. Check for typos in task name
3. Verify the Pfyfile is in the current directory or parent directories

### Issue: Permission denied

**Check:**
1. User context in error message (are you root when you shouldn't be?)
2. File permissions on scripts you're trying to execute
3. SELinux or AppArmor policies (in containers)

### Issue: Command not found

**Check:**
1. Is the program installed?
2. Is it in your PATH? (shown in error environment variables)
3. Are you in a container with a minimal environment?

## Error Handling in Scripts

If you're importing pf modules in your own scripts, you can use the exception handling:

```python
from pf_exceptions import (
    PFException,
    PFExecutionError,
    format_exception_for_user
)

try:
    # Your code here
    pass
except PFException as e:
    # Format and display pf exceptions
    print(format_exception_for_user(e, include_traceback=True))
except Exception as e:
    # Format any exception with context
    print(format_exception_for_user(e, include_traceback=True))
```

## Contributing

When adding new error handling:

1. **Use the appropriate exception class** - don't use generic Exception
2. **Provide helpful suggestions** - what should the user do to fix it?
3. **Include relevant context** - task name, command, file path, line number
4. **Test in different environments** - containers, different platforms, subshells

## Related Documentation

- [PF Syntax Checking](./SYNTAX_CHECKING.md) - Details on syntax validation
- [PF Debugging](./DEBUGGING.md) - Advanced debugging techniques
- [PF Environment Variables](./ENVIRONMENT.md) - Environment variable handling
