# Contributing to pf-web-poly-compile-helper-runner

Thank you for your interest in contributing to this project! This document provides guidelines and instructions for contributing.

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
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to help us maintain a welcoming and inclusive community.

## Getting Started

1. **Fork the repository** on GitHub

2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/pf-web-poly-compile-helper-runner.git
   cd pf-web-poly-compile-helper-runner
   ```

2.5. **Add the upstream remote**: 
   ```bash
   git remote add upstream https://github.com/P4X-ng/pf-web-poly-compile-helper-runner.git
   ```

<small>It's 2.5 because I forgot a step and don't feel like renumbering them all</small>

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

## How to Contribute

### Reporting Bugs

<<<<<<< HEAD
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
=======
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

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Add or update tests as needed
4. Ensure all tests pass
5. Commit your changes with a descriptive message
6. Push to your fork
7. Open a Pull Request

## Development Setup

### Prerequisites

- Linux (Ubuntu/Debian recommended) or macOS
- Python 3.10+
- Node.js 18+
- Git
- Docker or Podman (optional, for container-based development)

### Installation

```bash
# Install pf runner
sudo ./install.sh

# Or for user-level installation
./install.sh --prefix ~/.local

# Install Node.js dependencies
npm install

# Install Playwright for testing
npx playwright install
```

### Running the Development Server

```bash
pf web-dev
```

## Pull Request Process

1. **Update documentation** if your changes require it
2. **Add tests** for new functionality
3. **Ensure all tests pass**:
   ```bash
   pf web-test
   npm run test:unit
   ```
4. **Update the CHANGELOG.md** if applicable
5. **Request a review** from a maintainer
6. **Address feedback** promptly

### Commit Message Guidelines

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

## Coding Standards

### Python (pf-runner)

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for public functions and classes

### JavaScript/TypeScript

- Use ESLint configuration (if present)
- Use meaningful variable and function names
- Write JSDoc comments for public APIs

### pf Task Files (.pf)

- Use `describe` for all tasks
- Include meaningful descriptions
- Follow the established DSL patterns
>>>>>>> 567bbdc (Changes before error encountered)

## Testing

### Running Tests

```bash
<<<<<<< HEAD
# Run all web tests
=======
# Run all Playwright tests
>>>>>>> 567bbdc (Changes before error encountered)
pf web-test

# Run specific test file
npx playwright test tests/e2e/polyglot-plus-c.spec.ts

<<<<<<< HEAD
# Run tests with debug mode
=======
# Run unit tests
npm run test:unit

# Run with verbose output
npm run test:unit:verbose

# Debug tests
>>>>>>> 567bbdc (Changes before error encountered)
npx playwright test --debug
```

### Writing Tests

<<<<<<< HEAD
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
=======
- Place E2E tests in `tests/e2e/`
- Place unit tests in appropriate subdirectories under `tests/`
- Use descriptive test names
- Test both success and failure cases

## Documentation

- Update README.md for significant changes
- Update QUICKSTART.md for user-facing changes
- Add to docs/ for new features or guides
- Keep documentation up-to-date with code changes

## Questions?

If you have questions, feel free to:

- Open an issue for discussion
- Check existing documentation in `pf-runner/README.md`
- Review example tasks in `Pfyfile.pf` files

Thank you for contributing! 🚀
>>>>>>> 567bbdc (Changes before error encountered)
