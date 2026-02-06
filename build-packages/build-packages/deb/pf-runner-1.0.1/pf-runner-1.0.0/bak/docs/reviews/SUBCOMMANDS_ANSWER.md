# Answer: Are we supporting subcommands?

## Short Answer

**YES!** pf already supports subcommands through automatic generation from included Pfyfile files.

## How It Works

### 1. Subcommands are Automatically Created

When you include a Pfyfile in your main configuration, pf automatically creates a subcommand:

```text
# In Pfyfile.pf
include Pfyfile.web-demo.pf
include Pfyfile.security.pf
include Pfyfile.lifting.pf
```

This automatically creates:
- `pf web-demo <task>` - Run tasks from Pfyfile.web-demo.pf
- `pf security <task>` - Run tasks from Pfyfile.security.pf
- `pf lifting <task>` - Run tasks from Pfyfile.lifting.pf

### 2. How to Use Them

```bash
# Using subcommands
pf web-demo build-all
pf security scan url=http://localhost:8080
pf lifting install-tools

# Or use tasks directly (both work!)
pf run web-build-all
pf web-build-all

# With parameters
pf web-demo dev port=3000
pf security scan url=http://localhost verbose=true
```

### 3. How They Mix with Displaying Files

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

### 4. Within Each Subcommand, Tasks are Grouped by Prefix

Tasks are further organized by common prefixes:

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

## Complete Documentation

See the comprehensive guide at **[docs/SUBCOMMANDS.md](docs/SUBCOMMANDS.md)** which covers:

- ✅ How subcommands work
- ✅ How to use them
- ✅ How to create your own subcommands
- ✅ How they mix with file display
- ✅ Best practices for organizing tasks
- ✅ Real-world examples
- ✅ Troubleshooting

## Summary

**Everything you asked for is already implemented and working!**

1. ✅ **Subcommands are supported** - Automatically generated from included Pfyfiles
2. ✅ **Grouping by subcommands** - Tasks are organized by source file
3. ✅ **Mixes with displaying files** - `pf list` shows tasks organized by subcommand AND by prefix
4. ✅ **Easy to use** - Just include a Pfyfile and the subcommand is created automatically

No additional implementation needed - just use the existing functionality and refer to the documentation!
