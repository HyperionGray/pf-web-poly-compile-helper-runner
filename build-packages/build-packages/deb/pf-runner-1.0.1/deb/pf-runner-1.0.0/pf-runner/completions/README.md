# pf Shell Completions

This directory contains shell completion scripts for the `pf` task runner.

## Installation

### Automatic Installation

The easiest way to install completions is via the Makefile:

```bash
cd pf-runner
make install-completions
```

This will automatically detect your shell and install the appropriate completion file.

### Manual Installation

#### Bash

**System-wide (requires sudo):**
```bash
sudo cp completions/pf-completion.bash /etc/bash_completion.d/pf
```

**User-level:**
```bash
mkdir -p ~/.local/share/bash-completion/completions
cp completions/pf-completion.bash ~/.local/share/bash-completion/completions/pf
```

Then restart your shell or source the file:
```bash
source ~/.local/share/bash-completion/completions/pf
```

#### Zsh

**System-wide (requires sudo):**
```bash
sudo cp completions/_pf /usr/local/share/zsh/site-functions/_pf
```

**User-level:**
```bash
mkdir -p ~/.zsh/completions
cp completions/_pf ~/.zsh/completions/_pf

# Add to your ~/.zshrc if not already present:
echo 'fpath=(~/.zsh/completions $fpath)' >> ~/.zshrc
echo 'autoload -U compinit && compinit' >> ~/.zshrc
```

Then restart your shell or reload completions:
```bash
exec zsh
# or
source ~/.zshrc
```

## Usage

Once installed, completions will work automatically when you type `pf` and press Tab:

```bash
# Complete task names from Pfyfile.pf
pf [TAB]

# Complete options
pf env=[TAB]
pf host=[TAB]

# Complete .pf file paths
pf Pfyfile.[TAB]

# Complete built-in tasks
pf lis[TAB]  # → pf list
```

## Features

### Bash Completion Features
- Task name completion from current Pfyfile.pf
- Built-in task completion (update, upgrade, list, help, etc.)
- Option completion (env=, hosts=, user=, sudo=, etc.)
- .pf file path completion

### Zsh Completion Features
- All bash features plus:
- Descriptive task names with descriptions
- Smart parameter completion
- Enhanced file path handling

## Troubleshooting

### Completions not working

1. **Check if completion file is sourced:**
   ```bash
   # Bash
   complete -p pf
   
   # Zsh
   which _pf
   ```

2. **Reload shell configuration:**
   ```bash
   # Bash
   source ~/.bashrc
   
   # Zsh
   exec zsh
   ```

3. **Check file permissions:**
   ```bash
   ls -l ~/.local/share/bash-completion/completions/pf
   ls -l ~/.zsh/completions/_pf
   ```
   Files should be readable (644 or 755).

### Tasks not appearing in completion

Make sure you have a `Pfyfile.pf` in your current directory and that `pf list` works:
```bash
cd /path/to/your/project
pf list
```

If `pf list` works but completions don't show tasks, try regenerating completions:
```bash
# Force reload bash completions
. ~/.local/share/bash-completion/completions/pf

# Force reload zsh completions
rm ~/.zcompdump
compinit
```

## Development

### Testing Completions

#### Bash
```bash
# Source the completion file directly
source completions/pf-completion.bash

# Test completion
pf [TAB][TAB]
```

#### Zsh
```bash
# Source directly
source completions/_pf

# Test completion
pf [TAB]
```

### Modifying Completions

After modifying the completion scripts:

1. Test your changes locally (see above)
2. Reinstall: `make install-completions`
3. Reload your shell or source the updated file

## Contributing

When adding new features to `pf`, please update the completion scripts:

1. Add new tasks to the built-in task list in both completion files
2. Add new options to the opts array/list
3. Test completions in both bash and zsh
4. Update this README if new features require documentation
