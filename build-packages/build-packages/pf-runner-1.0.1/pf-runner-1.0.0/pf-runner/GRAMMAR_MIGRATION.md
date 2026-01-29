# Grammar Migration Guide

This document explains the migration from string-based parsing to Lark grammar-based parsing.

## Overview

The pf-runner DSL has been migrated to use a robust, grammar-based parser built with Lark.
This provides:

- **Robust parsing** with proper error messages
- **Abstract Syntax Tree (AST)** for better code analysis
- **Extensibility** through the addon system
- **Maintainability** with formal grammar definition

## Architecture

### Core Components

1. **pf.lark** - Formal grammar definition
   - Defines all DSL syntax rules
   - Covers core verbs: shell, describe, env, if/else, for loops
   - Includes build system helpers: makefile, cmake, cargo, etc.

2. **pf_lark_parser.py** - Grammar-based parser
   - Uses Lark to parse `.pf` files
   - Transforms AST into runtime data structures
   - Replaces string-based parsing in `pf_parser.py`

3. **addon/** - Extension system
   - `interface.py` - Base interface for addons
   - `polyglot.py` - Polyglot language support addon
   - Clean separation of concerns

### Grammar Structure

The grammar is organized hierarchically:

```
start
├── statement (top-level)
│   ├── env_var (global environment)
│   ├── task (task definition)
│   └── comment
│
task
├── IDENTIFIER (task name)
├── param* (parameters)
├── NEWLINE
├── task_body+ (task statements)
│   ├── describe
│   ├── shell
│   ├── env_stmt
│   ├── if_stmt / else
│   ├── for_loop
│   ├── sync_stmt
│   ├── packages_stmt
│   ├── service_stmt
│   ├── directory_stmt
│   ├── copy_stmt
│   └── build system helpers
└── end
```

## Addon System

### Purpose

The addon system handles features that don't fit naturally into the grammar:

- **Polyglot language support** - Too many languages to hardcode in grammar
- **Dynamic code generation** - Templating and code synthesis
- **External tool integration** - Plugin-like extensions

### Interface

All addons implement the `AddonInterface`:

```python
class AddonInterface(ABC):
    @property
    def name(self) -> str: ...
    
    @property
    def version(self) -> str: ...
    
    def can_handle(self, operation: str, args: Dict[str, Any]) -> bool: ...
    
    def execute(self, operation: str, args: Dict[str, Any], 
                context: Dict[str, Any]) -> Any: ...
    
    def validate(self, operation: str, args: Dict[str, Any]) 
                -> Optional[str]: ...
```

### Example: Polyglot Addon

The polyglot addon handles code execution in multiple languages:

```python
from addon import AddonRegistry
from addon.polyglot import PolyglotAddon

# Register addon
registry = AddonRegistry()
registry.register(PolyglotAddon())

# Use addon
addon = registry.find_handler('polyglot_shell', 
                               {'lang': 'python', 'code': 'print("hello")'})
result = addon.execute('polyglot_shell', args, context)
```

## Migration Path

### Phase 1: Grammar Expansion ✅
- [x] Expand pf.lark to include all DSL verbs
- [x] Add build system helper statements
- [x] Document grammar structure

### Phase 2: Addon System ✅
- [x] Create addon/ directory structure
- [x] Define AddonInterface
- [x] Implement AddonRegistry
- [x] Create polyglot addon example

### Phase 3: Lark Parser ✅
- [x] Implement PfLarkParser
- [x] Create PfTransformer for AST conversion
- [x] Parse into runtime data structures

### Phase 4: Integration (IN PROGRESS)
- [ ] Integrate Lark parser into pf_parser.py
- [ ] Maintain backward compatibility
- [ ] Add fallback to old parser if needed
- [ ] Update tests

### Phase 5: Cleanup
- [ ] Remove old string-based parsing code
- [ ] Update documentation
- [ ] Performance benchmarks
- [ ] Migration complete

## Usage Examples

### Basic Task Parsing

```python
from pf_lark_parser import parse_pf

pf_code = """
task hello param1="value1"
  describe Say hello
  shell echo "Hello, $param1!"
end
"""

tasks = parse_pf(pf_code)
# tasks = {'hello': {'name': 'hello', 'params': {'param1': 'value1'}, ...}}
```

### With Addon System

```python
from addon import AddonRegistry
from addon.polyglot import PolyglotAddon

# Setup
registry = AddonRegistry()
registry.register(PolyglotAddon())

# Execute polyglot code
addon = registry.get('polyglot')
command = addon.execute('polyglot_shell', {
    'lang': 'python',
    'code': 'print("Hello from Python!")',
    'args': []
}, context={})
```

## Benefits

### Robustness
- **Formal grammar** - No ambiguity in language definition
- **Error reporting** - Lark provides precise error locations
- **Validation** - Grammar enforces syntax rules automatically

### Extensibility
- **Addon system** - Easy to add new features
- **Clean interface** - Well-defined extension points
- **Plugin architecture** - Third-party extensions possible

### Maintainability
- **Separation of concerns** - Grammar, parser, and runtime separated
- **Documentation** - Grammar serves as formal specification
- **Testing** - Easy to test grammar rules independently

## Development

### Adding New Grammar Rules

1. Edit `pf.lark` to add new statement type
2. Add case to `PfTransformer` to handle new node
3. Update documentation
4. Add tests

### Creating New Addons

1. Implement `AddonInterface`
2. Register with `AddonRegistry`
3. Document addon capabilities
4. Add tests

## Testing

```bash
# Test grammar parsing
python3 -c "from pf_lark_parser import parse_pf; parse_pf('task test\\nshell echo hi\\nend')"

# Test addon
python3 -c "from addon.polyglot import PolyglotAddon; a=PolyglotAddon(); print(a.name)"
```

## Backward Compatibility

The migration maintains full backward compatibility:

- All existing `.pf` files will continue to work
- No changes required to existing tasks
- Gradual transition from old to new parser
- Fallback mechanism if grammar parsing fails

## Performance

- **Grammar compilation** - One-time cost at startup
- **AST generation** - Minimal overhead vs. string parsing
- **Caching** - Parsed trees can be cached for repeated use

## Future Enhancements

- **LSP support** - Language server for IDE integration
- **Syntax highlighting** - Editor integration via grammar
- **Auto-completion** - Based on grammar rules
- **Static analysis** - Lint and validate `.pf` files
- **Format/prettify** - Automatic code formatting

## References

- [Lark Documentation](https://lark-parser.readthedocs.io/)
- [pf.lark Grammar File](./pf.lark)
- [Addon Interface](./addon/interface.py)
- [Polyglot Addon](./addon/polyglot.py)
