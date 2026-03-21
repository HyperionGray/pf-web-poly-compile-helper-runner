# Test Coverage Guide

**Last Updated:** 2026-01-05  
**Status:** Comprehensive test infrastructure in place

## Overview

This guide provides comprehensive information about the test coverage in the pf-web-poly-compile-helper-runner project, including how to run tests, add new tests, and interpret test results.

## Current Test Infrastructure

### Test Frameworks
- **Playwright** - E2E tests for web interfaces (Chromium, Firefox, WebKit)
- **pytest** - Python unit and integration tests  
- **Node.js** - Custom test runners for JavaScript/TypeScript
- **Shell scripts** - Integration tests for command-line tools

### Test Execution Modes
- **Headless** - Default mode for CI/CD
- **Headed** - Interactive mode with browser UI for debugging
- **Debug** - Step-through debugging with Playwright Inspector

## Running Tests

### Quick Start

```bash
# Run all Playwright E2E tests
npm test

# Run all unit tests
npm run test:unit

# Run complete test suite
npm run test:all

# Run Python tests
python3 -m pytest tests/

# Run specific test file
npx playwright test tests/e2e/ui-structure.spec.ts
```

### Test Commands Reference

#### Playwright Tests
```bash
npm test                      # Run E2E tests (headless)
npm run test:ui               # Run with Playwright UI (interactive)
npm run test:debug            # Run with debugger/inspector
```

#### Unit Tests by Category
```bash
npm run test:grammar          # Grammar validation
npm run test:parser           # Parser functionality
npm run test:polyglot         # Polyglot language support
npm run test:build-helpers    # Build system helpers
npm run test:containerization # Container orchestration
npm run test:api              # REST API endpoints
npm run test:tui              # Terminal UI tests
npm run test:sync             # Synchronization operations
```

#### Python Tests
```bash
# Run all Python tests
python3 -m pytest tests/

# Run with coverage
python3 -m pytest --cov=pf-runner-full tests/

# Run specific test file
python3 -m pytest tests/test_pf_tui.py

# Run with verbose output
python3 -m pytest -v tests/
```

#### Security Tests
```bash
npm run security:scan         # Scan for credentials
npm run security:deps         # Check dependency vulnerabilities
npm run security:headers      # Validate HTTP headers
npm run security:all          # Run all security tests
```

## Test Coverage Status

### Files With Test Coverage

#### Core Modules (Python)
- ✅ `pf-runner-full/pf_tui.py` - TUI functionality (tests/test_pf_tui.py)
- ✅ `pf-runner-full/pf_parser.py` - Parser functionality (tests/test_pf_parser.py)
- ✅ Grammar and parsing - Comprehensive grammar tests
- ✅ API functionality - API endpoint tests

#### Web Interface (TypeScript/Playwright)
- ✅ UI structure - ui-structure.spec.ts
- ✅ Error handling - error-handling.spec.ts
- ✅ Polyglot compilation - polyglot-plus-c.spec.ts
- ✅ Comprehensive UI - comprehensive-ui.spec.ts

#### Integration Tests
- ✅ Build helpers - 65+ tests
- ✅ Container management - 40+ tests
- ✅ Shell language support - 60+ tests
- ✅ Synchronization operations - 60+ tests

### Files Without Dedicated Tests

Many utility and demo files don't have dedicated test files but are covered by integration tests:

#### Demo/Utility Scripts
- `demos/screenshot_tui.py` - Demo script for TUI screenshots
- `demos/demo_tui.py` - Non-interactive TUI demonstration
- `demo_unified_api.py` - API demonstration script
- `simple_syntax_validator.py` - Syntax validation utility

#### Installation Scripts
- `pf-runner-full/setup.py` - Installation configuration (tested via CI)
- Installation validated through CI/CD pipeline

#### Tool Scripts
Many tool scripts in `tools/` are utilities that:
- Are tested through integration tests
- Are used in development/debugging workflows
- Don't require dedicated unit tests per project conventions

## Adding New Tests

### Adding Playwright Tests

1. Create a new test file in `tests/e2e/`:
```typescript
// tests/e2e/my-feature.spec.ts
import { test, expect } from '@playwright/test';

test.describe('My Feature', () => {
  test('feature works correctly', async ({ page }) => {
    await page.goto('http://localhost:8080');
    await expect(page.locator('selector')).toBeVisible();
  });
});
```

2. Run your test:
```bash
npx playwright test tests/e2e/my-feature.spec.ts
```

### Adding Python Tests

1. Create a test file in `tests/`:
```python
# tests/test_my_module.py
import pytest
from pf_runner import my_module

def test_functionality():
    result = my_module.my_function()
    assert result == expected_value
```

2. Run your test:
```bash
python3 -m pytest tests/test_my_module.py -v
```

### Adding Node.js Tests

