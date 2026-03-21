#!/usr/bin/env python3
"""
screenshot_tui.py - Screenshot/snapshot utility for the pf TUI menu

Canonical location: demos/screenshot_tui.py
"""

from __future__ import annotations

import os
import sys
from typing import Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
PF_RUNNER_FULL = os.path.join(REPO_ROOT, "pf-runner-full")
if PF_RUNNER_FULL not in sys.path:
    sys.path.insert(0, PF_RUNNER_FULL)

try:
    from rich.console import Console  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    Console = Any  # type: ignore[misc,assignment]

try:
    from pf_tui import PfTUI  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    PfTUI = Any  # type: ignore[misc,assignment]


def _print_demo_banner(console: Any) -> None:
    console.print("[bold yellow]" + "=" * 68 + "[/bold yellow]")
    console.print("[bold yellow] " + "DEMO SCREENSHOT MODE".center(66) + "[/bold yellow]")
    console.print("[bold yellow]" + "=" * 68 + "[/bold yellow]")


def show_menu_screenshot() -> None:
    """Render a static snapshot of the pf TUI task menu."""
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
