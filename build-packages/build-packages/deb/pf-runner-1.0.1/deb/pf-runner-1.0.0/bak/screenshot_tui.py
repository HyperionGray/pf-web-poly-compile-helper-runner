#!/usr/bin/env python3
"""
Script to capture TUI menu screenshot
"""

import sys
import os

# Add pf-runner to path
script_dir = os.path.dirname(os.path.abspath(__file__))
pf_runner_path = os.path.join(script_dir, 'pf-runner')
sys.path.insert(0, pf_runner_path)

from pf_tui import PfTUI
from rich.console import Console

def show_menu_screenshot():
    """Show TUI menu for screenshot"""
    console = Console()
    
    # Initialize TUI
    tui = PfTUI()
    tui.load_tasks()
    tui.categorize_tasks()
    
    # Show header and menu
    tui.show_header()
    
    console.print("\n[bold cyan]Main Menu:[/bold cyan]")
    console.print("  [1] List all tasks by category")
    console.print("  [2] Run a task")
    console.print("  [3] Check task syntax")
    console.print("  [4] View debugging tools")
    console.print("  [5] Search tasks")
    console.print("  [6] Exploit Development Tools")
    console.print("  [q] Quit")
    
    console.print("\n[bold green]New Feature:[/bold green] Option 6 provides quick access to:")
    console.print("  • Install exploit tools (pwntools, ROPgadget, checksec)")
    console.print("  • Run exploit workflow on binaries")
    console.print("  • Generate exploit templates")
    console.print("  • Find ROP gadgets")
    console.print("  • Access comprehensive help")
    
    console.print("\n[bold yellow]Task Categories Available:[/bold yellow]")
    for i, category in enumerate(tui.categories[:8], 1):
        console.print(f"  {i}. {category.name} ({len(category.tasks)} tasks)")
    console.print(f"  ... and {len(tui.categories) - 8} more categories")
    
    console.print(f"\n[bold]Total:[/bold] {len(tui.tasks)} tasks in {len(tui.categories)} categories")
    console.print("\n[dim]Press Ctrl+C to exit this demo[/dim]")

if __name__ == "__main__":
    show_menu_screenshot()
