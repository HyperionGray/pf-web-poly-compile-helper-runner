# pf TUI - Interactive Task Runner Interface

A comprehensive Text User Interface (TUI) for the pf task runner, built with Python's rich library for beautiful terminal display and interaction.

## Overview

The pf TUI provides a modern, intuitive interface for:
- **Task Management**: Browse, search, and run tasks organized by categories
- **Visual Debugging**: Integration with debugging and reverse engineering tools
- **Syntax Checking**: Validate task definitions before execution
- **Tool Discovery**: View available debugging tools and their installation status

## Features

### 1. Task Organization by Category

Tasks are automatically categorized based on their naming patterns:

- **Web & WASM**: Web development and WebAssembly compilation tasks
- **Build & Compilation**: Build system integration and compilation tasks
- **Installation**: Tool and dependency installation tasks
- **Testing**: Test execution and validation tasks
- **Debugging & RE**: Debugging and reverse engineering tasks
- **Security Testing**: Security scanning and vulnerability testing
- **Binary Injection**: Binary patching and code injection
- **Binary Lifting**: Binary-to-IR conversion tasks
- **ROP Exploitation**: Return-oriented programming tools
- **Git Tools**: Repository management and cleanup
- **Core Tasks**: General-purpose tasks

### 2. Interactive Task Execution

- Select tasks from a list or enter task names directly
- Provide parameters interactively (e.g., `port=8080 dir=web`)
- Confirm execution before running
- Real-time output display

### 3. Syntax Checking

- Validate shell commands in task definitions
- Check individual tasks or scan all tasks
- Detailed error reporting with line numbers
- Progress bar for batch validation

### 4. Debugging Tools Integration

The TUI displays information about integrated debugging and reverse engineering tools:

