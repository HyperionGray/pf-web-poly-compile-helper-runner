#!/usr/bin/env python3
"""
demo_tui.py - Demo script for pf TUI (Text User Interface).

Demonstrates the PfTUI interface by loading tasks and showing a summary of
available task categories.
"""

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNNER_DIR = os.path.join(ROOT_DIR, "pf-runner-full")
if RUNNER_DIR not in sys.path:
    sys.path.insert(0, RUNNER_DIR)

# Populated lazily so importing this module does not require optional deps.
Console = None
PfTUI = None


def _ensure_dependencies() -> None:
    """Load optional demo dependencies on demand."""
    global Console, PfTUI
    if Console is not None and PfTUI is not None:
        return

    from rich.console import Console as RichConsole
    from pf_tui import PfTUI as PfTUIClass

    Console = RichConsole
    PfTUI = PfTUIClass


def _print_demo_banner(console) -> None:
    """Print a prominent banner for demo-only runs."""
    line = "=" * 64
    console.print(f"[bold yellow]{line}[/bold yellow]")
    console.print("[bold yellow]DEMO MODE - NON-PRODUCTION OUTPUT[/bold yellow]")
    console.print(f"[bold yellow]{line}[/bold yellow]")


def demo_tui() -> int:
    """Run a brief demo of the pf TUI, showing task categories and counts."""
    try:
        _ensure_dependencies()
    except ImportError:
        print(
            "Error: demo dependencies missing. Install with: pip install rich",
            file=sys.stderr,
        )
        return 1

    console = Console()
    tui = PfTUI()

    _print_demo_banner(console)

    try:
        tui.load_tasks()
        tui.categorize_tasks()
    except Exception as exc:  # pragma: no cover - best-effort utility output
        console.print(f"[yellow]Warning:[/yellow] failed to load all demo data: {exc}")

    console.print("[bold blue]pf TUI Demo[/bold blue]")
    console.print(f"Loaded {len(tui.tasks)} tasks")
    if tui.categories:
        console.print(f"Categories: {', '.join(str(c.name) for c in tui.categories)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(demo_tui())
