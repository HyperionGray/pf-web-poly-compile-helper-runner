#!/usr/bin/env python3
"""
pf_tui.py - Interactive TUI for pf runner using rich library

This module provides a comprehensive Text User Interface for:
1. Listing and running tasks organized by categories
2. Visual debugging with integrated debugger tools
3. Syntax checking and validation
4. Job status monitoring
5. Keyboard-navigable file and task browser
"""

import sys
import os
import glob
import subprocess
import traceback
import tty
import termios
import shutil
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field

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


@dataclass
class PfyFile:
    """Represents a Pfyfile with its tasks"""
    path: str
    name: str
    category: str
    tasks: List[Tuple[str, str]] = field(default_factory=list)  # [(task_name, description)]
    color: str = "cyan"


class PfTUI:
    """Interactive TUI for pf runner with keyboard navigation"""
    
    # Color mapping for file categories
    CATEGORY_COLORS = {
        "web": "cyan",
        "debug": "red",
        "debugging": "red",
        "exploit": "bright_red",
        "security": "bright_red",
        "kernel": "bright_yellow",
        "injection": "bright_magenta",
        "lifting": "bright_cyan",
        "rop": "bright_blue",
        "git": "bright_green",
        "heap": "bright_magenta",
        "practice": "yellow",
        "build": "green",
        "test": "magenta",
        "tui": "cyan",
        "core": "white",
    }
    
    def __init__(self, pfyfile: Optional[str] = None):
        self.console = Console()
        self.pfyfile = pfyfile
        self.tasks: Dict[str, Task] = {}
        self.categories: List[TaskCategory] = []
        self.pfy_files: List[PfyFile] = []
        self.current_view = "main"  # main, files, tasks, task_detail
        self.selected_index = 0
        self.selected_file: Optional[PfyFile] = None
        self.scroll_offset = 0
        self.max_display_items = 15
        
    def discover_pfy_files(self) -> None:
        """Discover all Pfyfile.*.pf files in the project"""
        # Find the root directory
        pfy_path = _find_pfyfile(file_arg=self.pfyfile)
        root_dir = os.path.dirname(pfy_path)
        
        # Also check parent directory for includes
        parent_dir = os.path.dirname(root_dir) if root_dir else "."
        
        self.pfy_files = []
        
        # Search for Pfyfile*.pf patterns
        search_dirs = [root_dir, parent_dir]
        seen_files = set()
        
        for search_dir in search_dirs:
            if not search_dir or not os.path.exists(search_dir):
                continue
            patterns = [
                os.path.join(search_dir, "Pfyfile.*.pf"),
                os.path.join(search_dir, "Pfyfile.pf"),
            ]
            for pattern in patterns:
                for filepath in glob.glob(pattern):
                    if filepath in seen_files:
                        continue
                    seen_files.add(filepath)
                    
                    basename = os.path.basename(filepath)
                    # Extract category from filename
                    if basename == "Pfyfile.pf":
                        category = "core"
                        name = "Main"
                    else:
                        # Remove Pfyfile. prefix and .pf suffix
                        category = basename[8:-3] if basename.startswith("Pfyfile.") else basename[:-3]
                        name = category.replace("-", " ").replace("_", " ").title()
                    
                    color = self.CATEGORY_COLORS.get(category, "white")
                    pfy_file = PfyFile(
                        path=filepath,
                        name=name,
                        category=category,
                        color=color,
                    )
                    self.pfy_files.append(pfy_file)
        
        # Sort by name
        self.pfy_files.sort(key=lambda f: f.name)
        
        # Load tasks for each file
        for pfy_file in self.pfy_files:
            try:
                tasks_desc = list_dsl_tasks_with_desc(file_arg=pfy_file.path)
                pfy_file.tasks = tasks_desc
            except Exception:
                pfy_file.tasks = []
        
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
    
    def show_header(self, subtitle_text: Optional[str] = None) -> None:
        """Display TUI header"""
        title = Text("pf Task Runner - Interactive TUI", style="bold cyan")
        if subtitle_text:
            subtitle = Text(subtitle_text, style="dim")
        else:
            subtitle = Text("Use ↑↓ to navigate, Enter to select, q to quit/back", style="dim")
        
        header_panel = Panel(
            Text.assemble(title, "\n", subtitle),
            box=box.DOUBLE,
            border_style="bright_cyan",
        )
        self.console.print(header_panel)
    
    def _get_key(self) -> str:
        """Get a single keypress from the user"""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            # Handle escape sequences for arrow keys
            if ch == '\x1b':
                ch2 = sys.stdin.read(1)
                if ch2 == '[':
                    ch3 = sys.stdin.read(1)
                    if ch3 == 'A':
                        return 'up'
                    elif ch3 == 'B':
                        return 'down'
                    elif ch3 == 'C':
                        return 'right'
                    elif ch3 == 'D':
                        return 'left'
                return 'escape'
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    def _open_in_editor(self, filepath: str) -> None:
        """Open a file in the user's default editor"""
        # Get editor from environment, with safe fallbacks
        editor = os.environ.get("EDITOR", os.environ.get("VISUAL", ""))
        
        # Define safe list of common editors
        safe_editors = ["nano", "vim", "vi", "emacs", "code", "gedit", "kate", "notepad"]
        
        # Validate editor is a known safe editor or exists in PATH
        if editor:
            # Extract just the command name (in case of paths)
            editor_name = os.path.basename(editor)
            # Check if it's in the safe list or is an absolute path that exists
            if editor_name not in safe_editors and not (os.path.isabs(editor) and os.path.isfile(editor)):
                # Verify it exists in PATH
                if not shutil.which(editor):
                    editor = ""
        
        # Try the configured editor first
        if editor:
            try:
                subprocess.run([editor, filepath], check=False)
                return
            except FileNotFoundError:
                pass
        
        # Fallback to common editors
        for fallback in safe_editors[:3]:  # Try nano, vim, vi
            if shutil.which(fallback):
                try:
                    subprocess.run([fallback, filepath], check=False)
                    return
                except FileNotFoundError:
                    continue
        
        self.console.print("[red]No editor found. Set EDITOR environment variable.[/red]")
        Prompt.ask("Press Enter to continue")
    
    def show_files_view(self) -> Optional[str]:
        """Display Pfyfiles in a navigable list. Returns action to take."""
        if not self.pfy_files:
            self.console.print("[yellow]No Pfyfiles found.[/yellow]")
            return "back"
        
        while True:
            self.console.clear()
            self.show_header("Browse Pfyfiles - Press e to edit, Enter to view tasks, q to go back")
            
            self.console.print("\n[bold cyan]📁 Pfyfiles[/bold cyan]\n")
            
            # Calculate display range with scrolling
            total_items = len(self.pfy_files)
            start_idx = self.scroll_offset
            end_idx = min(start_idx + self.max_display_items, total_items)
            
            # Show scroll indicator if needed
            if start_idx > 0:
                self.console.print("    [dim]↑ more above[/dim]")
            
            for i, pfy_file in enumerate(self.pfy_files[start_idx:end_idx], start=start_idx):
                task_count = len(pfy_file.tasks)
                prefix = "→ " if i == self.selected_index else "  "
                style = f"bold {pfy_file.color}" if i == self.selected_index else pfy_file.color
                
                name_text = f"{prefix}📄 {pfy_file.name}"
                task_info = f"({task_count} tasks)"
                
                if i == self.selected_index:
                    self.console.print(f"[{style}]{name_text}[/{style}] [dim]{task_info}[/dim]")
                else:
                    self.console.print(f"[{style}]{name_text}[/{style}] [dim]{task_info}[/dim]")
            
            if end_idx < total_items:
                self.console.print(f"    [dim]↓ {total_items - end_idx} more below[/dim]")
            
            self.console.print(f"\n[dim]File: {self.pfy_files[self.selected_index].path}[/dim]")
            self.console.print("\n[dim]Navigation: ↑/↓ move, Enter=view tasks, e=edit file, q=back[/dim]")
            
            key = self._get_key()
            
            if key == 'up' or key == 'k':
                if self.selected_index > 0:
                    self.selected_index -= 1
                    if self.selected_index < self.scroll_offset:
                        self.scroll_offset = self.selected_index
            elif key == 'down' or key == 'j':
                if self.selected_index < len(self.pfy_files) - 1:
                    self.selected_index += 1
                    if self.selected_index >= self.scroll_offset + self.max_display_items:
                        self.scroll_offset = self.selected_index - self.max_display_items + 1
            elif key == '\r' or key == '\n':
                self.selected_file = self.pfy_files[self.selected_index]
                return "view_tasks"
            elif key == 'e':
                self._open_in_editor(self.pfy_files[self.selected_index].path)
            elif key == 'q' or key == '\x1b':
                return "back"
    
    def show_tasks_for_file(self) -> Optional[str]:
        """Display tasks for the selected file in a navigable list."""
        if not self.selected_file or not self.selected_file.tasks:
            self.console.print("[yellow]No tasks found in this file.[/yellow]")
            return "back"
        
        task_index = 0
        task_scroll = 0
        tasks = self.selected_file.tasks
        
        while True:
            self.console.clear()
            self.show_header(f"Tasks in {self.selected_file.name} - Enter to run, q to go back")
            
            self.console.print(f"\n[bold {self.selected_file.color}]📋 {self.selected_file.name} Tasks[/bold {self.selected_file.color}]\n")
            
            # Calculate display range
            total_tasks = len(tasks)
            start_idx = task_scroll
            end_idx = min(start_idx + self.max_display_items, total_tasks)
            
            if start_idx > 0:
                self.console.print("    [dim]↑ more above[/dim]")
            
            for i, (task_name, description) in enumerate(tasks[start_idx:end_idx], start=start_idx):
                prefix = "→ " if i == task_index else "  "
                style = f"bold {self.selected_file.color}" if i == task_index else "white"
                
                desc_text = f" - {description}" if description else ""
                self.console.print(f"[{style}]{prefix}{task_name}[/{style}][dim]{desc_text}[/dim]")
            
            if end_idx < total_tasks:
                self.console.print(f"    [dim]↓ {total_tasks - end_idx} more below[/dim]")
            
            self.console.print("\n[dim]Navigation: ↑/↓ move, Enter=run task, s=syntax check, q=back[/dim]")
            
            key = self._get_key()
            
            if key == 'up' or key == 'k':
                if task_index > 0:
                    task_index -= 1
                    if task_index < task_scroll:
                        task_scroll = task_index
            elif key == 'down' or key == 'j':
                if task_index < len(tasks) - 1:
                    task_index += 1
                    if task_index >= task_scroll + self.max_display_items:
                        task_scroll = task_index - self.max_display_items + 1
            elif key == '\r' or key == '\n':
                task_name = tasks[task_index][0]
                self._run_task(task_name)
            elif key == 's':
                task_name = tasks[task_index][0]
                self._check_task_syntax(task_name)
                Prompt.ask("\nPress Enter to continue")
            elif key == 'q' or key == '\x1b':
                return "back"
    
    def _run_task(self, task_name: str) -> None:
        """Run a specific task"""
        self.console.clear()
        self.console.print(f"\n[bold cyan]Running task: {task_name}[/bold cyan]\n")
        
        # Get parameters if needed
        params_input = Prompt.ask("Enter parameters (e.g., port=8080 dir=web) or press Enter", default="")
        
        # Build command
        cmd_parts = ["pf", task_name]
        if params_input:
            cmd_parts.extend(params_input.split())
        
        cmd = " ".join(cmd_parts)
        
        self.console.print(f"\n[green]Executing:[/green] {cmd}\n")
        result = subprocess.run(cmd, shell=True, capture_output=False)
        if result.returncode != 0:
            self.console.print(f"\n[red]Command failed with exit code {result.returncode}[/red]")
        
        Prompt.ask("\nPress Enter to continue")
    
    def show_main_menu(self) -> str:
        """Display the main menu with keyboard navigation"""
        menu_items = [
            ("📁", "Browse Pfyfiles", "Navigate and manage your pf task files"),
            ("📋", "All Tasks by Category", "View all tasks organized by type"),
            ("🔍", "Search Tasks", "Find tasks by name or description"),
            ("✓", "Syntax Checker", "Validate task syntax"),
            ("🔧", "Debugging Tools", "View available debugging tools"),
            ("💥", "Exploit Tools", "Exploit development toolkit"),
            ("❌", "Quit", "Exit the TUI"),
        ]
        
        menu_index = 0
        
        while True:
            self.console.clear()
            self.show_header()
            
            self.console.print("\n[bold cyan]Main Menu[/bold cyan]\n")
            
            for i, (icon, title, desc) in enumerate(menu_items):
                prefix = "→ " if i == menu_index else "  "
                style = "bold cyan" if i == menu_index else "white"
                self.console.print(f"[{style}]{prefix}{icon} {title}[/{style}]")
                if i == menu_index:
                    self.console.print(f"     [dim]{desc}[/dim]")
            
            self.console.print("\n[dim]Use ↑/↓ to navigate, Enter to select[/dim]")
            
            key = self._get_key()
            
            if key == 'up' or key == 'k':
                menu_index = (menu_index - 1) % len(menu_items)
            elif key == 'down' or key == 'j':
                menu_index = (menu_index + 1) % len(menu_items)
            elif key == '\r' or key == '\n':
                # Return corresponding action
                if menu_index == 0:
                    return "files"
                elif menu_index == 1:
                    return "categories"
                elif menu_index == 2:
                    return "search"
                elif menu_index == 3:
                    return "syntax"
                elif menu_index == 4:
                    return "debug_tools"
                elif menu_index == 5:
                    return "exploit_tools"
                elif menu_index == 6:
                    return "quit"
            elif key == 'q':
                return "quit"
            elif key == '1':
                return "files"
            elif key == '2':
                return "categories"
            elif key == '3':
                return "search"
            elif key == '4':
                return "syntax"
            elif key == '5':
                return "debug_tools"
            elif key == '6':
                return "exploit_tools"
    
    def list_tasks_by_category(self) -> None:
        """Display tasks organized by category with keyboard navigation"""
        if not self.categories:
            self.console.print("[yellow]No tasks found.[/yellow]")
            return
        
        # Build flat list of all tasks across categories for navigation
        all_items = []  # [(category_name, task_name, description, color)]
        for category in self.categories:
            for task_name, description in sorted(category.tasks):
                all_items.append((category.name, task_name, description, category.color))
        
        if not all_items:
            self.console.print("[yellow]No tasks found.[/yellow]")
            return
        
        current_index = 0
        scroll_offset = 0
        max_items = 18  # More items visible
        
        while True:
            self.console.clear()
            self.show_header("All Tasks - Enter to run, s for syntax check, q to go back")
            
            # Calculate display range
            total_items = len(all_items)
            start_idx = scroll_offset
            end_idx = min(start_idx + max_items, total_items)
            
            self.console.print(f"\n[bold cyan]📋 All Tasks ({total_items} total)[/bold cyan]\n")
            
            if start_idx > 0:
                self.console.print("    [dim]↑ more above[/dim]")
            
            current_category = None
            for i in range(start_idx, end_idx):
                cat_name, task_name, description, color = all_items[i]
                
                # Show category header when it changes
                if cat_name != current_category:
                    current_category = cat_name
                    self.console.print(f"\n  [bold {color}]── {cat_name} ──[/bold {color}]")
                
                prefix = "  → " if i == current_index else "    "
                style = f"bold {color}" if i == current_index else "white"
                desc_text = f" [dim]- {description}[/dim]" if description else ""
                self.console.print(f"[{style}]{prefix}{task_name}[/{style}]{desc_text}")
            
            if end_idx < total_items:
                self.console.print(f"\n    [dim]↓ {total_items - end_idx} more below[/dim]")
            
            self.console.print("\n[dim]Navigation: ↑/↓ move, Enter=run, s=syntax check, q=back[/dim]")
            
            key = self._get_key()
            
            if key == 'up' or key == 'k':
                if current_index > 0:
                    current_index -= 1
                    if current_index < scroll_offset:
                        scroll_offset = current_index
            elif key == 'down' or key == 'j':
                if current_index < len(all_items) - 1:
                    current_index += 1
                    if current_index >= scroll_offset + max_items:
                        scroll_offset = current_index - max_items + 1
            elif key == '\r' or key == '\n':
                task_name = all_items[current_index][1]
                self._run_task(task_name)
            elif key == 's':
                task_name = all_items[current_index][1]
                self._check_task_syntax(task_name)
                Prompt.ask("\nPress Enter to continue")
            elif key == 'q' or key == '\x1b':
                return
    
    def run_task_interactive(self) -> None:
        """Interactive task runner with keyboard navigation"""
        # Get all task names
        all_tasks = [(task[0], task[1]) for category in self.categories for task in category.tasks]
        all_tasks.sort(key=lambda x: x[0])
        
        if not all_tasks:
            self.console.print("[yellow]No tasks found.[/yellow]")
            return
        
        current_index = 0
        scroll_offset = 0
        max_items = 15
        
        while True:
            self.console.clear()
            self.show_header("Select a Task to Run - Enter to run, q to go back")
            
            total_items = len(all_tasks)
            start_idx = scroll_offset
            end_idx = min(start_idx + max_items, total_items)
            
            self.console.print(f"\n[bold cyan]🚀 Run a Task ({total_items} available)[/bold cyan]\n")
            
            if start_idx > 0:
                self.console.print("    [dim]↑ more above[/dim]")
            
            for i in range(start_idx, end_idx):
                task_name, description = all_tasks[i]
                prefix = "→ " if i == current_index else "  "
                style = "bold cyan" if i == current_index else "white"
                desc_text = f" [dim]- {description}[/dim]" if description else ""
                self.console.print(f"[{style}]{prefix}{task_name}[/{style}]{desc_text}")
            
            if end_idx < total_items:
                self.console.print(f"\n    [dim]↓ {total_items - end_idx} more below[/dim]")
            
            self.console.print("\n[dim]Navigation: ↑/↓ move, Enter=run, q=back[/dim]")
            
            key = self._get_key()
            
            if key == 'up' or key == 'k':
                if current_index > 0:
                    current_index -= 1
                    if current_index < scroll_offset:
                        scroll_offset = current_index
            elif key == 'down' or key == 'j':
                if current_index < len(all_tasks) - 1:
                    current_index += 1
                    if current_index >= scroll_offset + max_items:
                        scroll_offset = current_index - max_items + 1
            elif key == '\r' or key == '\n':
                task_name = all_tasks[current_index][0]
                self._run_task(task_name)
            elif key == 'q' or key == '\x1b':
                return
    
    def check_syntax(self) -> None:
        """Check syntax of tasks with keyboard navigation"""
        # Get all task names
        all_tasks = [(task[0], task[1]) for category in self.categories for task in category.tasks]
        all_tasks.sort(key=lambda x: x[0])
        
        if not all_tasks:
            self.console.print("[yellow]No tasks found.[/yellow]")
            return
        
        # Add "Check All" as first option
        menu_items = [("Check All Tasks", "Validate syntax of all tasks")] + all_tasks
        
        current_index = 0
        scroll_offset = 0
        max_items = 15
        
        while True:
            self.console.clear()
            self.show_header("Syntax Checker - Select task to check, Enter to check, q to go back")
            
            total_items = len(menu_items)
            start_idx = scroll_offset
            end_idx = min(start_idx + max_items, total_items)
            
            self.console.print(f"\n[bold cyan]✓ Syntax Checker[/bold cyan]\n")
            
            if start_idx > 0:
                self.console.print("    [dim]↑ more above[/dim]")
            
            for i in range(start_idx, end_idx):
                task_name, description = menu_items[i]
                prefix = "→ " if i == current_index else "  "
                if i == 0:
                    # "Check All" option
                    style = "bold green" if i == current_index else "green"
                else:
                    style = "bold cyan" if i == current_index else "white"
                desc_text = f" [dim]- {description}[/dim]" if description else ""
                self.console.print(f"[{style}]{prefix}{task_name}[/{style}]{desc_text}")
            
            if end_idx < total_items:
                self.console.print(f"\n    [dim]↓ {total_items - end_idx} more below[/dim]")
            
            self.console.print("\n[dim]Navigation: ↑/↓ move, Enter=check, q=back[/dim]")
            
            key = self._get_key()
            
            if key == 'up' or key == 'k':
                if current_index > 0:
                    current_index -= 1
                    if current_index < scroll_offset:
                        scroll_offset = current_index
            elif key == 'down' or key == 'j':
                if current_index < len(menu_items) - 1:
                    current_index += 1
                    if current_index >= scroll_offset + max_items:
                        scroll_offset = current_index - max_items + 1
            elif key == '\r' or key == '\n':
                if current_index == 0:
                    # Check all tasks
                    self.console.clear()
                    self._check_all_tasks_syntax()
                    Prompt.ask("\nPress Enter to continue")
                else:
                    task_name = menu_items[current_index][0]
                    self.console.clear()
                    self._check_task_syntax(task_name)
                    Prompt.ask("\nPress Enter to continue")
            elif key == 'q' or key == '\x1b':
                return
    
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
                is_valid, error_msg = validate_shell_syntax(shell_cmd)
                if not is_valid:
                    errors.append((i, line, error_msg))
        
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
                        is_valid, error_msg = validate_shell_syntax(shell_cmd)
                        if not is_valid:
                            task_errors.append((i, line, error_msg))
                
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
        """Display available debugging tools with keyboard navigation"""
        while True:
            self.console.clear()
            self.show_header("Debugging Tools - Press q to go back")
            
            self.console.print("\n[bold cyan]🔧 Debugging & Reverse Engineering Tools[/bold cyan]\n")
            
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
            
            self.console.print("\n[dim]Press q to go back[/dim]")
            
            key = self._get_key()
            if key == 'q' or key == '\x1b':
                return
    
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
        """Search for tasks by name or description with interactive results"""
        self.console.clear()
        self.show_header("Search Tasks - Type to search, Enter to select, q to go back")
        
        query = Prompt.ask("\n[bold cyan]🔍 Enter search query[/bold cyan]")
        query_lower = query.lower()
        
        results = []
        for category in self.categories:
            for task_name, description in category.tasks:
                if query_lower in task_name.lower() or query_lower in (description or "").lower():
                    results.append((task_name, description, category.name, category.color))
        
        if not results:
            self.console.print(f"\n[yellow]No tasks found matching '{query}'[/yellow]")
            Prompt.ask("\nPress Enter to continue")
            return
        
        # Navigate results with keyboard
        current_index = 0
        scroll_offset = 0
        max_items = 15
        
        while True:
            self.console.clear()
            self.show_header(f"Search Results for '{query}' - Enter to run, s for syntax check, q to go back")
            
            total_items = len(results)
            start_idx = scroll_offset
            end_idx = min(start_idx + max_items, total_items)
            
            self.console.print(f"\n[bold green]Found {total_items} matching task(s)[/bold green]\n")
            
            if start_idx > 0:
                self.console.print("    [dim]↑ more above[/dim]")
            
            for i in range(start_idx, end_idx):
                task_name, description, cat_name, color = results[i]
                prefix = "→ " if i == current_index else "  "
                style = f"bold {color}" if i == current_index else "white"
                desc_text = f" [dim]- {description}[/dim]" if description else ""
                cat_text = f" [dim]({cat_name})[/dim]"
                self.console.print(f"[{style}]{prefix}{task_name}[/{style}]{desc_text}{cat_text}")
            
            if end_idx < total_items:
                self.console.print(f"\n    [dim]↓ {total_items - end_idx} more below[/dim]")
            
            self.console.print("\n[dim]Navigation: ↑/↓ move, Enter=run, s=syntax check, /=new search, q=back[/dim]")
            
            key = self._get_key()
            
            if key == 'up' or key == 'k':
                if current_index > 0:
                    current_index -= 1
                    if current_index < scroll_offset:
                        scroll_offset = current_index
            elif key == 'down' or key == 'j':
                if current_index < len(results) - 1:
                    current_index += 1
                    if current_index >= scroll_offset + max_items:
                        scroll_offset = current_index - max_items + 1
            elif key == '\r' or key == '\n':
                task_name = results[current_index][0]
                self._run_task(task_name)
            elif key == 's':
                task_name = results[current_index][0]
                self.console.clear()
                self._check_task_syntax(task_name)
                Prompt.ask("\nPress Enter to continue")
            elif key == '/':
                # New search
                return self.search_tasks()
            elif key == 'q' or key == '\x1b':
                return
    
    def show_exploit_tools(self) -> None:
        """Display exploit development tools menu with keyboard navigation"""
        # Build flat list of tools for navigation
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
        
        # Build flat list with category info
        all_items = []  # [(category, task_name, description)]
        for category, tools in exploit_categories.items():
            for task_name, description in tools:
                all_items.append((category, task_name, description))
        
        current_index = 0
        scroll_offset = 0
        max_items = 15
        
        while True:
            self.console.clear()
            self.show_header("Exploit Tools - Enter to run, q to go back")
            
            total_items = len(all_items)
            start_idx = scroll_offset
            end_idx = min(start_idx + max_items, total_items)
            
            self.console.print(f"\n[bold bright_red]💥 Exploit Development Tools ({total_items} tools)[/bold bright_red]\n")
            
            if start_idx > 0:
                self.console.print("    [dim]↑ more above[/dim]")
            
            current_category = None
            for i in range(start_idx, end_idx):
                cat_name, task_name, description = all_items[i]
                
                # Show category header when it changes
                if cat_name != current_category:
                    current_category = cat_name
                    self.console.print(f"\n  [bold bright_red]── {cat_name} ──[/bold bright_red]")
                
                prefix = "  → " if i == current_index else "    "
                style = "bold cyan" if i == current_index else "white"
                desc_text = f" [dim]- {description}[/dim]"
                self.console.print(f"[{style}]{prefix}{task_name}[/{style}]{desc_text}")
            
            if end_idx < total_items:
                self.console.print(f"\n    [dim]↓ {total_items - end_idx} more below[/dim]")
            
            self.console.print("\n[dim]Navigation: ↑/↓ move, Enter=run tool, q=back[/dim]")
            
            key = self._get_key()
            
            if key == 'up' or key == 'k':
                if current_index > 0:
                    current_index -= 1
                    if current_index < scroll_offset:
                        scroll_offset = current_index
            elif key == 'down' or key == 'j':
                if current_index < len(all_items) - 1:
                    current_index += 1
                    if current_index >= scroll_offset + max_items:
                        scroll_offset = current_index - max_items + 1
            elif key == '\r' or key == '\n':
                task_name = all_items[current_index][1]
                self._run_exploit_action(task_name)
            elif key == 'q' or key == '\x1b':
                return
    
    def _run_exploit_action(self, command: str) -> None:
        """Run an exploit development command"""
        self.console.clear()
        self.console.print(f"\n[green]Executing:[/green] pf {command}")
        result = subprocess.run(f"pf {command}", shell=True, capture_output=False)
        if result.returncode != 0:
            self.console.print(f"[red]Command failed with exit code {result.returncode}[/red]")
        Prompt.ask("\nPress Enter to continue")
    
    def run(self) -> int:
        """Main TUI loop with keyboard navigation"""
        try:
            # Load tasks
            if not self.load_tasks():
                return 1
            
            # Categorize tasks
            self.categorize_tasks()
            
            # Discover Pfyfiles
            self.discover_pfy_files()
            
            # Main loop
            while True:
                action = self.show_main_menu()
                
                if action == "files":
                    result = self.show_files_view()
                    if result == "view_tasks":
                        self.show_tasks_for_file()
                elif action == "categories":
                    self.list_tasks_by_category()
                elif action == "search":
                    self.search_tasks()
                elif action == "syntax":
                    self.check_syntax()
                elif action == "debug_tools":
                    self.show_debugging_tools()
                elif action == "exploit_tools":
                    self.show_exploit_tools()
                elif action == "quit":
                    self.console.clear()
                    self.console.print("\n[cyan]Goodbye![/cyan]")
                    return 0
            
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Interrupted by user[/yellow]")
            return 130
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]")
            traceback.print_exc()
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
