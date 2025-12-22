#!/usr/bin/env python3
"""
Flexible syntax patch for pf-runner.

This patch modifies the pf parser to support flexible syntax where
shell commands don't require the explicit "shell" verb.
"""

def apply_flexible_syntax_patch():
    """
    Apply the flexible syntax patch to pf_parser.py
    
    This function modifies the verb detection logic to:
    1. Define a set of known DSL verbs
    2. Default to shell execution for unrecognized verbs
    3. Maintain backward compatibility
    """
    
    # The patch replaces the verb dispatch logic
    original_dispatch = '''    # Dispatch by verb
    if verb == "shell":'''
    
    flexible_dispatch = '''    # Define known DSL verbs (non-shell commands)
    KNOWN_VERBS = {
        "packages", "sync", "service", "directory", "copy", "makefile", "make",
        "cmake", "meson", "ninja", "cargo", "go_build", "gobuild", "configure", 
        "justfile", "just", "autobuild", "auto_build", "build_detect", "detect_build",
        "env", "shell_lang", "describe"
    }
    
    # Check if this is a known DSL verb or should default to shell
    is_shell_command = verb not in KNOWN_VERBS
    
    # Handle shell commands (explicit "shell" verb or default behavior)
    if verb == "shell" or is_shell_command:
        # For default shell behavior, the entire line is the command
        shell_cmd = rest_of_line if verb == "shell" else stripped'''
    
    return original_dispatch, flexible_dispatch

def create_syntax_validation_tasks():
    """
    Create pf check and pf fix tasks for syntax validation.
    """
    
    check_task = '''
task pf-check [alias check]
  describe Validate pf syntax and report issues
  shell_lang python
  shell import os, re, sys
  shell 
  shell def check_pf_syntax(file_path="Pfyfile.pf"):
  shell     """Check pf file syntax and report issues."""
  shell     if not os.path.exists(file_path):
  shell         print(f"Error: {file_path} not found")
  shell         return False
  shell     
  shell     with open(file_path, 'r') as f:
  shell         content = f.read()
  shell     
  shell     issues = []
  shell     lines = content.splitlines()
  shell     in_task = False
  shell     
  shell     for i, line in enumerate(lines, 1):
  shell         stripped = line.strip()
  shell         if not stripped or stripped.startswith('#'):
  shell             continue
  shell             
  shell         if stripped.startswith('task '):
  shell             in_task = True
  shell             continue
  shell         elif stripped == 'end':
  shell             in_task = False
  shell             continue
  shell             
  shell         if in_task:
  shell             # Check for common issues
  shell             if stripped.startswith('shell ') and len(stripped) > 6:
  shell                 # Suggest removing shell prefix for simple commands
  shell                 cmd = stripped[6:].strip()
  shell                 if not cmd.startswith('[lang:') and not '<<' in cmd:
  shell                     issues.append(f"Line {i}: Consider removing 'shell ' prefix: {stripped}")
  shell     
  shell     if issues:
  shell         print("Syntax suggestions:")
  shell         for issue in issues:
  shell             print(f"  {issue}")
  shell         return False
  shell     else:
  shell         print("✓ Syntax looks good!")
  shell         return True
  shell 
  shell check_pf_syntax()
end

task pf-fix [alias fix]
  describe Automatically fix common pf syntax issues
  shell_lang python
  shell import os, re, sys, shutil
  shell 
  shell def fix_pf_syntax(file_path="Pfyfile.pf", backup=True):
  shell     """Fix common pf syntax issues."""
  shell     if not os.path.exists(file_path):
  shell         print(f"Error: {file_path} not found")
  shell         return False
  shell     
  shell     if backup:
  shell         backup_path = f"{file_path}.backup"
  shell         shutil.copy2(file_path, backup_path)
  shell         print(f"Created backup: {backup_path}")
  shell     
  shell     with open(file_path, 'r') as f:
  shell         content = f.read()
  shell     
  shell     lines = content.splitlines()
  shell     fixed_lines = []
  shell     in_task = False
  shell     fixes_applied = 0
  shell     
  shell     for line in lines:
  shell         stripped = line.strip()
  shell         
  shell         if stripped.startswith('task '):
  shell             in_task = True
  shell             fixed_lines.append(line)
  shell             continue
  shell         elif stripped == 'end':
  shell             in_task = False
  shell             fixed_lines.append(line)
  shell             continue
  shell             
  shell         if in_task and stripped.startswith('shell '):
  shell             # Remove unnecessary shell prefixes for simple commands
  shell             cmd = stripped[6:].strip()
  shell             if cmd and not cmd.startswith('[lang:') and not '<<' in cmd:
  shell                 # Keep the original indentation
  shell                 indent = len(line) - len(line.lstrip())
  shell                 fixed_line = ' ' * indent + cmd
  shell                 fixed_lines.append(fixed_line)
  shell                 fixes_applied += 1
  shell             else:
  shell                 fixed_lines.append(line)
  shell         else:
  shell             fixed_lines.append(line)
  shell     
  shell     if fixes_applied > 0:
  shell         with open(file_path, 'w') as f:
  shell             f.write('\\n'.join(fixed_lines) + '\\n')
  shell         print(f"✓ Applied {fixes_applied} syntax fixes to {file_path}")
  shell     else:
  shell         print("No fixes needed")
  shell     
  shell     return True
  shell 
  shell fix_pf_syntax()
end
'''
    
    return check_task

