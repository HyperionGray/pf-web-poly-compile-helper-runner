#!/usr/bin/env python3
"""Compatibility shim for demos/screenshot_tui.py."""

from __future__ import annotations

import sys

from demos import screenshot_tui as _shot_impl

# Kept as module-level names so existing tests can patch these attributes.
PfTUI = _shot_impl.PfTUI
Console = _shot_impl.Console


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
