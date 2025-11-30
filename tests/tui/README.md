# TUI Testing Framework

A comprehensive testing framework for Terminal User Interface (TUI) applications in the pf-web-poly-compile-helper-runner project.

## Overview

This framework provides automated testing capabilities for TUI applications, allowing developers to test terminal-based tools without manual interaction. It supports mocking of system dependencies, simulation of user input, and validation of terminal output.

## Quick Start

### Running TUI Tests

```bash
# Run all TUI tests
npm run test:tui

# Run only git-cleanup tests
npm run test:tui-only

# Run all tests (web + TUI)
npm run test:all

# Run integration test
node tests/tui/integration-test.mjs
```

### Basic Test Structure

```javascript
import { TUITestFramework } from './framework/tui-test-framework.mjs';

const myTests = TUITestFramework.createTestSuite('My TUI Tool', [
  {
    name: 'Basic functionality test',
    async run(framework) {
      // Setup mocks
      framework.setupGitMocks();
      
      // Add user interactions
      framework.addSelection('Option 1');
      framework.addConfirmation(true);
      
      // Run the test
      const result = await framework.runTUITest('node', ['my-tool.mjs']);
      
      // Validate results
      framework.assertExitCode(result, 0);
      framework.assertOutputContains(result, 'Expected output');
    }
  }
]);

// Run the test suite
myTests.run();
```

## Framework Components

### 1. TUITestFramework Class

The core testing framework that provides:

- **Mock System**: Mock external dependencies (git, file system, etc.)
- **User Interaction Simulation**: Automate user input for prompts
- **Output Capture**: Capture and validate terminal output
- **Assertion Methods**: Validate test results
- **Test Suite Management**: Organize and run multiple tests

### 2. Mock System

#### Git Command Mocking

```javascript
// Setup common git mocks
framework.setupGitMocks();

// Custom git command mocking
framework.mockCommand('git status', ['On branch main']);
framework.mockCommand('git log --oneline', ['abc123 Initial commit']);
```

#### File System Mocking

```javascript
// Mock file operations in your tool
const mockFs = {
  existsSync: (path) => path === 'expected-file.txt',
  writeFileSync: (path, content) => { /* mock implementation */ },
  readFileSync: (path) => 'mock file content'
};
```

### 3. User Interaction Simulation

#### Selection Prompts

```javascript
// Simulate selecting an option from a list
framework.addSelection('1 MB'); // Select by value
framework.addSelection(2);      // Select by index
```

#### Checkbox Prompts

```javascript
// Simulate checkbox selections
framework.addCheckboxSelection([0, 2]); // Select first and third items
framework.addCheckboxSelection([]);     // Select nothing
```

#### Confirmation Prompts

```javascript
// Simulate yes/no confirmations
framework.addConfirmation(true);  // Yes
framework.addConfirmation(false); // No
```

#### Text Input

```javascript
// Simulate text input
framework.addTextInput('custom value');
framework.addTextInput('500KB');
```

### 4. Validation Methods

#### Output Validation

```javascript
// Check if output contains specific text
framework.assertOutputContains(result, 'Expected text');

// Check if output matches a pattern
framework.assertOutputMatches(result, /Pattern.*regex/);

// Validate exit code
framework.assertExitCode(result, 0);

// Validate that prompts appeared
framework.assertPromptsAppeared(result, [
  'Select an option',
  'Are you sure?'
]);
```

## Creating Testable TUI Tools

### Dependency Injection Pattern

To make your TUI tool testable, use dependency injection:

```javascript
export class MyTUITool {
  constructor(dependencies = {}) {
    this.deps = {
      execSync: dependencies.execSync || execSync,
      fs: dependencies.fs || fs,
      prompts: {
        select: dependencies.select || select,
        confirm: dependencies.confirm || confirm
      },
      console: dependencies.console || console,
      process: dependencies.process || process,
      ...dependencies
    };
  }

  async run() {
    // Use this.deps instead of direct imports
    const result = this.deps.execSync('git status');
    const choice = await this.deps.prompts.select({
      message: 'Choose an option',
      choices: ['Option 1', 'Option 2']
    });
  }
}
```

### Test Mode Detection

```javascript
constructor(dependencies = {}) {
  this.isTestMode = process.env.TUI_TEST_MODE === 'true';
  this.testId = process.env.TUI_TEST_ID || '';
  
  // Adjust behavior for testing if needed
  if (this.isTestMode) {
    // Disable animations, reduce timeouts, etc.
  }
}
```

## Test Scenarios

### Comprehensive Test Coverage

The framework supports testing various scenarios:

#### 1. Happy Path Tests
- Normal user workflows
- Expected input/output patterns
- Successful completion scenarios

#### 2. Error Handling Tests
- Invalid input handling
- System command failures
- Permission errors
- Network failures

#### 3. Edge Case Tests
- Empty inputs
- Very large inputs
- Boundary conditions
- Unusual system states

#### 4. User Interaction Tests
- Cancellation at various stages
- Invalid selections
- Timeout scenarios
- Multiple interaction patterns