def create_agents_guide():
    """
    Create AGENTS.md guide for AI agents.
    """
    
    agents_md = '''# pf Task Runner Guide for AI Agents

This guide helps AI agents understand and use the pf task runner effectively.

## Quick Reference

### Basic Syntax

pf uses a clean, symbol-free DSL for defining tasks. **Shell commands no longer require the "shell" prefix** - they work by default.

```pf
task example-task
  describe This is what the task does
  echo "Hello World"                    # Direct shell command (NEW!)
  ls -la                               # Another shell command
  packages install curl wget           # DSL verb for package management
  echo "Installation complete"         # Back to shell commands
end
```

### Task Definition

```pf
task task-name [alias short-name]
  describe Brief description of what this task does
  # Task body with commands
end
```

### Parameter Passing

All these formats are equivalent:
```bash
pf my-task key=value
pf my-task --key=value  
pf my-task --key value
pf my-task key="value with spaces"
```

### Flexible Command Syntax

**NEW: No "shell" prefix needed for most commands!**

```pf
task build-app
  describe Build the application
  # These all work without "shell" prefix:
  echo "Starting build..."
  mkdir -p build
  cd build
  cmake ..
  make -j4
  echo "Build complete!"
end
```

### When to Use Explicit Verbs

Use explicit verbs for DSL operations:

```pf
task setup-system
  describe Set up the system
  packages install git curl build-essential    # Package management
  service start nginx                          # Service management  
  directory /var/www/app mode=755             # Directory creation
  copy local_file=config.yml remote_file=/etc/app/config.yml
  
  # Regular shell commands (no prefix needed):
  echo "System setup complete"
  systemctl status nginx
end
```

### Polyglot Language Support

Use `[lang:language]` for non-bash languages:

```pf
task analyze-data
  describe Analyze data with Python
  [lang:python] import pandas as pd
  [lang:python] df = pd.read_csv('data.csv')
  [lang:python] print(df.describe())
  
  # Or use shell_lang to set language for multiple commands:
  shell_lang python
  import numpy as np
  result = np.mean(df['values'])
  print(f"Mean: {result}")
end
```

### Multi-line Code Blocks

Use heredoc syntax for longer code:

```pf
task complex-analysis
  describe Run complex Python analysis
  [lang:python] << PYEOF
import pandas as pd
import matplotlib.pyplot as plt

# Load and analyze data
df = pd.read_csv('data.csv')
summary = df.describe()
print(summary)

# Create visualization
plt.figure(figsize=(10, 6))
plt.plot(df['x'], df['y'])
plt.savefig('analysis.png')
PYEOF
end
```

## DSL Verbs Reference

### Package Management
```pf
packages install package1 package2
packages remove old-package
```

### Service Management  
```pf
service start service-name
service stop service-name
service restart service-name
service enable service-name
service disable service-name
```

### File Operations
```pf
directory /path/to/dir mode=755 owner=user
copy local_file=src.txt remote_file=dest.txt
sync src=/local/path dest=/remote/path
```

### Build Systems
```pf
autobuild                    # Auto-detect and build
makefile all jobs=4         # Make with parallel jobs
cmake . build_dir=build     # CMake configuration
cargo build release=true    # Rust build
go_build output=myapp       # Go build
```

## Common Patterns for AI Agents

### 1. Simple Shell Task
```pf
task hello
  describe Print a greeting
  echo "Hello from pf!"
  date
  whoami
end
```

### 2. Build and Test
```pf
task build-and-test
  describe Build project and run tests
  echo "Building..."
  autobuild release=true
  echo "Running tests..."
  ./run-tests.sh
  echo "Complete!"
end
```

### 3. System Setup
```pf
task setup-dev-env
  describe Set up development environment
  packages install git curl nodejs npm
  npm install -g typescript
  git config --global user.name "Developer"
  echo "Development environment ready"
end
```

### 4. Multi-language Processing
```pf
task process-data
  describe Process data with multiple tools
  echo "Starting data processing..."
  
  [lang:python] 
  import json
  with open('input.json') as f:
      data = json.load(f)
  
  [lang:node]
  const fs = require('fs');
  const processed = require('./process.js')(data);
  fs.writeFileSync('output.json', JSON.stringify(processed));
  
  echo "Data processing complete"
end
```

### 5. Deployment Task
```pf
task deploy [alias dp]
  describe Deploy application to server
  echo "Deploying to $environment..."
  autobuild release=true
  sync src=./build dest=/var/www/app
  service restart myapp
  echo "Deployment to $environment complete"
end
```

## Best Practices for AI Agents

### 1. Always Include Descriptions
```pf
task my-task
  describe Clear description of what this task does  # Always include this!
  # ... task body
end
```

### 2. Use Parameters for Flexibility
```pf
task deploy-to-env
  describe Deploy to specified environment
  echo "Deploying to environment: $env"
  ./deploy.sh --env=$env --version=$version
end
```

Call with: `pf deploy-to-env env=staging version=1.2.3`

### 3. Provide Aliases for Common Tasks
```pf
task build-application [alias build|alias b]
  describe Build the application
  autobuild release=true
end
```

### 4. Use Appropriate Verbs
- Use bare commands for shell operations
- Use `packages` for package management
- Use `service` for service control
- Use `autobuild` for building projects

### 5. Handle Errors Gracefully
```pf
task safe-deploy
  describe Deploy with error checking
  if ! ./run-tests.sh; then
    echo "Tests failed, aborting deployment"
    exit 1
  fi
  echo "Tests passed, proceeding with deployment"
  ./deploy.sh
end
```

## Migration from Old Syntax

If you see old pf files with `shell` prefixes everywhere:

**Old syntax:**
```pf
task old-style
  shell echo "hello"
  shell ls -la
  shell mkdir build
end
```

**New flexible syntax:**
```pf
task new-style
  echo "hello"      # No shell prefix needed!
  ls -la           # Much cleaner
  mkdir build      # More intuitive
end
```

Use `pf fix` to automatically convert old syntax to new flexible syntax.

## Validation and Fixing

- `pf check` - Validate syntax and get suggestions
- `pf fix` - Automatically fix common syntax issues

## Summary for AI Agents

1. **Default to shell commands** - no "shell" prefix needed
2. **Use DSL verbs** for specific operations (packages, service, etc.)
3. **Always include descriptions** for tasks
4. **Use parameters** for flexibility (`$param` syntax)
5. **Provide aliases** for commonly used tasks
6. **Use polyglot syntax** `[lang:xxx]` for non-bash languages
7. **Test with `pf check`** before committing

The pf syntax is designed to be intuitive - if it looks like a shell command, it probably is one!
'''
    
    return agents_md

if __name__ == "__main__":
    print("Flexible syntax patch utilities loaded")
    print("Use apply_flexible_syntax_patch() to get patch content")
    print("Use create_syntax_validation_tasks() to get validation tasks")
    print("Use create_agents_guide() to get AGENTS.md content")