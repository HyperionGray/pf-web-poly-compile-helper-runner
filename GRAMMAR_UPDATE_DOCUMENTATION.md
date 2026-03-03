# Grammar Update Documentation

This document describes the grammar improvements implemented to address the GitHub issue.

## Summary of Changes

The grammar has been updated to be more flexible and support cloud action declarations, addressing all points from the issue:

### 1. Whitespace Handling ✓

**Status**: Already implemented via `%ignore WS`

The grammar properly ignores whitespace between tokens, allowing flexible indentation:

```pf
task foo
  describe hi    # indentation is flexible
    shell echo "hello"
end
```

### 2. Blank Lines Support ✓

**Status**: Implemented

Blank lines are now allowed in multiple places:

- Empty files and files with only comments
- Between statements (tasks, env vars, comments)
- Inside task bodies
- Inside if/else blocks
- Inside for loops

```pf
# File can start with blank lines


task test

  describe test with blank lines
  
  shell echo "command 1"
  
  shell echo "command 2"

end


# Multiple blank lines between tasks
```

### 3. Variable Syntax Enhancement ✓

**Status**: Implemented

Both `$var` and `${var}` syntax are now supported:

```pf
task test
  describe Test both syntaxes
  
  if $simple_var
    shell echo "Simple syntax"
  end
  
  if ${braced_var}
    shell echo "Braced syntax"
  end
  
  if ${environment} == "production"
    shell echo "Production mode"
  end
end
```

**Grammar Rule**:
```lark
variable: "$" IDENTIFIER | "${" IDENTIFIER "}"
```

### 4. Comment Behavior Documentation ✓

**Status**: Documented

Comments are only recognized as pf comments when `#` appears as the first non-whitespace character on a line. Within `TEXT_LINE` contexts (like shell commands), `#` is treated as part of the command text:

```pf
# This is a pf comment

task test
  describe test
  shell echo "This # is part of the shell command"
  shell grep '#pattern' file.txt   # This # is also part of the command
end
```

This behavior is intentional and allows shell/script comments to work naturally.

### 5. Cloud Action Task Headers ✓

**Status**: Implemented

New optional task header statements for declaring capabilities and resource requirements:

#### timeout

Specify maximum execution time:

```pf
task long-running
  describe Long running task
  timeout 30m
  shell ./slow-process.sh
end
```

#### sandbox

Declare sandbox environment:

```pf
task build
  describe Build in container
  sandbox container    # Options: microvm, container, host
  shell make build
end
```

#### network

Specify network access level:

```pf
task deploy
  describe Deploy with network restrictions
  network restricted    # Options: restricted, allowlist, open
  shell ./deploy.sh
end
```

#### allowlist

Define allowed hosts (when network=allowlist):

```pf
task npm-install
  describe Install from npm with allowlist
  network allowlist
  allowlist host=github.com host=npmjs.com host=registry.npmjs.org
  shell npm install
end
```

#### artifact

Declare artifacts produced by the task:

```pf
task build
  describe Build and produce artifacts
  artifact dist/app.tar.gz
  artifact build/logs/build.log
  shell ./build.sh
end
```

#### secrets

Declare required secrets:

```pf
task deploy
  describe Deploy with secrets
  secrets allow GITHUB_TOKEN NPM_TOKEN AWS_ACCESS_KEY
  shell ./deploy.sh
end
```

#### Complete Example

```pf
task production-deploy
  describe Deploy to production with full security
  
  timeout 1h
  sandbox microvm
  network allowlist
  allowlist host=github.com host=docker.io host=production.example.com
  artifact deploy-logs/deploy-$(date +%Y%m%d).log
  secrets allow GITHUB_TOKEN DOCKER_TOKEN PROD_DEPLOY_KEY
  
  shell echo "Deploying to production..."
  shell ./scripts/deploy-prod.sh
end
```

## Grammar Rules Added/Modified

### Start Rule (Modified)
```lark
start: (statement | NEWLINE)+
```
Allows blank lines at file level.

### Task Rule (Modified)
```lark
task: "task" IDENTIFIER (param | alias_def)* NEWLINE (task_body | NEWLINE)+ "end"
```
Allows blank lines in task bodies.

### If Statement Rule (Modified)
```lark
if_stmt: "if" condition NEWLINE if_body else_body? "end"
if_body: (task_body | NEWLINE)+
else_body: "else" NEWLINE (task_body | NEWLINE)+
```
Allows blank lines in if/else blocks.

### For Loop Rule (Modified)
```lark
for_loop: "for" IDENTIFIER "in" iterable NEWLINE (task_body | NEWLINE)+ "end"
```
Allows blank lines in for loop bodies.

### Variable Rule (Modified)
```lark
variable: "$" IDENTIFIER | "${" IDENTIFIER "}"
```
Supports both `$var` and `${var}` syntax.

### New Cloud Action Rules (Added)
```lark
timeout_stmt: "timeout" TEXT_LINE
sandbox_stmt: "sandbox" IDENTIFIER
network_stmt: "network" IDENTIFIER
allowlist_stmt: "allowlist" TEXT_LINE
artifact_stmt: "artifact" TEXT_LINE
secrets_stmt: "secrets" TEXT_LINE
```

### Task Body Rule (Modified)
```lark
task_body: describe 
         | shell 
         | shell_lang 
         | env_stmt 
         | for_loop 
         | if_stmt 
         | sync_stmt
         | packages_stmt
         | service_stmt
         | directory_stmt
         | copy_stmt
         | makefile_stmt
         | cmake_stmt
         | meson_stmt
         | cargo_stmt
         | go_build_stmt
         | configure_stmt
         | justfile_stmt
         | autobuild_stmt
         | build_detect_stmt
         | timeout_stmt      # NEW
         | sandbox_stmt      # NEW
         | network_stmt      # NEW
         | allowlist_stmt    # NEW
         | artifact_stmt     # NEW
         | secrets_stmt      # NEW
```

## Testing

Comprehensive test suite in `tests/grammar/test_grammar_updates.py`:

- **Whitespace Handling**: 3 tests - all passing ✓
- **Blank Lines Support**: 5 tests - all passing ✓
- **Variable Syntax**: 4 tests - all passing ✓
- **Cloud Action Headers**: 7 tests - all passing ✓
- **Regression Tests**: 3 tests - all passing ✓

**Total**: 22 tests, all passing ✓

## Backward Compatibility

All changes are backward compatible. Existing `.pf` files continue to work as before:

- Whitespace handling was already implemented
- Blank lines are now optional but not required
- `$var` syntax continues to work alongside `${var}`
- New cloud action headers are optional
- Comment behavior remains unchanged

## Example File

See `pf-runner/example_grammar_features.pf` for a comprehensive demonstration of all new features.
