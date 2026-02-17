# Task Aliases Feature

## Overview

The pf task runner now supports **command aliases** - short, memorable names for longer task names. This makes it faster and easier to run frequently-used tasks.

## Defining Aliases

Add aliases to tasks using the `[alias name]` syntax in task definitions:

```pf
task long-command-name [alias cmd]
  describe A task with a short alias
  shell echo "This can be run as: pf cmd"
end

task build-and-deploy [alias bd|alias=deploy]
  describe Multiple aliases are supported
  shell echo "Can be run as: pf bd OR pf deploy"
end
```

### Alias Syntax

Two formats are supported:
- `[alias name]` - Space-separated
- `[alias=name]` - Equals-separated

Multiple aliases can be defined:
- `[alias a|alias b]` - Pipe-separated multiple aliases
- `[alias=a|alias=b]` - Also works with equals format

## Using Aliases

### Command Line

```bash
# Run task by full name
pf run long-command-name

# Run task by alias (automatically resolved)
pf cmd

# Also works with parameters
pf cmd param1=value1
```

### REST API

The REST API automatically exposes aliases at short endpoints:

```bash
# Access via full task name
GET  http://localhost:8000/pf/long-command-name
POST http://localhost:8000/pf/long-command-name

# Access via alias (shorter!)
GET  http://localhost:8000/cmd
POST http://localhost:8000/cmd
```

## Example: REST API Management

The `Pfyfile.rest-api.pf` demonstrates alias usage:

```pf
task rest-on [alias=ron]
  describe Start the pf REST API server
  # ... implementation ...
end

task rest-off [alias=roff]
  describe Stop the pf REST API server
  # ... implementation ...
end

task rest-dev [alias=rdev]
  describe Start REST API in development mode
  # ... implementation ...
end
```

Usage:
```bash
# Long form
pf rest-on
pf rest-off

# Short form (via aliases)
pf ron
pf roff
```

## API Integration

When you define a task with an alias, it becomes available at two endpoints:

1. **Full name**: `/pf/{task-name}` (e.g., `/pf/rest-on`)
2. **Alias**: `/{alias}` (e.g., `/ron`)

Both endpoints support:
- `GET` - Get task information
- `POST` - Execute the task

### API Example

```bash
# Get task info via full name
curl http://localhost:8000/pf/rest-on

# Get task info via alias
curl http://localhost:8000/ron

# Execute via alias
curl -X POST http://localhost:8000/ron \
  -H "Content-Type: application/json" \
  -d '{"params": {}}'
```

## Benefits

1. **Faster typing**: `pf ron` instead of `pf rest-on`
2. **Easier to remember**: Create memorable shortcuts
3. **API-friendly**: Shorter URLs for HTTP requests
4. **Backward compatible**: Full task names still work
5. **Multiple aliases**: One task can have several aliases

## Notes

- Aliases must be unique across all tasks
- Aliases are case-sensitive
- Aliases don't conflict with built-in commands
- Tasks can have multiple aliases
- Aliases work everywhere: CLI, API, scripts

## See Also

- [REST API Documentation](../README.md#pf-rest-api-server-) - REST API usage
- [Pfyfile.rest-api.pf](../Pfyfile.rest-api.pf) - Example alias definitions
- [Task Definition Syntax](QUICKSTART.md) - Complete task syntax guide
