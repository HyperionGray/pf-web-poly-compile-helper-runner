#!/usr/bin/env python3
"""
Canonical screenshot_tui script location.

This script intentionally lives under demos/ to keep demo-only code out of the
repo root and away from production paths.
"""

import os
import sys
from typing import Any

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PF_RUNNER_FULL = os.path.join(REPO_ROOT, "pf-runner-full")
if PF_RUNNER_FULL not in sys.path:
    sys.path.insert(0, PF_RUNNER_FULL)

try:
    from rich.console import Console
except BaseException:  # pragma: no cover
    Console = None  # type: ignore[misc,assignment]

if Console is not None:
    try:
        from pf_tui import PfTUI
    except BaseException:  # pragma: no cover
        PfTUI = None  # type: ignore[misc,assignment]
else:  # pragma: no cover
    PfTUI = None  # type: ignore[misc,assignment]


def _print_demo_banner(console: Any) -> None:
    console.print("")
    console.print("[bold yellow]============================[/bold yellow]")
    console.print("[bold yellow]==== DEMO SNAPSHOT MODE ====[/bold yellow]")
    console.print("[bold yellow]============================[/bold yellow]")


def show_menu_screenshot() -> None:
    """Render a static snapshot of the pf TUI task menu."""
    if Console is None or PfTUI is None:
        print(
            "Error: demo dependencies are not installed. Install with: pip install 'pf-runner[tui]'",
            file=sys.stderr,
        )
        return

    console = Console()
    _print_demo_banner(console)

    tui = PfTUI()
    try:
        tui.load_tasks()
        tui.categorize_tasks()
        tui.show_header()
    except Exception:
        pass

    console.print("[bold green]pf Task Menu[/bold green]")
    if tui.categories:
        for category in tui.categories:
            console.print(f"  [cyan]{category.name}[/cyan]")
    else:
        console.print("  (no tasks found)")


if __name__ == "__main__":
    show_menu_screenshot()
