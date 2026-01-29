# pf-runner Addon System

The addon system provides a clean, extensible interface for adding features to the pf-runner DSL that don't fit naturally into the core grammar.

## Overview

### What is an Addon?

An addon is a self-contained module that:
- Implements the `AddonInterface`
- Can handle specific operations
- Executes those operations in context
- Validates inputs before execution

### When to Use Addons

Use addons for features that:
- Have complex, dynamic behavior
- Support many variations (e.g., 20+ languages)
- Require external dependencies
- Need plugin-like extensibility
- Don't fit cleanly into grammar rules

### What Goes in Grammar vs Addons?

**Grammar** (pf.lark):
- Simple, declarative statements
- Fixed set of operations
- Direct mapping to commands
- Examples: `shell`, `cargo`, `cmake`

**Addons** (addon/):
- Complex, algorithmic features
- Dynamic code generation
- Extensible functionality
- Examples: polyglot languages, custom builders

## Architecture

```
┌─────────────────────────────────────────┐
│           AddonRegistry                  │
│  Central registry for all addons         │
│  - register(addon)                       │
│  - find_handler(operation, args)         │
│  - get(name)                             │
└─────────────────────────────────────────┘
                    │
                    ▼
     ┌──────────────────────────────┐
     │      AddonInterface           │
     │  Abstract base class          │
     │  - name: str                  │
     │  - version: str               │
     │  - can_handle(op, args)       │
     │  - execute(op, args, ctx)     │
     │  - validate(op, args)         │
     └──────────────────────────────┘
                    │
        ┌───────────┴────────────┬─────────────┐
        ▼                        ▼             ▼
┌──────────────────┐    ┌──────────────┐   ┌──────────┐
│ PolyglotAddon    │    │ (Future)     │   │ (Future) │
│ - 20+ languages  │    │ BuildAddon   │   │ Custom   │
│ - Code execution │    │ - Patterns   │   │ Addons   │
└──────────────────┘    └──────────────┘   └──────────┘
```

## Creating an Addon

### Step 1: Implement AddonInterface

```python
from addon import AddonInterface
from typing import Any, Dict

class MyAddon(AddonInterface):
    @property
    def name(self) -> str:
        return "my-addon"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def can_handle(self, operation: str, args: Dict[str, Any]) -> bool:
        """Check if this addon can handle the operation."""
        return operation == "my_operation"
    
    def execute(self, operation: str, args: Dict[str, Any], 
                context: Dict[str, Any]) -> Any:
        """Execute the operation."""
        # Your implementation here
        return result
    
    def validate(self, operation: str, args: Dict[str, Any]) -> str | None:
        """Validate arguments. Return None if valid, error message if not."""
        if 'required_arg' not in args:
            return "Missing required argument: required_arg"
        return None
```

### Step 2: Register the Addon

```python
from addon import AddonRegistry

# Create registry
registry = AddonRegistry()

# Register your addon
addon = MyAddon()
registry.register(addon)
```

### Step 3: Use the Addon

```python
# Find handler for operation
addon = registry.find_handler('my_operation', {'arg': 'value'})

if addon:
    # Validate first
    error = addon.validate('my_operation', {'arg': 'value'})
    if error:
        print(f"Validation failed: {error}")
    else:
        # Execute
        result = addon.execute('my_operation', 
                               {'arg': 'value'}, 
                               context={'env': 'prod'})
```

## Available Addons

### PolyglotAddon

Handles code execution in multiple programming languages.

**Languages Supported**: Python, JavaScript, Node, TypeScript, Rust, Go, C, C++, Java, Ruby, PHP, Perl, Bash, and many more.

**Example**:
```python
from addon.polyglot import PolyglotAddon

addon = PolyglotAddon()

# Execute Python code
command = addon.execute('polyglot_shell', {
    'lang': 'python',
    'code': 'print("Hello from Python!")',
    'args': []
}, context={})

# Execute Rust code
command = addon.execute('polyglot_shell', {
    'lang': 'rust',
    'code': 'fn main() { println!("Hello from Rust!"); }',
    'args': []
}, context={})
```

**Supported Operations**:
- `polyglot_shell` - Execute code in any supported language
- `shell` with `lang` parameter - Alternative syntax

**Validation**:
- Checks if language is supported
- Validates code is provided
- Returns helpful error messages

## Best Practices

### Addon Design

