# CI/CD Review System

This directory contains the automated CI/CD review system that generates comprehensive review reports covering code cleanliness, test coverage, documentation analysis, and build verification.

## Components

### Core Analysis Scripts

- **`file-analyzer.mjs`** - Analyzes repository files for size, categorization, and cleanliness
- **`documentation-validator.mjs`** - Validates documentation completeness and quality
- **`test-coverage-aggregator.mjs`** - Aggregates test results from Playwright and unit tests
- **`build-status-collector.mjs`** - Validates build functionality and reports status
- **`ci-cd-review-orchestrator.mjs`** - Main orchestrator that coordinates all components

## Usage

### Individual Components

Run individual analysis components:

```bash
# File analysis
npm run cicd:file-analysis
npm run cicd:file-analysis:report

# Documentation validation
npm run cicd:docs-validation
npm run cicd:docs-validation:report

# Test coverage aggregation
npm run cicd:test-coverage
npm run cicd:test-coverage:report

# Build status collection
npm run cicd:build-status
npm run cicd:build-status:report
```

### Complete Review

Run the complete CI/CD review:

```bash
# Generate and display review report
npm run cicd:review

# Generate and save review report to file
npm run cicd:review:save

# Generate JSON output for programmatic use
npm run cicd:review:json
```

### GitHub Actions Integration

The CI/CD review system is automatically triggered by the GitHub Actions workflow:

- **Trigger**: Push to main branch, pull requests, or manual dispatch
- **Workflow File**: `.github/workflows/cicd-review.yml`
- **Artifacts**: Review reports and test results are uploaded as artifacts
- **Issues**: Automatic issue creation/update with review results on main branch pushes
- **PR Comments**: Summary comments on pull requests

## Output Format

The system generates review reports in the following format:

```markdown
# Complete CI/CD Agent Review Report

**Review Date:** [UTC timestamp]
**Repository:** P4X-ng/pf-web-poly-compile-helper-runner
**Branch:** main
**Trigger:** push

## Executive Summary
[Component status checkmarks]

## Detailed Findings

## Build Status
[Build verification results]

## Code Cleanliness Analysis
[File size analysis and recommendations]

## Documentation Analysis
[Documentation completeness check]

## Test Coverage and Playwright Integration
[Test results and coverage statistics]

## Next Steps - Amazon Q Review
[Integration points for Amazon Q]

## Action Items Summary
[Prioritized action items]
```

## Configuration

### File Analysis Configuration

- **Large File Threshold**: 500 lines (configurable in `file-analyzer.mjs`)
- **Excluded Patterns**: node_modules, .git, build artifacts, binary files
- **Categories**: auto-generated, core-component, test, documentation, configuration, build-deployment, source-code

### Documentation Requirements

- **Root Documentation**: README.md, QUICKSTART.md, LICENSE.md, LICENSE
- **Docs Structure**: docs/CHANGELOG.md, docs/development/CONTRIBUTING.md, docs/development/CODE_OF_CONDUCT.md, docs/security/SECURITY.md, docs/installation/INSTALL.md
- **README Sections**: Installation, Usage, Features, Contributing, License, Documentation, Examples, API

### Test Coverage

- **Test Types**: Playwright E2E, Unit tests, TUI tests, Grammar tests, API tests
- **File Patterns**: *.spec.ts, *.spec.js, *.test.mjs, *.test.js
- **Timeout**: 30 seconds per test suite

### Build Validation

- **Required Steps**: Node.js environment check, NPM dependencies installation, build validation
- **Environment**: Node.js, NPM, package.json validation
- **Timeout**: 60 seconds per build step

## Error Handling

The system includes comprehensive error handling:

- **Component Failures**: Individual component failures don't stop the overall review
- **Timeouts**: Configurable timeouts for long-running operations
- **Graceful Degradation**: Partial results are reported even if some components fail
- **Detailed Logging**: Comprehensive logging for debugging and monitoring

## Extending the System

### Adding New Analysis Components

1. Create a new analysis script in this directory
2. Implement the required interface methods:
   - Main analysis function
   - Report generation
   - CI/CD formatting
   - Error handling
3. Add the component to the orchestrator
4. Update package.json scripts
5. Update this documentation

### Customizing Report Format

The report format can be customized by modifying the `formatReviewReport` method in `ci-cd-review-orchestrator.mjs`.

### Integration with External Systems

The system provides JSON output for integration with external systems:

```bash
npm run cicd:review:json > review-results.json
```

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure scripts have execute permissions
2. **Missing Dependencies**: Run `npm install` to install required packages
3. **Timeout Issues**: Increase timeout values in individual components
4. **File Access Errors**: Check file permissions and paths

### Debug Mode

Enable verbose logging by setting environment variables:

```bash
DEBUG=1 npm run cicd:review
```

### Manual Testing

Test individual components manually:

```bash
node scripts/ci-cd-review/file-analyzer.mjs --json
node scripts/ci-cd-review/documentation-validator.mjs --cicd
node scripts/ci-cd-review/test-coverage-aggregator.mjs
node scripts/ci-cd-review/build-status-collector.mjs --cicd
```

## Performance Considerations

- **File Scanning**: Large repositories may take longer to scan
- **Test Execution**: Test suites run with timeouts to prevent hanging
- **Parallel Execution**: Components run sequentially to avoid resource conflicts
- **Caching**: Consider implementing caching for repeated runs

## Security Considerations

- **No Sensitive Data**: The system doesn't expose sensitive information in reports
- **File Access**: Only reads files, doesn't modify repository contents
- **Network Access**: Limited to local operations and npm registry
- **Permissions**: Runs with minimal required permissions