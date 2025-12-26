# Contributing to pf-web-poly-compile-helper-runner

Thank you for your interest in contributing to this project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

## Getting Started

### Prerequisites

- Linux (Ubuntu/Debian recommended) or macOS
- Git
- Python 3.10+
- Docker or Podman (for containerized workflows)
- Node.js 18+ (for web development features)

### Development Setup

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/pf-web-poly-compile-helper-runner.git
   cd pf-web-poly-compile-helper-runner
   ```

3. **Add the upstream remote**: 
   ```bash
   git remote add upstream https://github.com/P4X-ng/pf-web-poly-compile-helper-runner.git
   ```

4. **Install pf-runner**:
   ```bash
   # Container-first install (recommended)
   ./install.sh --runtime podman

   # Native host install (optional)
   sudo ./install.sh --mode native
   ./install.sh --mode native --prefix ~/.local
   ```

5. **Install development dependencies**:
   ```bash
   npm install
   npx playwright install
   ```

6. **Verify your setup**:
   ```bash
   pf --version
   pf list
   ```

## How to Contribute

### Reporting Issues

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- A clear and descriptive title
- Steps to reproduce the behavior
- Expected behavior vs actual behavior
- Your environment (OS, Python version, Node.js version, etc.)
- Any relevant logs or error messages

### Suggesting Enhancements

Enhancement suggestions are welcome! Please include:

- A clear and descriptive title
- Detailed description of the proposed enhancement
- Explanation of why this enhancement would be useful
- Examples of how it would work

### Contributing Code

1. **Find an issue to work on** or create one for new features
2. **Comment on the issue** to let others know you're working on it
3. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes** following our coding standards
5. **Add tests** for new functionality
6. **Submit a pull request**

## Pull Request Process

1. **Update documentation** if your changes require it
2. **Add tests** for new functionality
3. **Ensure all tests pass**:
   ```bash
   npm run test:all
   ```
4. **Update the CHANGELOG.md** if applicable
5. **Request a review** from a maintainer
6. **Address feedback** promptly

### Commit Message Guidelines

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Types:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

## Coding Standards

### Python (pf-runner)

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for public functions and classes
- Use meaningful variable and function names

### JavaScript/TypeScript

- Use ES modules
- Follow existing formatting conventions
- Add JSDoc comments for public APIs

## Testing

### Running Tests

```bash
# Run all tests
npm run test:all

# Run specific test suites
npm run test          # Playwright E2E tests
npm run test:unit     # Unit tests
npm run test:tui      # TUI tests
npm run test:grammar  # Grammar tests
```

### Writing Tests

- Place E2E tests in `tests/e2e/`
- Place unit tests in appropriate subdirectories under `tests/`
- Use descriptive test names
- Test both success and failure cases

### Debugging Tests

```bash
# Debug Playwright tests
npm run test:debug

# Run tests with UI
npm run test:ui
```

## Documentation

- Update README.md for significant changes
- Update QUICKSTART.md for user-facing changes
- Add to docs/ for new features or guides
- Keep documentation up-to-date with code changes

## Task File Contributions

When contributing new pf tasks:

- Use descriptive task names
- Include `describe` for all tasks
- Follow established DSL patterns
- Test tasks thoroughly

Example:
```pf
describe "Brief description of what this task does"
task my-new-task
  # Task implementation
end
```

## Questions?

If you have questions about contributing, feel free to:

- Open an issue for discussion
- Check existing documentation in `pf-runner/README.md`
- Review example tasks in `Pfyfile.pf` files

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.
