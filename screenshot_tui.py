#!/usr/bin/env python3
"""
screenshot_tui.py - Script to print a TUI menu snapshot.

Tests patch `PfTUI` and `Console`, so keep this module lightweight and importable.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


# Ensure pf-runner modules are importable when running from repo root.
REPO_ROOT = Path(__file__).resolve().parent
PF_RUNNER_DIR = REPO_ROOT / "pf-runner"
if str(PF_RUNNER_DIR) not in sys.path:
    sys.path.insert(0, str(PF_RUNNER_DIR))


try:
    from pf_tui import PfTUI  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    PfTUI = Any  # type: ignore[misc,assignment]

try:
    from rich.console import Console  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    Console = Any  # type: ignore[misc,assignment]


def show_menu_screenshot() -> None:
    """Print a menu-like view that can be used for docs/screenshots."""
    console = Console()

    tui = PfTUI()
    tui.load_tasks()
    tui.categorize_tasks()
    tui.show_header()

    console.print("\n[bold cyan]Main Menu:[/bold cyan]")
    console.print("  [1] List all tasks by category")
    console.print("  [2] Run a task")
    console.print("  [3] Check task syntax")
    console.print("  [4] View debugging tools")
    console.print("  [5] Search tasks")
    console.print("  [q] Quit")

    console.print(f"\n[bold]Total:[/bold] {len(getattr(tui, 'tasks', []))} tasks in {len(getattr(tui, 'categories', []))} categories")


if __name__ == "__main__":
    show_menu_screenshot()

