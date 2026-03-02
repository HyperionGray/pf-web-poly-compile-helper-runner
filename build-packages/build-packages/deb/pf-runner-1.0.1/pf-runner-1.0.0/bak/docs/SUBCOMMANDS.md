# Subcommands and Task Organization in pf

## Overview

**YES, pf supports subcommands!** Subcommands are automatically created from included Pfyfile files, providing a powerful way to organize and group related tasks.

## What are Subcommands?

Subcommands in pf are **automatically generated** from included Pfyfile configuration files. When you include a file like `Pfyfile.web-demo.pf`, pf automatically creates a `web-demo` subcommand containing all tasks from that file.

### How It Works

1. **Include Files**: When you include a Pfyfile in your main `Pfyfile.pf`:
   ```text
   include Pfyfile.web-demo.pf
   include Pfyfile.build-helpers.pf
   include Pfyfile.security.pf
   ```

2. **Automatic Subcommands**: pf automatically creates subcommands:
   - `pf web-demo <task>` - Tasks from Pfyfile.web-demo.pf
   - `pf build-helpers <task>` - Tasks from Pfyfile.build-helpers.pf
   - `pf security <task>` - Tasks from Pfyfile.security.pf

3. **Naming Convention**: The subcommand name is derived from the filename:
   - `Pfyfile.web-demo.pf` → `web-demo` subcommand
   - `Pfyfile.build_helpers.pf` → `build-helpers` subcommand (underscores → hyphens)
   - `Pfyfile.security.pf` → `security` subcommand

## Using Subcommands

### Basic Syntax

```bash
# General format
pf <subcommand> <task> [params...]

# Without subcommand (legacy/direct task execution)
pf run <task> [params...]

# Or even simpler (run is implicit)
pf <task> [params...]
```

### Examples

```bash
# Using subcommands
pf web-demo build-all
pf security scan url=http://localhost:8080
pf lifting install-tools
pf fuzzing build-target source=target.c

# Using tasks directly (works for all tasks)
pf run web-build-all
pf run security-scan url=http://localhost:8080
pf run install-retdec
pf run build-afl-target source=target.c

# With parameters
pf web-demo dev port=3000
pf security scan url=http://localhost verbose=true
pf lifting lift-binary binary=/path/to/binary
```

### Listing Tasks by Subcommand

The `pf list` command automatically organizes tasks by their source file (subcommand):

```bash
$ pf list

Built-ins:
  update  upgrade  install-base  ...

From Pfyfile.pf:
  default-task  setup  install  ...

[web-demo] From Pfyfile.web-demo.pf:
  web-build-all      - Build all WASM modules
  web-build-rust     - Build Rust to WASM
  web-dev            - Start development server
  ...

[security] From Pfyfile.security.pf:
  security-scan      - Run security vulnerability scan
  security-fuzz      - Fuzz web application endpoints
  ...

[lifting] From Pfyfile.lifting.pf:
  install-retdec     - Install RetDec binary lifter
  lift-binary-retdec - Lift binary to LLVM IR
  ...
```

## How Subcommands Mix with Task Display

### Organized by Source File

When you run `pf list`, tasks are automatically grouped by their source file:

1. **Built-in tasks** are shown first (update, upgrade, etc.)
2. **Main Pfyfile.pf tasks** are shown next
3. **Included file tasks** are shown under their subcommand name in brackets

### Prefix-Based Grouping

Within each source file, tasks are further grouped by prefix:

```bash
[web-demo] From Pfyfile.web-demo.pf:
  web-dev            - Development server

  [web-build]
    web-build-all    - Build all modules
    web-build-rust   - Build Rust module
    web-build-c      - Build C module
    
  [web-test]
    web-test         - Run tests
    web-test-e2e     - Run E2E tests
```

This dual organization (by source file AND by prefix) makes it easy to:
- Find related tasks quickly
- Understand task organization
- Navigate large projects with many tasks

## Creating Your Own Subcommands

### Step 1: Create a Pfyfile

Create a new Pfyfile with a descriptive name:

```bash
touch Pfyfile.myproject.pf
```

### Step 2: Define Tasks

Add tasks to your new Pfyfile:

```text
# Pfyfile.myproject.pf

task build
  describe Build the myproject application
  shell cargo build --release
end

task test
  describe Run myproject tests
  shell cargo test
end

task deploy
  describe Deploy myproject to production
  env ENV=production
  shell ./deploy.sh
end
```

### Step 3: Include in Main Pfyfile

Add an include statement to your main `Pfyfile.pf`:

```text
# Pfyfile.pf

include Pfyfile.myproject.pf

# ... other includes ...
```

### Step 4: Use Your Subcommand

```bash
# Via subcommand
pf myproject build
pf myproject test
pf myproject deploy

# Or directly (both work!)
pf run myproject-build
pf run myproject-test
pf run myproject-deploy
```

## Advanced Features

### Subcommand Help

Get help for a specific subcommand:

```bash
pf <subcommand> --help
pf web-demo --help
```

### Filtering by Subcommand

List tasks only from a specific subcommand:

```bash
pf list --subcommand web-demo
pf list --subcommand security
```

### Mixing with Global Options

Subcommands work seamlessly with global options:

