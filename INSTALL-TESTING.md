# Installation Testing Guide

This document describes how to test the installer functionality.

## Test Scenarios

### 1. Base Installation Test

```bash
# Clone the repository
git clone <repository-url>
cd pf-web-poly-compile-helper-runner

# Test help output
./install.sh --help

# Run base installation
./install.sh base

# Verify installation
source ~/.bashrc  # or restart shell
pf list
pf install-base --help
```

Expected results:
- Fabric library installed
- pf command available in PATH
- Shell completions installed
- Base tasks visible in `pf list`

### 2. Interactive Installation Test

```bash
# Run interactive installer
./install.sh

# Select option 1 (Base only)
# Follow prompts
```

Expected results:
- Interactive menu displays correctly
- Installation proceeds based on selection
- Completion message shows next steps

### 3. Full Installation Test

```bash
# Install everything
./install.sh all
```

Expected results:
- Base installation completes
- Web tools installation attempts
- Node.js, Rust, and WABT installed (if supported)
- pf command works with all tasks

### 4. Using pf Tasks

```bash
# After base installation
pf install-web  # Install web tools
pf install      # Install everything
```

Expected results:
- Tasks execute install.sh with appropriate arguments
- Installation proceeds correctly

## Manual Verification Checklist

- [ ] `./install.sh --help` displays help text
- [ ] `./install.sh base` completes without errors
- [ ] `pf` command is available after installation
- [ ] `pf list` shows install tasks
- [ ] `pf install-base` task works
- [ ] `pf install-web` task works
- [ ] `pf install` task works
- [ ] Shell completions work (tab completion)
- [ ] README.md installation section is clear and accurate
- [ ] Installation works on Ubuntu/Debian
- [ ] Installation works on macOS (if possible to test)

## Edge Cases

### Test when Fabric already installed
```bash
pip install --user "fabric>=3.2,<4"
./install.sh base
```
Should detect existing installation and continue.

### Test with missing prerequisites
Temporarily remove git or python3 and verify installer handles it gracefully.

### Test with insufficient permissions
Try installation without sudo access - should fail gracefully with clear error messages.

## Cleanup

To clean up after testing:

```bash
# Remove installed pf command
rm -f ~/.local/bin/pf
rm -f ~/work/pf-web-poly-compile-helper-runner/pf-web-poly-compile-helper-runner/pf-runner/pf

# Remove completions
rm -f ~/.local/share/bash-completion/completions/pf
rm -f ~/.zsh/completions/_pf

# Uninstall Fabric (optional)
pip uninstall fabric
```

## Known Limitations

1. Emscripten installation requires manual steps (by design)
2. LFortran is optional and may not be available on all systems
3. Some web tools may require additional configuration
4. macOS may need Homebrew for some packages
