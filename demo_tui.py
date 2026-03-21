#!/usr/bin/env python3
"""Compatibility shim for demos/demo_tui.py."""

from __future__ import annotations

import sys

from demos import demo_tui as _demo_impl

# Kept as module-level names so existing tests can patch these attributes.
PfTUI = _demo_impl.PfTUI
Console = _demo_impl.Console


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
