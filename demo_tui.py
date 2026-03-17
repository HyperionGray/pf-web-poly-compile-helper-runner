#!/usr/bin/env python3
"""
demo_tui.py - Demo script for pf TUI (Text User Interface)

Demonstrates the PfTUI interface by loading tasks and showing
a summary of available task categories.
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


def demo_tui() -> None:
    """Run a brief demo of the pf TUI, showing task categories and counts."""
    console = Console()
    tui = PfTUI()

    try:
        tui.load_tasks()
        tui.categorize_tasks()
    except Exception:
        pass

    console.print("[bold blue]pf TUI Demo[/bold blue]")
    console.print(f"Loaded {len(tui.tasks)} tasks")
    if tui.categories:
        console.print(f"Categories: {', '.join(str(c.name) for c in tui.categories)}")


if __name__ == "__main__":
    demo_tui()
