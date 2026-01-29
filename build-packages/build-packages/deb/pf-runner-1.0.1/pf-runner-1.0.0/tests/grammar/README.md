# Grammar Unit Tests for pf

Comprehensive unit tests that verify the pf task runner grammar as documented in `pf.lark` and the docs.

## Running Tests

```bash
# Run all grammar tests
./tests/grammar/run_all_grammar_tests.sh

# Run individual test suites
./tests/grammar/test_grammar.sh       # Core grammar features
./tests/grammar/test_polyglot.sh      # Polyglot language support
./tests/grammar/test_build_helpers.sh # Build system helpers
./tests/grammar/test_web_api.sh       # Web/WASM builds and REST API
./tests/grammar/test_debugging.sh     # Debugging and RE tools
```

## Test Coverage

### 1. Core Grammar (`test_grammar.sh`)

Tests fundamental grammar features:
- Task definitions (`task...end`)
- Task parameters with defaults
- Parameter passing formats (key=value, --key=value, --key value)
- Environment variables (`env`)
- Variable interpolation (`$var`, `${var}`)
- Shell commands
- Comments (`#`)
- Include mechanism
- Multiple task execution
- Task listing

### 2. Build System Helpers (`test_build_helpers.sh`)

Tests build system integration:
- `makefile` / `make` verb
- `cmake` verb
- `cargo` verb (Rust)
- `go_build` / `gobuild` verb
- `meson` / `ninja` verb
- `justfile` / `just` verb
- `autobuild` / `auto_build` verb
- `build_detect` / `detect_build` verb
- `configure` verb (Autotools)
- Build system detection priority

### 3. Polyglot Languages (`test_polyglot.sh`)

Tests language documentation and configuration:
- Documentation exists (LANGS.md, README)
- Shell languages documented (bash, sh, dash, zsh, fish, ksh, tcsh, pwsh)
- Scripting languages documented (python, node, perl, ruby, lua, php)
- Compiled languages documented (c, cpp, rust, go, fortran)
- LLVM IR variants documented (c-llvm, cpp-llvm, fortran-llvm)
- Language aliases documented
- Parser configuration (POLYGLOT_LANGS, POLYGLOT_ALIASES)

### 4. Web/API Features (`test_web_api.sh`)

Tests web development tasks:
- Web build tasks (web-build-rust, web-build-c, etc.)
- WASM target tasks
- LLVM target tasks
- asm.js target tasks
- Development server tasks
- REST API files and documentation
- Playwright test configuration
- Security testing tasks

### 5. Debugging/RE Features (`test_debugging.sh`)

Tests debugging and reverse engineering:
- Debugger installation tasks
- Debug example builds
- Interactive debugging tasks
- Disassembly and binary analysis
- Binary lifting tasks (RetDec, LLVM)
- Binary injection tasks
- ROP exploitation tasks
- pwntools integration
- ROPgadget integration
- TUI tasks
- Git cleanup tasks
- Documentation coverage

## Grammar Documentation vs Implementation

The `pf.lark` grammar file documents both implemented and planned features. The tests verify:

1. **Implemented features** - Tested by execution
2. **Documented features** - Verified in grammar/docs
3. **Planned features** - Noted in test comments

Features like `shell_lang` and `[lang:*]` inline tags are documented in the grammar but may require specific parser implementations. Tests note these cases and use bash-level equivalents where possible.

## Adding New Tests

When adding new grammar features:

1. Add tests to the appropriate test file
2. Use the `pass`/`fail`/`skip` helper functions
3. Add sections with `section "Name"`
4. Test both positive and negative cases
5. Document any limitations in comments

## Dependencies

- Bash
- Python 3 with Fabric library
- Various build tools (optional, tests skip if not available)

## Test Output

Tests produce colored output:
- ✓ PASS (green) - Test passed
- ✗ FAIL (red) - Test failed
- ○ SKIP (yellow) - Test skipped (missing dependency)

The runner produces a summary at the end showing total passed/failed/skipped counts.
