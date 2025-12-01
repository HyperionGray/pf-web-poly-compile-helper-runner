#!/usr/bin/env python3
"""
pf_tui.py - Interactive TUI for pf runner using rich library

This module provides a comprehensive Text User Interface for:
1. Listing and running tasks organized by categories
2. Visual debugging with integrated debugger tools
3. Syntax checking and validation
4. Job status monitoring
"""

import sys
import os
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.tree import Tree
from rich import box
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn

# Import existing pf functionality
from pf_parser import (
    _find_pfyfile, _load_pfy_source_with_includes, parse_pfyfile_text,
    list_dsl_tasks_with_desc, Task, BUILTINS
)
from pf_shell import validate_shell_syntax


@dataclass
class TaskCategory:
    """Represents a category of tasks"""
    name: str
    tasks: List[Tuple[str, str]]  # [(task_name, description)]
    color: str = "cyan"


class PfTUI:
    """Interactive TUI for pf runner"""
    
    def __init__(self, pfyfile: Optional[str] = None):
        self.console = Console()
        self.pfyfile = pfyfile
        self.tasks: Dict[str, Task] = {}
        self.categories: List[TaskCategory] = []
        
    def load_tasks(self) -> bool:
        """Load tasks from Pfyfile"""
        try:
            dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=self.pfyfile)
            self.tasks = parse_pfyfile_text(dsl_src, task_sources)
            return True
        except Exception as e:
            self.console.print(f"[red]Error loading tasks: {e}[/red]")
            return False
    
    def categorize_tasks(self) -> None:
        """Organize tasks into categories"""
        tasks_with_desc = list_dsl_tasks_with_desc(file_arg=self.pfyfile)
        
        categories = {
            "web": TaskCategory("Web & WASM", [], "cyan"),
            "build": TaskCategory("Build & Compilation", [], "green"),
            "install": TaskCategory("Installation", [], "yellow"),
            "test": TaskCategory("Testing", [], "magenta"),
            "debug": TaskCategory("Debugging & RE", [], "red"),
            "exploit": TaskCategory("Exploit Development", [], "bright_red"),
            "security": TaskCategory("Security Testing", [], "bright_red"),
            "kernel": TaskCategory("Kernel Debugging", [], "bright_yellow"),
            "injection": TaskCategory("Binary Injection", [], "bright_magenta"),
            "lifting": TaskCategory("Binary Lifting", [], "bright_cyan"),
            "rop": TaskCategory("ROP Exploitation", [], "bright_blue"),
            "git": TaskCategory("Git Tools", [], "bright_green"),
            "pwn": TaskCategory("Pwntools & Shellcode", [], "bright_red"),
            "heap": TaskCategory("Heap Exploitation", [], "bright_magenta"),
            "practice": TaskCategory("Practice Binaries", [], "yellow"),
            "core": TaskCategory("Core Tasks", [], "white"),
        }
        
        for task_name, description in tasks_with_desc:
            categorized = False
            
            # Categorize based on task name prefix
            for prefix, category in categories.items():
                if task_name.startswith(f"{prefix}-"):
                    category.tasks.append((task_name, description or ""))
                    categorized = True
                    break
            
            # Special handling for tasks without prefix but with known patterns
            if not categorized:
                if any(keyword in task_name.lower() for keyword in ['exploit', 'pwn', 'rop', 'shellcode', 'gadget']):
                    categories["exploit"].tasks.append((task_name, description or ""))
                    categorized = True
                elif any(keyword in task_name.lower() for keyword in ['heap', 'spray']):
                    categories["heap"].tasks.append((task_name, description or ""))
                    categorized = True
                elif any(keyword in task_name.lower() for keyword in ['practice', 'demo', 'vulnerable']):
                    categories["practice"].tasks.append((task_name, description or ""))
                    categorized = True
            
            if not categorized:
                categories["core"].tasks.append((task_name, description or ""))
        
        # Only add categories that have tasks
        self.categories = [cat for cat in categories.values() if cat.tasks]
    
    def show_header(self) -> None:
        """Display TUI header"""
        title = Text("pf Task Runner - Interactive TUI", style="bold cyan")
        subtitle = Text("Navigate tasks, check syntax, and debug with ease", style="dim")
        
        header_panel = Panel(
            Text.assemble(title, "\n", subtitle),
            box=box.DOUBLE,
            border_style="bright_cyan",
        )
        self.console.print(header_panel)
    
    def show_menu(self) -> str:
        """Display main menu and get user choice"""
        self.console.print("\n[bold cyan]Main Menu:[/bold cyan]")
        self.console.print("  [1] List all tasks by category")
        self.console.print("  [2] Run a task")
        self.console.print("  [3] Check task syntax")
        self.console.print("  [4] View debugging tools")
        self.console.print("  [5] Search tasks")
        self.console.print("  [6] Exploit Development Tools")
        self.console.print("  [q] Quit")
        
        choice = Prompt.ask("\nSelect an option", choices=["1", "2", "3", "4", "5", "6", "q"], default="1")
        return choice
    
    def list_tasks_by_category(self) -> None:
        """Display tasks organized by category"""
        self.console.clear()
        self.show_header()
        
        for category in self.categories:
            if not category.tasks:
                continue
            
            table = Table(
                title=f"[bold {category.color}]{category.name}[/bold {category.color}]",
                box=box.ROUNDED,
                show_header=True,
                header_style=f"bold {category.color}",
            )
            table.add_column("Task Name", style=category.color, no_wrap=True)
            table.add_column("Description", style="dim")
            
            for task_name, description in sorted(category.tasks):
                table.add_row(task_name, description or "[dim]No description[/dim]")
            
            self.console.print(table)
            self.console.print()
    
    def run_task_interactive(self) -> None:
        """Interactive task runner"""
        self.console.print("\n[bold cyan]Task Runner[/bold cyan]")
        
        # Get all task names
        all_tasks = [task[0] for category in self.categories for task in category.tasks]
        all_tasks.sort()
        
        # Show available tasks
        self.console.print("\nAvailable tasks:")
        for i, task in enumerate(all_tasks[:20], 1):
            self.console.print(f"  {i}. {task}")
        if len(all_tasks) > 20:
            self.console.print(f"  ... and {len(all_tasks) - 20} more")
        
        task_name = Prompt.ask("\nEnter task name to run", default="list")
        
        if task_name not in all_tasks and task_name not in BUILTINS:
            self.console.print(f"[red]Task '{task_name}' not found[/red]")
            return
        
        # Get parameters
        params_input = Prompt.ask("Enter parameters (e.g., port=8080 dir=web)", default="")
        
        # Build command
        cmd_parts = ["pf", task_name]
        if params_input:
            cmd_parts.extend(params_input.split())
        
        cmd = " ".join(cmd_parts)
        
        # Confirm execution
        if Confirm.ask(f"\nExecute: [cyan]{cmd}[/cyan]?", default=True):
            self.console.print(f"\n[green]Executing:[/green] {cmd}")
            # Use subprocess for safer execution
            import subprocess
            result = subprocess.run(cmd, shell=True, capture_output=False)
            if result.returncode != 0:
                self.console.print(f"[red]Command failed with exit code {result.returncode}[/red]")
        else:
            self.console.print("[yellow]Execution cancelled[/yellow]")
    
    def check_syntax(self) -> None:
        """Check syntax of tasks"""
        self.console.print("\n[bold cyan]Syntax Checker[/bold cyan]")
        
        task_name = Prompt.ask("Enter task name to check", default="")
        
        if not task_name:
            self.console.print("[yellow]Checking all tasks...[/yellow]")
            self._check_all_tasks_syntax()
        else:
            self._check_task_syntax(task_name)
    
    def _check_task_syntax(self, task_name: str) -> None:
        """Check syntax of a specific task"""
        if task_name not in self.tasks and task_name not in BUILTINS:
            self.console.print(f"[red]Task '{task_name}' not found[/red]")
            return
        
        if task_name in BUILTINS:
            lines = BUILTINS[task_name]
        else:
            lines = self.tasks[task_name].lines
        
        self.console.print(f"\n[cyan]Checking syntax for task:[/cyan] {task_name}")
        
        errors = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('shell '):
                shell_cmd = stripped[6:].strip()
                result = validate_shell_syntax(shell_cmd)
                if not result["valid"]:
                    errors.append((i, line, result["error"]))
        
        if errors:
            self.console.print(f"[red]Found {len(errors)} syntax error(s):[/red]")
            for line_num, line, error in errors:
                self.console.print(f"  Line {line_num}: {error}")
                self.console.print(f"    {line}")
        else:
            self.console.print("[green]✓ All syntax checks passed[/green]")
    
    def _check_all_tasks_syntax(self) -> None:
        """Check syntax of all tasks"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Checking tasks...", total=len(self.tasks))
            
            errors_by_task = {}
            
            for task_name, task_obj in self.tasks.items():
                progress.update(task, advance=1, description=f"Checking {task_name}...")
                
                task_errors = []
                for i, line in enumerate(task_obj.lines, 1):
                    stripped = line.strip()
                    if stripped.startswith('shell '):
                        shell_cmd = stripped[6:].strip()
                        result = validate_shell_syntax(shell_cmd)
                        if not result["valid"]:
                            task_errors.append((i, line, result["error"]))
                
                if task_errors:
                    errors_by_task[task_name] = task_errors
        
        if errors_by_task:
            self.console.print(f"\n[red]Found syntax errors in {len(errors_by_task)} task(s):[/red]")
            for task_name, errors in errors_by_task.items():
                self.console.print(f"\n[yellow]{task_name}:[/yellow]")
                for line_num, line, error in errors:
                    self.console.print(f"  Line {line_num}: {error}")
                    self.console.print(f"    {line}")
        else:
            self.console.print("\n[green]✓ All tasks passed syntax checks[/green]")
    
    def show_debugging_tools(self) -> None:
        """Display available debugging tools"""
        self.console.clear()
        self.show_header()
        
        self.console.print("\n[bold cyan]Debugging & Reverse Engineering Tools[/bold cyan]\n")
        
        # Create a tree view of debugging tools
        tree = Tree("[bold]Available Tools[/bold]", guide_style="cyan")
        
        # Binary Analysis
        binary_branch = tree.add("[cyan]Binary Analysis[/cyan]")
        binary_branch.add("🔍 oryx - TUI for exploring binaries")
        binary_branch.add("🔍 binsider - Binary analyzer with TUI")
        binary_branch.add("🔍 Radare2 - Reverse engineering framework")
        binary_branch.add("🔍 Ghidra - NSA's reverse engineering suite")
        binary_branch.add("🔍 Snowman - C++ decompiler (open source)")
        
        # Exploit Development
        exploit_branch = tree.add("[bright_red]Exploit Development[/bright_red]")
        exploit_branch.add("💥 pwntools - Exploit development framework")
        exploit_branch.add("💥 checksec - Binary protection checker")
        exploit_branch.add("💥 ROPgadget - ROP chain automation")
        exploit_branch.add("💥 ropper - Alternative ROP tool")
        
        # Network Analysis
        network_branch = tree.add("[green]Network Analysis[/green]")
        network_branch.add("🌐 rustnet - Network monitoring tool")
        network_branch.add("🌐 Wireshark - Network protocol analyzer")
        
        # System Analysis
        system_branch = tree.add("[yellow]System Analysis[/yellow]")
        system_branch.add("⚙️  sysz - Systemd unit file viewer")
        system_branch.add("⚙️  strace - System call tracer")
        system_branch.add("⚙️  ltrace - Library call tracer")
        
        # Debuggers
        debugger_branch = tree.add("[red]Debuggers[/red]")
        debugger_branch.add("🐛 GDB - GNU Debugger")
        debugger_branch.add("🐛 LLDB - LLVM Debugger")
        debugger_branch.add("🐛 pwndbg - GDB plugin for exploit dev")
        
        # Binary Injection
        injection_branch = tree.add("[magenta]Binary Injection[/magenta]")
        injection_branch.add("💉 LD_PRELOAD injection")
        injection_branch.add("💉 Binary patching with patchelf")
        injection_branch.add("💉 Runtime injection")
        
        self.console.print(tree)
        
        # Show installation status
        self.console.print("\n[bold]Installation Status:[/bold]")
        tools_to_check = [
            ("gdb", "gdb --version", "GDB"),
            ("lldb", "lldb --version", "LLDB"),
            ("radare2", "r2 -version", "Radare2"),
            ("ghidra", "ghidra --version", "Ghidra"),
            ("snowman", "snowman --help", "Snowman"),
            ("oryx", "oryx --version", "oryx"),
            ("binsider", "binsider --version", "binsider"),
            ("pwntools", "python3 -c 'import pwn'", "pwntools"),
            ("checksec", "checksec --version", "checksec"),
            ("ROPgadget", "ROPgadget --version", "ROPgadget"),
            ("ropper", "ropper --version", "ropper"),
            ("strace", "strace -V", "strace"),
            ("patchelf", "patchelf --version", "patchelf"),
        ]
        
        status_table = Table(box=box.SIMPLE)
        status_table.add_column("Tool", style="cyan")
        status_table.add_column("Status", justify="center")
        
        for tool_name, check_cmd, display_name in tools_to_check:
            installed = self._check_tool_installed(check_cmd)
            status = "[green]✓ Installed[/green]" if installed else "[red]✗ Not installed[/red]"
            status_table.add_row(display_name, status)
        
        self.console.print(status_table)
        
        self.console.print("\n[dim]Note: Use pf tasks to install and configure these tools[/dim]")
    
    def _check_tool_installed(self, check_cmd: str) -> bool:
        """Check if a tool is installed"""
        try:
            import subprocess
            result = subprocess.run(
                check_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=2
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
        except Exception:
            # Catch any other unexpected errors
            return False
    
    def search_tasks(self) -> None:
        """Search for tasks by name or description"""
        self.console.print("\n[bold cyan]Task Search[/bold cyan]")
        
        query = Prompt.ask("Enter search query")
        query_lower = query.lower()
        
        results = []
        for category in self.categories:
            for task_name, description in category.tasks:
                if query_lower in task_name.lower() or query_lower in description.lower():
                    results.append((task_name, description, category.name))
        
        if results:
            self.console.print(f"\n[green]Found {len(results)} matching task(s):[/green]")
            
            table = Table(box=box.ROUNDED)
            table.add_column("Task Name", style="cyan")
            table.add_column("Description", style="white")
            table.add_column("Category", style="dim")
            
            for task_name, description, category in results:
                table.add_row(task_name, description or "[dim]No description[/dim]", category)
            
            self.console.print(table)
        else:
            self.console.print(f"[yellow]No tasks found matching '{query}'[/yellow]")
    
    def show_exploit_tools(self) -> None:
        """Display exploit development tools menu"""
        self.console.clear()
        self.show_header()
        
        self.console.print("\n[bold bright_red]Exploit Development Tools[/bold bright_red]\n")
        
        # Create categories of exploit tools
        exploit_categories = {
            "Analysis & Info Gathering": [
                ("exploit-info", "Comprehensive binary analysis"),
                ("checksec", "Check binary security features"),
                ("exploit-test-tools", "Test all exploit tools installation"),
            ],
            "Exploit Generation": [
                ("pwn-template", "Generate exploit template"),
                ("exploit-workflow", "Complete exploit development workflow"),
                ("buffer-overflow-exploit", "Generate buffer overflow exploit"),
                ("format-string-exploit", "Generate format string exploit"),
            ],
            "ROP Chain Building": [
                ("rop-find-gadgets", "Find ROP gadgets in binary"),
                ("rop-chain-build", "Build ROP chain automatically"),
                ("rop-search-gadgets", "Search for specific gadgets"),
                ("ropper-gadgets", "Find gadgets using ropper"),
            ],
            "Shellcode & Patterns": [
                ("pwn-shellcode", "Generate shellcode"),
                ("pwn-cyclic", "Generate cyclic pattern"),
                ("pwn-cyclic-find", "Find offset in pattern"),
                ("buffer-overflow-pattern", "Generate overflow pattern"),
            ],
            "Installation": [
                ("install-exploit-tools", "Install all exploit tools"),
                ("install-pwntools", "Install pwntools"),
                ("install-ropgadget", "Install ROPgadget"),
                ("install-checksec", "Install checksec"),
            ],
        }
        
        # Display in a tree structure
        tree = Tree("[bold]Exploit Development Tools[/bold]", guide_style="bright_red")
        
        for category, tools in exploit_categories.items():
            category_branch = tree.add(f"[bright_red]{category}[/bright_red]")
            for task_name, description in tools:
                category_branch.add(f"[cyan]{task_name}[/cyan] - [dim]{description}[/dim]")
        
        self.console.print(tree)
        
        # Quick actions
        self.console.print("\n[bold]Quick Actions:[/bold]")
        self.console.print("  [1] Install all exploit tools")
        self.console.print("  [2] Run exploit workflow on a binary")
        self.console.print("  [3] Generate exploit template")
        self.console.print("  [4] Find ROP gadgets")
        self.console.print("  [5] View exploit help")
        self.console.print("  [b] Back to main menu")
        
        action = Prompt.ask("\nSelect action", choices=["1", "2", "3", "4", "5", "b"], default="b")
        
        if action == "1":
            self._run_exploit_action("install-exploit-tools")
        elif action == "2":
            binary = Prompt.ask("Enter binary path")
            self._run_exploit_action(f"exploit-workflow binary={binary}")
        elif action == "3":
            binary = Prompt.ask("Enter binary path")
            output = Prompt.ask("Enter output file name", default="exploit.py")
            self._run_exploit_action(f"pwn-template binary={binary} output={output}")
        elif action == "4":
            binary = Prompt.ask("Enter binary path")
            self._run_exploit_action(f"rop-find-gadgets binary={binary}")
        elif action == "5":
            self._run_exploit_action("exploit-help")
    
    def _run_exploit_action(self, command: str) -> None:
        """Run an exploit development command"""
        import subprocess
        self.console.print(f"\n[green]Executing:[/green] pf {command}")
        result = subprocess.run(f"pf {command}", shell=True, capture_output=False)
        if result.returncode != 0:
            self.console.print(f"[red]Command failed with exit code {result.returncode}[/red]")
        Prompt.ask("\nPress Enter to continue")
    
    def run(self) -> int:
        """Main TUI loop"""
        try:
            # Load tasks
            if not self.load_tasks():
                return 1
            
            # Categorize tasks
            self.categorize_tasks()
            
            # Main loop
            while True:
                self.console.clear()
                self.show_header()
                
                choice = self.show_menu()
                
                if choice == "1":
                    self.list_tasks_by_category()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "2":
                    self.run_task_interactive()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "3":
                    self.check_syntax()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "4":
                    self.show_debugging_tools()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "5":
                    self.search_tasks()
                    Prompt.ask("\nPress Enter to continue")
                elif choice == "6":
                    self.show_exploit_tools()
                elif choice == "q":
                    self.console.print("\n[cyan]Goodbye![/cyan]")
                    return 0
            
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Interrupted by user[/yellow]")
            return 130
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]")
            return 1


def main():
    """Entry point for pf TUI"""
    pfyfile = None
    if len(sys.argv) > 1:
        pfyfile = sys.argv[1]
    
    tui = PfTUI(pfyfile)
    return tui.run()


if __name__ == "__main__":
    sys.exit(main())
