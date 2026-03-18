#!/usr/bin/env python3
"""
screenshot_tui.py - Screenshot/snapshot utility for the pf TUI menu.

Renders a static snapshot of the pf TUI task menu for documentation
and preview purposes.
"""

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNNER_DIR = os.path.join(ROOT_DIR, "pf-runner-full")
if RUNNER_DIR not in sys.path:
    sys.path.insert(0, RUNNER_DIR)

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


def _print_demo_banner(console: Console) -> None:
    """Print a prominent banner for demo-only runs."""
    line = "=" * 64
    console.print(f"[bold yellow]{line}[/bold yellow]")
    console.print("[bold yellow]DEMO MODE - NON-PRODUCTION OUTPUT[/bold yellow]")
    console.print(f"[bold yellow]{line}[/bold yellow]")


def show_menu_screenshot() -> None:
    """Render a static snapshot of the pf TUI task menu."""
    console = Console()
    tui = PfTUI()

    _print_demo_banner(console)

    try:
        tui.load_tasks()
        tui.categorize_tasks()
        tui.show_header()
    except Exception as exc:  # pragma: no cover - best-effort utility output
        console.print(f"[yellow]Warning:[/yellow] failed to load all demo data: {exc}")

    console.print("[bold green]pf Task Menu[/bold green]")
    if tui.categories:
        for category in tui.categories:
            console.print(f"  [cyan]{category.name}[/cyan]")
    else:
        console.print("  (no tasks found)")


if __name__ == "__main__":
    show_menu_screenshot()
