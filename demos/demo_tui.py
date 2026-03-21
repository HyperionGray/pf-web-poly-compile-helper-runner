#!/usr/bin/env python3
"""
Canonical demo_tui script location.

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
except ImportError:  # pragma: no cover
    Console = Any  # type: ignore[misc,assignment]

try:
    from pf_tui import PfTUI
except ImportError:  # pragma: no cover
    PfTUI = Any  # type: ignore[misc,assignment]


def _print_demo_banner(console: Any) -> None:
    console.print("")
    console.print("[bold yellow]============================[/bold yellow]")
    console.print("[bold yellow]==== DEMO MODE: PF TUI ======[/bold yellow]")
    console.print("[bold yellow]============================[/bold yellow]")


def demo_tui() -> None:
    """Run a brief non-interactive demo of the pf TUI."""
    console = Console()
    _print_demo_banner(console)

    tui = PfTUI()
    try:
        tui.load_tasks()
        tui.categorize_tasks()
    except Exception:
        # Keep demo output stable even in partial environments.
        pass

    console.print("[bold blue]pf TUI Demo[/bold blue]")
    console.print(f"Loaded {len(tui.tasks)} tasks")
    if tui.categories:
        console.print(f"Categories: {', '.join(str(c.name) for c in tui.categories)}")


if __name__ == "__main__":
    demo_tui()
