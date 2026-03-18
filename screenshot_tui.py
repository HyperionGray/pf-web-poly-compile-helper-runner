#!/usr/bin/env python3
"""
screenshot_tui.py - Screenshot/snapshot utility for the pf TUI menu

Renders a static snapshot of the pf TUI task menu for documentation
and preview purposes.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "pf-runner-full"))

try:
    from rich.console import Console
except ImportError:
    print("Error: rich is not installed. Install with: pip install rich", file=sys.stderr)
    sys.exit(1)

try:
    from pf_tui import PfTUI
except ImportError:
    print("Error: pf_tui module not available", file=sys.stderr)
    sys.exit(1)


def show_menu_screenshot() -> None:
    """Render a static snapshot of the pf TUI task menu."""
    console = Console()
    tui = PfTUI()

    try:
        tui.load_tasks()
        tui.categorize_tasks()
        tui.show_header()
    except Exception as exc:
        print(f"Error generating TUI screenshot: {exc}", file=sys.stderr)
        sys.exit(1)

    console.print("[bold yellow]==================== DEMO ====================[/bold yellow]")
    console.print("[bold green]pf Task Menu[/bold green]")
    if tui.categories:
        for category in tui.categories:
            console.print(f"  [cyan]{category.name}[/cyan]")
    else:
        console.print("  (no tasks found)")


if __name__ == "__main__":
    show_menu_screenshot()
