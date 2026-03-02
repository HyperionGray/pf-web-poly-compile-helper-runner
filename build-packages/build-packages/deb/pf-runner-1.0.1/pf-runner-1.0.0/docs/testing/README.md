# Testing Documentation

This directory contains comprehensive documentation about testing in the pf-web-poly-compile-helper-runner project.

## Documentation Files

- **[TEST_COVERAGE_GUIDE.md](TEST_COVERAGE_GUIDE.md)** - Complete guide to test coverage, running tests, and adding new tests
  - Test infrastructure overview
  - Commands for running tests
  - Coverage status and statistics
  - Best practices for writing tests
  - CI/CD integration details
  - Troubleshooting guide

## Quick Links

### Running Tests
```bash
# All tests
npm run test:all

# E2E tests only
npm test

# Python tests
python3 -m pytest tests/

# Unit tests
npm run test:unit
```

### Test Documentation
- [Comprehensive Test README](../../tests/README-COMPREHENSIVE.md) - Test structure overview
- [Testing Summary](../../TESTING_SUMMARY.md) - Test execution results
- [Quick Reference Testing](../../QUICK_REFERENCE_TESTING.md) - Installation file testing

### Configuration
- [playwright.config.ts](../../playwright.config.ts) - Playwright E2E test configuration
- [pytest.ini](../../pytest.ini) - Python test configuration
- [package.json](../../package.json) - Test scripts

### CI/CD
- [CI/CD Pipeline](.github/workflows/ci.yml) - GitHub Actions workflow

## Test Categories

### End-to-End (E2E) Tests
Location: `tests/e2e/`  
Framework: Playwright  
Browsers: Chromium, Firefox, WebKit

### Unit Tests
Location: `tests/` (various subdirectories)  
Framework: Custom Node.js runners  
Categories: Grammar, Parser, API, Build Helpers, etc.

### Python Tests
Location: `tests/`  
Framework: pytest  
Coverage: Core modules (pf_tui, pf_parser, etc.)

### Integration Tests
Location: Various test directories  
Scope: Containerization, OS switching, package management

## Getting Started

1. **Install dependencies**:
   ```bash
   npm ci
   pip install pytest pytest-cov
   ```

2. **Install Playwright browsers**:
   ```bash
   npx playwright install --with-deps
   ```

3. **Run tests**:
   ```bash
   npm run test:all
   ```

## Contributing

When adding new features:
1. Write tests for new functionality
2. Ensure existing tests still pass
3. Maintain 80%+ code coverage for critical modules
4. Follow test best practices outlined in the guide

## Support

For questions about testing:
- Review the [Test Coverage Guide](TEST_COVERAGE_GUIDE.md)
- Check existing tests in `tests/` directory
- Review CI/CD logs in GitHub Actions
