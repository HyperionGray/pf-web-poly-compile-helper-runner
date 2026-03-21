#!/usr/bin/env python3
"""
demo_tui.py - Demo script for pf TUI (Text User Interface)

Canonical location: demos/demo_tui.py
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

# Optional imports: keep module importable in minimal environments.
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
    console.print("[bold yellow] " + "DEMO MODE".center(66) + "[/bold yellow]")
    console.print("[bold yellow]" + "=" * 68 + "[/bold yellow]")


def demo_tui() -> None:
    """Run a brief demo of the pf TUI, showing task categories and counts."""
    console = Console()
    _print_demo_banner(console)

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