```bash
# Run on remote hosts
pf --hosts=server1,server2 web-demo deploy

# With environment
pf --env=prod security scan

# With sudo
pf --sudo lifting install-tools

# Multiple options
pf --env=staging --hosts=server1 --sudo myproject deploy
```

## Best Practices

### 1. Organize by Domain

Group related tasks into domain-specific Pfyfiles:

- `Pfyfile.web.pf` - Web development tasks
- `Pfyfile.database.pf` - Database operations
- `Pfyfile.deploy.pf` - Deployment tasks
- `Pfyfile.security.pf` - Security testing tasks

### 2. Use Descriptive Names

Choose clear, descriptive subcommand names:

✅ Good:
- `Pfyfile.api-server.pf` → `api-server` subcommand
- `Pfyfile.frontend-build.pf` → `frontend-build` subcommand
- `Pfyfile.integration-tests.pf` → `integration-tests` subcommand

❌ Avoid:
- `Pfyfile.misc.pf` - Too vague
- `Pfyfile.stuff.pf` - Not descriptive
- `Pfyfile.tmp.pf` - Unclear purpose

### 3. Keep Task Prefixes Consistent

Within each subcommand, use consistent task name prefixes for automatic grouping:

```text
# Pfyfile.docker.pf
task docker-build
task docker-run
task docker-stop
task docker-clean
task docker-logs
```

This creates a `[docker]` group in the task list.

### 4. Document Your Subcommands

Add descriptions to your tasks:

```text
task build
  describe Build the application with optimizations
  shell cargo build --release
end
```

## Backward Compatibility

### Legacy Task Names Still Work

Even with subcommands, you can still use task names directly:

```bash
# These are equivalent:
pf web-demo build-all
pf run web-build-all
pf web-build-all          # Shortest form
```

### No Breaking Changes

Adding subcommands doesn't break existing workflows:
- All old task names continue to work
- Scripts using `pf <task>` syntax are unaffected
- CI/CD pipelines remain compatible

## Real-World Examples

### Example 1: Web Development Project

```text
# Pfyfile.frontend.pf
task build
  describe Build frontend assets
  shell npm run build
end

task dev
  describe Start development server
  shell npm run dev
end

task test
  describe Run frontend tests
  shell npm test
end

# Pfyfile.backend.pf
task build
  describe Build backend binary
  shell cargo build --release
end

task dev
  describe Start backend server
  shell cargo run
end

task test
  describe Run backend tests
  shell cargo test
end
```

Usage:
```bash
# Clear, unambiguous commands
pf frontend build
pf frontend dev
pf backend build
pf backend dev

# Or run both in sequence
pf frontend build && pf backend build
```

### Example 2: DevOps Automation

```text
# Pfyfile.infrastructure.pf
task provision
  describe Provision infrastructure with Terraform
  shell terraform apply -auto-approve
end

task destroy
  describe Destroy infrastructure
  shell terraform destroy -auto-approve
end

# Pfyfile.deployment.pf
task staging
  describe Deploy to staging environment
  env ENV=staging
  shell ./deploy.sh
end

task production
  describe Deploy to production environment
  env ENV=production
  shell ./deploy.sh
end

# Pfyfile.monitoring.pf
task start
  describe Start monitoring services
  shell docker-compose -f monitoring.yml up -d
end

task stop
  describe Stop monitoring services
  shell docker-compose -f monitoring.yml down
end
```

Usage:
```bash
# Infrastructure management
pf infrastructure provision
pf infrastructure destroy

# Deployments
pf deployment staging
pf deployment production

# Monitoring
pf monitoring start
pf monitoring stop
```

## Troubleshooting

### Subcommand Not Found

If a subcommand isn't recognized:

1. Check that the Pfyfile is included in your main `Pfyfile.pf`:
   ```text
   include Pfyfile.mysubcommand.pf
   ```

2. Verify the file exists and has the correct naming pattern:
   ```bash
   ls -la Pfyfile.*.pf
   ```

3. Try listing all tasks to see what's available:
   ```bash
   pf list
   ```

### Task Name Conflicts

If you have tasks with the same name in different subcommands:

```bash
# Use the subcommand to disambiguate
pf frontend build    # Builds frontend
pf backend build     # Builds backend

# Without subcommand, uses first found (order from includes)
pf build            # Might be ambiguous!
```

**Best practice**: Use unique task names or always use subcommands for clarity.

### Help Not Showing Subcommands

If `pf --help` doesn't show your subcommands, they might not be loaded yet. Subcommands are discovered dynamically when you run a command. Try:

```bash
pf list              # Forces discovery
pf <subcommand> --help   # Get help for specific subcommand
```

## Summary

✅ **Subcommands ARE supported** through automatic generation from included Pfyfiles

✅ **Organization is automatic** - tasks are grouped by source file in `pf list`

✅ **Usage is intuitive** - `pf <subcommand> <task> [params]`

✅ **Backward compatible** - all existing task names still work

✅ **Easy to extend** - just create a new Pfyfile and include it

✅ **Mixes perfectly with display** - tasks are organized both by source file (subcommand) and by prefix

The subcommand system in pf provides excellent organization without adding complexity, making it easy to manage large projects with hundreds of tasks across multiple domains.