1. **Single Responsibility**: Each addon should handle one specific domain
2. **Clear Naming**: Use descriptive names (e.g., `PolyglotAddon`, `BuildSystemAddon`)
3. **Version Control**: Always specify version for compatibility
4. **Validation**: Validate inputs before execution
5. **Documentation**: Document supported operations and arguments

### Error Handling

```python
def execute(self, operation, args, context):
    try:
        # Your logic here
        return result
    except Exception as e:
        # Log error
        print(f"Addon error: {e}")
        # Re-raise or return error indication
        raise
```

### Testing

```python
def test_addon():
    addon = MyAddon()
    
    # Test can_handle
    assert addon.can_handle('my_op', {}) == True
    assert addon.can_handle('other_op', {}) == False
    
    # Test validation
    assert addon.validate('my_op', {}) == "Missing arg"
    assert addon.validate('my_op', {'arg': 'val'}) is None
    
    # Test execution
    result = addon.execute('my_op', {'arg': 'val'}, {})
    assert result == expected
```

## Examples

### Example 1: Build System Addon

```python
class BuildSystemAddon(AddonInterface):
    """Addon for intelligent build system detection and execution."""
    
    @property
    def name(self) -> str:
        return "build-system"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def can_handle(self, operation: str, args: Dict[str, Any]) -> bool:
        return operation == "auto_build"
    
    def execute(self, operation: str, args: Dict[str, Any], 
                context: Dict[str, Any]) -> str:
        """Detect build system and generate build command."""
        # Check for Cargo.toml
        if os.path.exists('Cargo.toml'):
            return "cargo build"
        
        # Check for CMakeLists.txt
        if os.path.exists('CMakeLists.txt'):
            return "cmake -B build && cmake --build build"
        
        # Check for Makefile
        if os.path.exists('Makefile'):
            return "make"
        
        raise ValueError("No build system detected")
```

### Example 2: Package Manager Addon

```python
class PackageManagerAddon(AddonInterface):
    """Addon for cross-platform package management."""
    
    @property
    def name(self) -> str:
        return "package-manager"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def can_handle(self, operation: str, args: Dict[str, Any]) -> bool:
        return operation in ["install_packages", "remove_packages"]
    
    def execute(self, operation: str, args: Dict[str, Any], 
                context: Dict[str, Any]) -> str:
        """Generate package manager command based on OS."""
        packages = args.get('packages', [])
        
        if sys.platform.startswith('linux'):
            if operation == "install_packages":
                return f"apt-get install {' '.join(packages)}"
            else:
                return f"apt-get remove {' '.join(packages)}"
        
        elif sys.platform == 'darwin':
            if operation == "install_packages":
                return f"brew install {' '.join(packages)}"
            else:
                return f"brew uninstall {' '.join(packages)}"
        
        raise ValueError(f"Unsupported platform: {sys.platform}")
```

## Future Addons

Ideas for future addons:

1. **CloudAddon** - AWS, GCP, Azure operations
2. **ContainerAddon** - Docker, Podman commands
3. **TestingAddon** - Framework-specific test runners
4. **LintingAddon** - Multi-language linting
5. **DocumentationAddon** - Doc generation
6. **SecurityAddon** - Security scanning
7. **DatabaseAddon** - DB migrations and operations
8. **APIAddon** - REST API testing and deployment

## Contributing

To contribute a new addon:

1. Implement `AddonInterface`
2. Add comprehensive tests
3. Document operations and arguments
4. Add examples to this README
5. Submit PR

## API Reference

### AddonInterface

Base class for all addons.

**Properties**:
- `name: str` - Unique addon identifier
- `version: str` - Semantic version (e.g., "1.0.0")

**Methods**:
- `can_handle(operation, args) -> bool` - Check if addon handles operation
- `execute(operation, args, context) -> Any` - Execute the operation
- `validate(operation, args) -> str|None` - Validate arguments

### AddonRegistry

Central registry for addon management.

**Methods**:
- `register(addon: AddonInterface)` - Register an addon
- `unregister(name: str)` - Remove an addon
- `get(name: str) -> AddonInterface|None` - Get addon by name
- `find_handler(operation, args) -> AddonInterface|None` - Find handler
- `list_addons() -> List[AddonInterface]` - List all addons

## License

Same as pf-runner project.

## See Also

- [Grammar Migration Guide](../GRAMMAR_MIGRATION.md)
- [Implementation Summary](../IMPLEMENTATION_SUMMARY.md)
- [Polyglot Addon](./polyglot.py)
- [Addon Interface](./interface.py)