#### 5. Performance Tests
- Large dataset handling
- Memory usage validation
- Execution time limits
- Resource cleanup

## Example: Git Cleanup Tests

The git-cleanup tool demonstrates comprehensive TUI testing:

```javascript
// tests/tui/git-cleanup.test.mjs
const gitCleanupTests = TUITestFramework.createTestSuite('Git Cleanup TUI', [
  {
    name: 'Basic workflow - analyze and select files',
    async run(framework) {
      framework.setupGitMocks();
      framework.addSelection('1 MB');
      framework.addCheckboxSelection([0]);
      framework.addConfirmation(true);
      framework.addConfirmation(true);
      
      const result = await framework.runTUITest('node', [gitCleanupTool]);
      
      framework.assertExitCode(result, 0);
      framework.assertOutputContains(result, 'Git history successfully cleaned');
    }
  },
  // ... more tests
]);
```

## Best Practices

### 1. Test Organization

```javascript
// Group related tests in suites
const authTests = TUITestFramework.createTestSuite('Authentication', [...]);
const fileTests = TUITestFramework.createTestSuite('File Operations', [...]);
const errorTests = TUITestFramework.createTestSuite('Error Handling', [...]);
```

### 2. Mock Management

```javascript
// Setup common mocks in beforeEach equivalent
async run(framework) {
  // Common setup
  framework.setupGitMocks();
  framework.mockCommand('custom-command', ['expected output']);
  
  // Test-specific setup
  // ... test logic
}
```

### 3. Assertion Patterns

```javascript
// Use descriptive assertions
framework.assertOutputContains(result, 'Backup created successfully');
framework.assertOutputMatches(result, /\d+ files? processed/);

// Validate multiple aspects
framework.assertExitCode(result, 0);
framework.assertPromptsAppeared(result, ['Select files', 'Confirm']);
```

### 4. Error Testing

```javascript
// Test error scenarios explicitly
framework.mockCommand('git status', { error: 'Not a git repository' });
const result = await framework.runTUITest('node', [tool]);
framework.assertExitCode(result, 1);
framework.assertOutputContains(result, 'not a git repository');
```

## Extending the Framework

### Adding New Mock Types

```javascript
// In tui-test-framework.mjs
setupCustomMocks() {
  this.mockCommand('custom-tool --version', ['v1.0.0']);
  this.mockCommand('custom-tool --list', ['item1', 'item2']);
}
```

### Custom Assertion Methods

```javascript
// Add to TUITestFramework class
assertTableFormat(result, expectedColumns) {
  const output = result.stdout + result.stderr;
  expectedColumns.forEach(column => {
    if (!output.includes(column)) {
      throw new Error(`Expected table column "${column}" not found`);
    }
  });
}
```

### New Interaction Types

```javascript
// Add support for new prompt types
addCustomInteraction(type, value, delay = 100) {
  this.addInteraction('custom', { type, value }, delay);
}
```

## Troubleshooting

### Common Issues

#### 1. Tests Timeout
```javascript
// Increase timeout for slow operations
const framework = new TUITestFramework({ timeout: 60000 });
```

#### 2. Mock Not Working
```javascript
// Ensure mock is set up before test execution
framework.mockCommand('exact-command-string', ['response']);
```

#### 3. Output Not Captured
```javascript
// Check that output is being written to stdout/stderr
// Use console.error for debugging in tests
```

#### 4. Interaction Not Triggered
```javascript
// Verify prompt patterns match expected output
framework.shouldSendInteraction(output, interaction);
```

### Debugging Tests

```javascript
// Enable debug output
const framework = new TUITestFramework({ 
  captureOutput: true,
  debug: true 
});

// Log captured output
console.log('Captured output:', result.output);
```

## Performance Considerations

### Memory Management

```javascript
// Always cleanup after tests
framework.cleanup();

// Use appropriate timeouts
const framework = new TUITestFramework({ timeout: 30000 });
```

### Test Isolation

```javascript
// Each test gets a fresh framework instance
const framework = new TUITestFramework();
// ... run test
framework.cleanup();
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: TUI Tests
on: [push, pull_request]
jobs:
  tui-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
      - run: npm install
      - run: npm run test:tui
```

### Test Reporting

The framework generates detailed JSON reports:

```json
{
  "summary": {
    "totalTests": 10,
    "totalPassed": 10,
    "totalFailed": 0,
    "successRate": 100,
    "duration": 5432
  },
  "suites": [...],
  "environment": {...}
}
```

## Contributing

### Adding New Tests

1. Create test file in `tests/tui/`
2. Import `TUITestFramework`
3. Create test suite with descriptive name
4. Add comprehensive test scenarios
5. Update `run-all-tui-tests.mjs` to include new suite

### Framework Improvements

1. Add new features to `tui-test-framework.mjs`
2. Update documentation
3. Add integration tests
4. Ensure backward compatibility

## License

This TUI testing framework is part of the pf-web-poly-compile-helper-runner project and follows the same license terms.