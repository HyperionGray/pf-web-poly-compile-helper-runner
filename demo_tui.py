#!/usr/bin/env python3
"""Compatibility shim for demos/demo_tui.py."""

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


def demo_tui() -> None:
    """Run the canonical TUI demo flow using patchable module symbols."""
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
    print("Note: demo_tui.py moved to demos/demo_tui.py", file=sys.stderr)
    demo_tui()
