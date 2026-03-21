#!/usr/bin/env python3
"""Compatibility shim for demos/screenshot_tui.py."""

from __future__ import annotations

import os
import sys
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "pf-runner-full"))

try:
    from rich.console import Console  # type: ignore[import-not-found]
except BaseException:  # pragma: no cover
    Console = Any  # type: ignore[misc,assignment]

try:
    from pf_tui import PfTUI  # type: ignore[import-not-found]
except BaseException:  # pragma: no cover
    PfTUI = Any  # type: ignore[misc,assignment]


def show_menu_screenshot() -> None:
    """Run the canonical TUI screenshot demo using patchable symbols."""
    console = Console()
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
    print("Note: screenshot_tui.py moved to demos/screenshot_tui.py", file=sys.stderr)
    show_menu_screenshot()
