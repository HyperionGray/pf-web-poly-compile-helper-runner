#!/usr/bin/env python3
"""
Demo script to showcase TUI features non-interactively.

Kept at repo root for compatibility with tests and quick manual runs.
"""

from __future__ import annotations

import os
import sys

# Add pf-runner to path (relative to this script's location)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PF_RUNNER_PATH = os.path.join(_SCRIPT_DIR, "pf-runner")
sys.path.insert(0, _PF_RUNNER_PATH)

from pf_tui import PfTUI  # pylint: disable=import-error
from rich.console import Console  # pylint: disable=import-error


def demo_tui() -> None:
    """Demonstrate TUI capabilities."""
    console = Console()

    console.print("\n[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]           pf TUI Demo - Non-Interactive Mode           [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]\n")

    tui = PfTUI()

    console.print("[bold]1. Header Display:[/bold]")
    tui.show_header()

    console.print("\n[bold]2. Loading Tasks:[/bold]")
    if tui.load_tasks():
        console.print(f"[green]✓ Successfully loaded {len(tui.tasks)} tasks[/green]")
    else:
        console.print("[red]✗ Failed to load tasks[/red]")
        return

    console.print("\n[bold]3. Categorizing Tasks:[/bold]")
    tui.categorize_tasks()
    console.print(f"[green]✓ Organized into {len(tui.categories)} categories[/green]")

    console.print("\n[bold]4. Category Summary:[/bold]")
    for category in tui.categories:
        console.print(f"  • [cyan]{category.name}[/cyan]: {len(category.tasks)} tasks")

    console.print("\n[bold]5. Debugging Tools View:[/bold]")
    tui.show_debugging_tools()

    console.print("\n[bold]6. Exploit Development Categories:[/bold]")
    exploit_categories = [
        cat
        for cat in tui.categories
        if "exploit" in cat.name.lower()
        or "pwn" in cat.name.lower()
        or "rop" in cat.name.lower()
        or "heap" in cat.name.lower()
    ]

    for category in exploit_categories:
        console.print(f"\n[bold {category.color}]{category.name}[/bold {category.color}] ({len(category.tasks)} tasks)")
        for task_name, _ in category.tasks[:3]:
            console.print(f"  • [cyan]{task_name}[/cyan]")
        if len(category.tasks) > 3:
            console.print(f"  ... and {len(category.tasks) - 3} more")

    console.print("\n[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold green]✓ Demo completed successfully![/bold green]")
    console.print("[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]\n")

    console.print("[dim]To run the full interactive TUI, use: pf tui[/dim]")
    console.print("[dim]To access exploit dev tools, select option 6 in the TUI[/dim]\n")


if __name__ == "__main__":
    demo_tui()
