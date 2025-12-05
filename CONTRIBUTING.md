# Contributing to pf-web-poly-compile-helper-runner

Thank you for your interest in contributing to the pf task runner and polyglot WebAssembly development environment! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

## Getting Started

### Prerequisites

- Linux (Ubuntu/Debian recommended) or macOS
- Git
- Python 3.10+
- Docker or Podman (for containerized workflows)
- Node.js (for web development features)

### Setting Up Your Development Environment

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/pf-web-poly-compile-helper-runner.git
   cd pf-web-poly-compile-helper-runner
   ```

3. **Install pf-runner**:
   ```bash
   ./install.sh --prefix ~/.local
   ```

4. **Install development dependencies**:
   ```bash
   npm install playwright
   npx playwright install
   ```

5. **Verify your setup**:
   ```bash
   pf --version
   pf list
   ```

## How to Contribute

### Reporting Bugs

1. **Check existing issues** to avoid duplicates
2. **Use the bug report template** when creating new issues
3. **Include**:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, Python version, etc.)
   - Relevant logs or error messages

### Suggesting Features

1. **Check existing issues and discussions** for similar suggestions
2. **Create a feature request** with:
   - Clear description of the proposed feature
   - Use cases and benefits
   - Potential implementation approach (optional)

### Contributing Code

1. **Find an issue to work on** or create one for new features
2. **Comment on the issue** to let others know you're working on it
3. **Create a feature branch** from `main`
4. **Make your changes** following our coding standards
5. **Add tests** for new functionality
6. **Submit a pull request**

## Development Workflow

### Branch Naming

Use descriptive branch names:
- `feature/add-new-build-system`
- `fix/wasm-compilation-error`
- `docs/update-quickstart`
- `refactor/parser-improvements`

### Commit Messages

Follow conventional commit format:
```
type(scope): brief description

Optional longer description explaining the change.

Fixes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Making Changes

1. **Create your branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with small, focused commits

3. **Test your changes**:
   ```bash
   pf web-test
   ```

4. **Push your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

## Coding Standards

### Python Code (pf-runner)

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Keep functions focused and modular
- Document complex logic with comments

### Pfyfile Tasks

- Use clear, descriptive task names
- Add `describe` for all tasks
- Keep tasks focused on single responsibilities
- Use consistent naming: `module-action` format

### JavaScript/TypeScript

- Use ES modules
- Follow existing formatting conventions
- Add JSDoc comments for public APIs

## Testing

### Running Tests

```bash
# Run all web tests
pf web-test

# Run specific test file
npx playwright test tests/e2e/polyglot-plus-c.spec.ts

# Run tests with debug mode
npx playwright test --debug
```

### Writing Tests

- Add tests for new features in `tests/e2e/`
- Follow existing test patterns
- Test both success and failure cases
- Use descriptive test names

## Documentation

### Updating Documentation

- Update relevant `.md` files for feature changes
- Keep README.md up to date
- Add examples for new features
- Update CHANGELOG.md for notable changes

### Documentation Files

- `README.md` - Main project documentation
- `QUICKSTART.md` - Quick start guide
- `docs/*.md` - Feature-specific documentation
- `pf-runner/*.md` - pf-runner specific docs

## Pull Request Process

### Before Submitting

1. **Ensure your code follows** the coding standards
2. **Run the test suite** and ensure all tests pass
3. **Update documentation** as needed
4. **Add a changelog entry** for notable changes

### Submitting Your PR

1. **Create your pull request** against the `main` branch
2. **Fill out the PR template** completely
3. **Link related issues** using keywords (Fixes #123)
4. **Request review** from maintainers

### Review Process

1. Maintainers will review your PR
2. Address any requested changes
3. Once approved, a maintainer will merge your PR

### After Merge

- Delete your feature branch
- Update your local main branch
- Celebrate your contribution! 🎉

## Questions?

- Check the [documentation](README.md)
- Open a discussion on GitHub
- File an issue for bugs

Thank you for contributing to pf-web-poly-compile-helper-runner!
