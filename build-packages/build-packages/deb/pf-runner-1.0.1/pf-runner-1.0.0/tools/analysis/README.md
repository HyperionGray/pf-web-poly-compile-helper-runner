# Code Analyzer Tool

A comprehensive static code analysis tool that performs GPT-5 style code analysis across multiple dimensions.

## Features

- **Security Analysis**: Detects common vulnerabilities including:
  - Hardcoded secrets and credentials
  - Dependency vulnerabilities
  - Dangerous function usage (eval, exec, pickle)
  - Command injection risks (shell=True, subprocess)
  - XSS vulnerabilities (innerHTML)
  - With CVE/CWE references

- **Performance Optimization**: Identifies opportunities for:
  - List comprehension usage in Python
  - Async/await patterns in JavaScript
  - Efficient string operations
  - Array method optimization

- **Architecture Quality**: Evaluates:
  - Single Responsibility Principle violations
  - High coupling detection
  - Large file identification
  - Code organization

- **Test Coverage**: Analyzes:
  - Test-to-source file ratios
  - Test framework configuration
  - Testing best practices

- **Documentation Quality**: Checks for:
  - README and contributing guides
  - Documentation directory structure
  - Docstring/JSDoc coverage

## Usage

### Command Line

```bash
# Analyze current directory
node tools/analysis/code-analyzer.mjs .

# Analyze specific directory
node tools/analysis/code-analyzer.mjs /path/to/project

# Save report to file
node tools/analysis/code-analyzer.mjs . --output report.md

# Verbose output
node tools/analysis/code-analyzer.mjs . --verbose
```

### Programmatic Usage

```javascript
import CodeAnalyzer from './tools/analysis/code-analyzer.mjs';

const analyzer = new CodeAnalyzer({
  rootDir: process.cwd(),
  verbose: false
});

// Run full analysis
const results = await analyzer.runAnalysis();

// Generate markdown report
const report = analyzer.generateReport();
console.log(report);

// Access specific results
console.log('Security findings:', results.security);
console.log('Performance findings:', results.performance);
console.log('Architecture findings:', results.architecture);
```

## Integration with GitHub Actions

The analyzer is integrated with the `auto-gpt5-implementation.yml` workflow:

```yaml
- name: Run Comprehensive Code Analysis
  run: |
    node tools/analysis/code-analyzer.mjs . --output /tmp/gpt5-analysis.md --verbose
```

The workflow automatically:
1. Runs comprehensive analysis on push/PR
2. Generates detailed reports
3. Creates GitHub issues with findings
4. Updates existing issues with new analysis

## Output Format

The analyzer generates a comprehensive markdown report with:

- Repository statistics (file counts, lines of code)
- Security findings with severity levels
- Performance optimization opportunities
- Architecture recommendations
- Test coverage analysis
- Documentation quality assessment
- Actionable checklist

## Exit Codes

- `0`: Success (no critical issues found)
- `1`: Critical or high-severity security issues found

## Testing

Run the test suite:

```bash
node tests/code-analyzer.test.mjs
```

## Supported Languages

- Python (.py)
- JavaScript (.js, .mjs)
- TypeScript (.ts)
- Go (.go)
- Rust (.rs)
- C/C++ (.c, .cpp)

## Requirements

- Node.js 18+
- Access to repository files
- Optional: Security tools (credential-scanner, dependency-checker)

## Limitations

- Performs static analysis only
- Does not execute code
- May produce false positives
- Limited to pattern-based detection
- Best used as part of comprehensive review process

## Future Enhancements

- Integration with additional security scanners
- Machine learning-based anomaly detection
- Custom rule configuration
- Multi-language support expansion
- IDE integration
