# Comprehensive pf Language Test Suite

This directory contains systematic tests for all pf language features, ensuring complete grammar coverage, API functionality, compilation workflows, and debugging tool integration.

## Test Structure

- **grammar/** - Grammar rule validation tests
- **shell-scripts/** - Bash scripts exercising all DSL features  
- **api/** - REST API and WebSocket tests
- **compilation/** - WASM, LLVM, asm.js build tests
- **debugging/** - Debugging tool integration tests
- **tui/** - Terminal interface tests (existing)
- **integration/** - End-to-end workflow tests
- **performance/** - Large-scale parsing and execution benchmarks
- **error-handling/** - Edge cases and error condition tests
- **docs-validation/** - Documentation alignment verification

## Usage

```bash
# Run all tests
./run-all-tests.sh

# Run specific test category
./grammar/test-grammar.sh
./shell-scripts/test-all-features.sh
./api/test-rest-api.sh
./compilation/test-all-targets.sh
./debugging/test-debugging-workflows.sh

# Run performance benchmarks
./performance/benchmark-parser.sh

# Validate documentation alignment
./docs-validation/validate-docs.sh
```

## Test Coverage Goals

- 100% grammar rule coverage
- All documented features tested
- All API endpoints validated
- All compilation targets verified
- All debugging workflows operational
- Complete error condition handling
- Documentation-implementation alignment

## Dependencies

See individual test directories for specific requirements.