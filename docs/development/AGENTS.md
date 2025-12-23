# pf Task Runner Guide for AI Agents

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

## Quick Copy-Paste Template

```pf
task my-new-task [alias mnt]
  describe What this task does
  echo "Starting task..."
  # Add your commands here (no shell prefix needed!)
  echo "Task complete!"
end
```

## Troubleshooting

### Common Issues

1. **Task not found**: Check task name spelling and use `pf list` to see available tasks
2. **Syntax errors**: Use `pf check` to validate your Pfyfile.pf
3. **Parameter issues**: Remember parameters use `$param` syntax inside tasks
4. **Language issues**: Use `[lang:python]` for non-bash languages

### Getting Help

- `pf list` - Show all available tasks
- `pf help` - Show general help
- `pf check` - Validate syntax
- `pf task-name --help` - Show help for specific task (if implemented)

This guide should help AI agents write effective pf tasks that follow current best practices and use the flexible syntax properly.