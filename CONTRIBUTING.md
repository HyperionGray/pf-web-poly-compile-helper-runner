# Contributing to pf-web-poly-compile-helper-runner

Thank you for your interest in contributing to this project! We welcome contributions from the community.

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub. When reporting issues, please include:

- A clear description of the problem or feature request
- Steps to reproduce the issue (if applicable)
- Expected vs actual behavior
- Your environment (OS, Node.js version, etc.)

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** with clear, descriptive commit messages
3. **Add tests** if applicable
4. **Update documentation** as needed
5. **Run the test suite** to ensure nothing is broken:
   ```bash
   npm test
   npm run test:unit
   npm run test:tui
   ```
6. **Submit a pull request** with a clear description of your changes

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/P4X-ng/pf-web-poly-compile-helper-runner.git
   cd pf-web-poly-compile-helper-runner
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Install pf-runner:
   ```bash
   sudo ./install.sh
   # Or for user installation:
   ./install.sh --prefix ~/.local
   ```

4. Run tests:
   ```bash
   npm test
   ```

### Code Style

- Follow the existing code style in the project
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and small

### Task File Contributions

When contributing new pf tasks:

1. Place task definitions in appropriate `.pf` files
2. Add a `describe` line for each task
3. Follow the naming convention: `category-action-name`
4. Test your tasks thoroughly before submitting

Example:
```text
task my-new-task
  describe Brief description of what this task does
  shell echo "Task implementation"
end
```

### Documentation

When contributing documentation:

- Update README.md for user-facing changes
- Add or update docs in the `docs/` directory
- Include examples where helpful
- Keep language clear and concise

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## Questions?

If you have questions about contributing, feel free to open an issue for discussion.

## License

By contributing, you agree that your contributions will be licensed under the project's ISC License.
