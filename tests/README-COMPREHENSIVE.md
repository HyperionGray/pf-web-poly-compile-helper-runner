# Comprehensive pf Language Test Suite

This directory contains systematic tests for all pf language features, ensuring complete grammar coverage, API functionality, compilation workflows, and debugging tool integration.

## Test Structure

- **grammar/** - Grammar rule validation tests
  - `grammar.test.mjs` - Comprehensive grammar syntax tests (80+ test cases)
  - `parser.test.mjs` - Variable interpolation and task parsing tests (75+ test cases)
  - `test-grammar.sh` - Shell-based grammar validation
- **shell-scripts/** - Shell language and polyglot tests
  - `polyglot.test.mjs` - All supported shell languages (60+ test cases)
  - `test-all-features.sh` - Feature validation scripts
  - `test-polyglot-languages.sh` - Language-specific tests
- **api/** - REST API and WebSocket tests
  - `api-server.test.mjs` - API endpoint tests (40+ test cases)
  - `test-rest-api.sh` - Shell-based API tests
- **compilation/** - Build system helper tests
  - `build-helpers.test.mjs` - Make, CMake, Cargo, Go, etc. (65+ test cases)
  - `test-all-targets.sh` - Compilation target validation
- **debugging/** - System operations tests
  - `sync-ops.test.mjs` - Sync, service, package operations (60+ test cases)
  - `test-debugging-workflows.sh` - Debugging workflow validation
- **tui/** - Terminal interface tests
  - `git-cleanup.test.mjs` - Git cleanup TUI tests
  - `run-all-tui-tests.mjs` - TUI test runner
- **e2e/** - End-to-end Playwright tests
  - `polyglot-plus-c.spec.ts` - WebAssembly demo tests
  - `error-handling.spec.ts` - Error handling tests
  - `ui-structure.spec.ts` - UI structure validation
  - `comprehensive-ui.spec.ts` - Comprehensive UI tests (50+ test cases)
- **performance/** - Performance benchmarks
- **error-handling/** - Edge cases and error conditions
- **docs-validation/** - Documentation alignment verification

## Running Tests

### Quick Start

```bash
# Run all unit tests
npm run test:unit

# Run with verbose output
npm run test:unit:verbose

# Run Playwright E2E tests
npm test

# Run all tests (E2E + TUI + Unit)
npm run test:all
```

### Individual Test Suites

```bash
# Grammar tests
npm run test:grammar

# Parser/variable interpolation tests
npm run test:parser

# Polyglot language tests
npm run test:polyglot

# Build system helper tests
npm run test:build-helpers

# Sync and operations tests
npm run test:sync

# API server tests
npm run test:api
```

### Shell-based Tests

```bash
# Run all shell-based tests
./run-all-tests.sh

# Run specific category
./grammar/test-grammar.sh
./shell-scripts/test-all-features.sh
./api/test-rest-api.sh
./compilation/test-all-targets.sh
./debugging/test-debugging-workflows.sh
```

## Test Coverage Summary

| Category | Tests | Description |
|----------|-------|-------------|
| Grammar | 80+ | Syntax validation for all grammar constructs |
| Parser | 75+ | Variable interpolation, task definition parsing |
| Polyglot | 60+ | Shell language support (bash, python, node, etc.) |
| Build Helpers | 65+ | Make, CMake, Meson, Cargo, Go, Just, etc. |
| Sync/Ops | 60+ | File sync, service management, package ops |
| API | 40+ | REST endpoints, WebSocket, error handling |
| E2E | 50+ | UI structure, responsiveness, interactions |
| **Total** | **430+** | Comprehensive coverage |

## Test Coverage Goals

- ✅ 100% grammar rule coverage
- ✅ All documented features tested
- ✅ All API endpoints validated
- ✅ All compilation targets verified
- ✅ All build system helpers covered
- ✅ All shell languages supported
- ✅ Complete error condition handling
- ✅ Documentation-implementation alignment

## Test Categories

### 1. Grammar Tests
Tests every grammar construct defined in `pf-runner/pf.lark`:
- Task definitions with parameters
- Environment variables (global and task-local)
- Shell language specifications
- Control flow (if/else, for loops)
- Variable interpolation
- Build system helpers
- System operations (packages, services, sync)

### 2. Parser Tests
Tests the parsing logic in `pf_parser.py`:
- Task name parsing
- Parameter parsing (key=value pairs)
- Variable reference resolution
- Include statement handling
- Comment processing
- Whitespace handling

### 3. Polyglot Tests
Tests shell language support:
- Interpreted languages (bash, python, node, ruby, perl, php)
- Compiled languages (rust, c, cpp, go, fortran)
- JVM languages (java)
- Modern languages (deno, typescript, julia, elixir)
- Alternative shells (sh, dash, zsh, fish, pwsh)
- Language aliases

### 4. Build Helper Tests
Tests build system integrations:
- Makefile/Make (targets, variables, parallel builds)
- CMake (configuration, build types, generators)
- Meson/Ninja (setup, compile, options)
- Cargo (build, test, clippy, fmt)
- Go (build, test, cross-compilation)
- Configure (autotools options)
- Just (recipes, arguments)
- Autobuild (auto-detection)

### 5. System Operations Tests
Tests sync and system management:
- File sync (local, SSH, excludes, options)
- Package management (install, remove)
- Service management (start, stop, enable, restart)
- Directory creation
- File copy with permissions

### 6. API Tests
Tests REST API endpoints:
- Health checks
- System information
- Build triggers
- Status queries
- Error handling
- CORS configuration

### 7. E2E Tests
Tests the web interface:
- Page structure and content
- Button interactions
- Module loading status
- Responsive design
- Accessibility
- Error handling

## Dependencies

### Node.js Tests
- Node.js 18+
- @playwright/test (E2E tests)

### Python Tests  
- Python 3.8+
- fabric >= 3.2

### Shell Tests
- Bash 4+
- curl, jq (API tests)

## Contributing

When adding new features to pf:
1. Add grammar tests for new syntax
2. Add parser tests for parsing logic
3. Add polyglot tests for new languages
4. Add build helper tests for new systems
5. Update this README with test counts