#### Binary Analysis Tools
- **oryx**: TUI for exploring binaries (https://github.com/pythops/oryx)
- **binsider**: Binary analyzer with TUI (https://github.com/orhun/binsider)
- **Radare2**: Reverse engineering framework
- **Ghidra**: NSA's reverse engineering suite

#### Network Analysis Tools
- **rustnet**: Network monitoring tool (https://github.com/domcyrus/rustnet)
- **Wireshark**: Network protocol analyzer

#### System Analysis Tools
- **sysz**: Systemd unit file viewer (https://github.com/joehillen/sysz)
- **strace**: System call tracer
- **ltrace**: Library call tracer

#### Debuggers
- **GDB**: GNU Debugger
- **LLDB**: LLVM Debugger
- **pwndbg**: GDB plugin for exploit development

#### Binary Injection
- **LD_PRELOAD injection**: Library preloading technique
- **Binary patching**: Modify binaries with patchelf
- **Runtime injection**: Inject code into running processes

### 5. Tool Installation Status

The TUI checks and displays the installation status of debugging tools, showing:
- ✓ Installed tools (green)
- ✗ Not installed tools (red)

## Installation

### Prerequisites

```bash
# Install rich library (if not already installed)
pip3 install --user rich

# Or use the pf task
pf install-tui-deps
```

### Usage

#### Launch the TUI

```bash
# Start with default Pfyfile
pf tui

# Start with a specific Pfyfile
pf tui-with-file file=custom.pf
```

#### TUI Navigation

Once launched, the TUI presents a main menu:

```
Main Menu:
  [1] List all tasks by category
  [2] Run a task
  [3] Check task syntax
  [4] View debugging tools
  [5] Search tasks
  [q] Quit
```

## Menu Options

### 1. List All Tasks by Category

Displays a beautiful table-based view of all tasks, organized by category with:
- Task names in color-coded categories
- Task descriptions
- Easy-to-read table format

### 2. Run a Task

Interactive task execution:
1. View available tasks (shows first 20)
2. Enter the task name to run
3. Provide parameters (optional)
4. Confirm execution
5. View real-time output

Example:
```
Enter task name to run: web-dev
Enter parameters (e.g., port=8080 dir=web): port=3000

Execute: pf web-dev port=3000? [Y/n]: y
```

### 3. Check Task Syntax

Validate task definitions:
- Check a specific task by name
- Press Enter to check all tasks
- View detailed error reports with line numbers
- Progress bar shows validation status

### 4. View Debugging Tools

Displays:
- Tree view of available debugging tools
- Tool descriptions and purposes
- Installation status table
- Links to tool repositories (in documentation)

### 5. Search Tasks

Find tasks quickly:
- Search by task name
- Search by description
- View results in a table with category information

## Demo Mode

For non-interactive demonstration:

```bash
# Run the TUI demo
python3 demo_tui.py
```

This showcases TUI capabilities without requiring user interaction.

## Architecture

### Components

1. **PfTUI Class**: Main TUI controller
   - `load_tasks()`: Load and parse Pfyfile
   - `categorize_tasks()`: Organize tasks by category
   - `show_menu()`: Display main menu
   - `run()`: Main TUI loop

2. **Task Category System**:
   - Automatic categorization based on task name prefixes
   - Color-coded categories for visual distinction
   - Extensible category definitions

3. **Syntax Validation**:
   - Integration with `pf_shell.validate_shell_syntax()`
   - Line-by-line validation
   - Detailed error reporting

4. **Tool Detection**:
   - Checks for installed debugging tools
   - Displays status with visual indicators
   - Provides installation guidance

## Debugging Tools Integration (v0.1)

### Implemented Features

- ✅ Tool discovery and status display
- ✅ Integration with existing pf debugging tasks
- ✅ Visual tool categorization
- ✅ Installation status checking

### Planned Features (Future Releases)

- [ ] Direct tool launch from TUI
- [ ] Tool configuration interface
- [ ] Real-time debugging session monitoring
- [ ] Integration with WASM compilation pipeline
- [ ] Plugin system for custom tools

## Examples

### Example 1: Browse and Run Web Tasks

```bash
pf tui
# Select [1] List all tasks by category
# Press Enter to continue
# Select [2] Run a task
# Enter: web-dev
# Enter: port=8080
# Confirm: y
```

### Example 2: Validate All Tasks

```bash
pf tui
# Select [3] Check task syntax
# Press Enter (no task name = check all)
# View results
```

### Example 3: Search for Security Tasks

```bash
pf tui
# Select [5] Search tasks
# Enter: security
# View all security-related tasks
```

## Integration with pf Tasks

The TUI integrates seamlessly with existing pf tasks:

```bash
# Install TUI dependencies
pf install-tui-deps

# Launch TUI
pf tui

# View TUI help
pf tui-help
```

## Keyboard Shortcuts

- **Number keys (1-5)**: Select menu option
- **q**: Quit TUI
- **Enter**: Confirm selection or continue
- **Ctrl+C**: Interrupt and exit

## Color Scheme

The TUI uses color-coding for better readability:

- **Cyan**: Web & WASM tasks
- **Green**: Build & Compilation, success messages
- **Yellow**: Installation tasks, warnings
- **Magenta**: Testing tasks
- **Red**: Debugging tasks, errors
- **Bright colors**: Special categories (security, kernel, etc.)

## Technical Details

### Dependencies

- **rich**: Terminal formatting and TUI components
- **pf_parser**: Task parsing and management
- **pf_shell**: Shell command validation

### File Structure

```
pf-runner/
├── pf_tui.py          # Main TUI implementation
├── pf_parser.py       # Task parsing (dependency)
├── pf_shell.py        # Shell validation (dependency)
└── ...

Pfyfile.tui.pf         # TUI task definitions
demo_tui.py            # Non-interactive demo
```

## Troubleshooting

### Issue: Module not found errors

```bash
# Ensure you're in the correct directory
cd pf-runner

# Install dependencies
pip3 install --user rich fabric
```

### Issue: Tasks not loading

```bash
# Verify Pfyfile exists
ls -la Pfyfile.pf

# Check for syntax errors in Pfyfile
pf list
```

### Issue: Colors not displaying

```bash
# Check terminal color support
echo $TERM

# Try setting TERM
export TERM=xterm-256color
```

## Contributing

To add new tool integrations to the TUI:

1. Add tool information to `show_debugging_tools()` in `pf_tui.py`
2. Add installation check to `_check_tool_installed()`
3. Create corresponding pf tasks for tool installation and usage
4. Update documentation

## References

- **rich library**: https://github.com/Textualize/rich
- **oryx**: https://github.com/pythops/oryx
- **binsider**: https://github.com/orhun/binsider
- **rustnet**: https://github.com/domcyrus/rustnet
- **sysz**: https://github.com/joehillen/sysz

## License

See main repository LICENSE file.