1. Create a test file in appropriate category:
```javascript
// tests/category/my-test.mjs
import { describe, it, expect } from './test-framework.mjs';

describe('My Feature', () => {
  it('should work correctly', () => {
    expect(myFunction()).toBe(expectedValue);
  });
});
```

## Test Best Practices

### General Guidelines
1. **Test Naming**: Use descriptive names that explain what is being tested
2. **Test Isolation**: Each test should be independent
3. **Test Data**: Use fixtures and mock data appropriately
4. **Assertions**: Include clear, specific assertions
5. **Coverage**: Focus on critical paths and edge cases

### Playwright-Specific
1. **Selectors**: Use role-based selectors when possible
2. **Waits**: Use `await expect()` for automatic waiting
3. **Assertions**: Prefer Playwright assertions over generic ones
4. **Test Organization**: Group related tests with `test.describe()`

### Python-Specific
1. **Fixtures**: Use pytest fixtures for setup/teardown
2. **Mocking**: Use `unittest.mock` or `pytest-mock` for isolation
3. **Parametrization**: Use `@pytest.mark.parametrize` for multiple cases
4. **Coverage**: Aim for 80%+ coverage on critical modules

## CI/CD Integration

### GitHub Actions Workflow

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main`
- Scheduled daily runs at 2 AM UTC

### Test Matrix
- Python versions: 3.9, 3.10, 3.11
- Node.js versions: 16, 18, 20
- Browsers: Chromium, Firefox, WebKit

### CI Test Commands
```yaml
# Python tests with coverage
coverage run -m pytest tests/ --verbose
coverage report --show-missing

# Playwright tests
npx playwright install --with-deps
npm test

# Unit tests
npm run test:unit
```

## Test Reports

### Playwright Reports
- Location: `playwright-report/`
- Format: HTML with screenshots and traces
- Access: `npx playwright show-report`

### Python Coverage Reports
- Location: `htmlcov/`
- Format: HTML coverage report
- Coverage target: 80%

### Test Results
- CI artifacts retained for 30-90 days
- Test reports uploaded on workflow completion
- Available in Actions tab on GitHub

## Troubleshooting

### Common Issues

#### Playwright browser not installed
```bash
npx playwright install --with-deps
```

#### Python dependencies missing
```bash
pip install -r requirements.txt  # If available
# Or install individually:
pip install pytest pytest-cov pytest-playwright
```

#### Node.js dependencies missing
```bash
npm ci  # Clean install from package-lock.json
```

#### Tests timeout
- Increase timeout in playwright.config.ts
- Check if web server is running
- Verify network connectivity

### Debug Mode

```bash
# Playwright with inspector
npm run test:debug

# Python with verbose output
python3 -m pytest -vv tests/

# Node.js with detailed output
npm run test:unit:verbose
```

## Test Statistics

### Current Coverage
- **Total Tests**: 400+ test cases
- **Success Rate**: 100% (all tests passing)
- **E2E Tests**: 50+ Playwright tests
- **Unit Tests**: 350+ tests across categories
- **Python Coverage**: 80%+ on core modules

### Test Categories
| Category | Tests | Status |
|----------|-------|--------|
| Grammar | 80+ | ✅ Passing |
| Parser | 75+ | ✅ Passing |
| Polyglot | 60+ | ✅ Passing |
| Build Helpers | 65+ | ✅ Passing |
| Sync/Ops | 60+ | ✅ Passing |
| API | 40+ | ✅ Passing |
| E2E | 50+ | ✅ Passing |

## Future Improvements

### Planned Enhancements
1. **Visual Regression Testing** - Screenshot comparison for UI changes
2. **Performance Benchmarking** - Automated performance test suite
3. **Test Data Factories** - Better test data management
4. **Parallel Execution** - Optimize test parallelization

### Coverage Goals
- Maintain 80%+ Python code coverage
- Add tests for new features at time of implementation
- Regular test review and cleanup
- Performance benchmarking for critical paths

## Resources

### Documentation
- [Playwright Documentation](https://playwright.dev)
- [pytest Documentation](https://docs.pytest.org)
- [Test Coverage Summary](../../TESTING_SUMMARY.md)
- [Comprehensive Test README](../../tests/README-COMPREHENSIVE.md)

### Related Files
- `playwright.config.ts` - Playwright configuration
- `pytest.ini` - pytest configuration
- `package.json` - Test scripts
- `.github/workflows/ci.yml` - CI/CD pipeline

## Contact

For questions about testing:
- Review existing tests in `tests/` directory
- Check CI/CD logs in GitHub Actions
- Refer to test documentation in `docs/testing/`

---

**Note**: This project follows a pragmatic approach to test coverage. Not every utility script requires dedicated tests - many are covered through integration tests or are validated through CI/CD workflows. The focus is on testing critical functionality and user-facing features.
