#!/usr/bin/env python3
"""
demo_tui.py - Small demo for the pf TUI.

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


def demo_tui() -> None:
    """Run a tiny, non-interactive TUI demo."""
    console = Console()
    tui = PfTUI()
    tui.load_tasks()
    tui.categorize_tasks()
    tui.show_header()
    console.print(f"\nLoaded {len(getattr(tui, 'tasks', []))} tasks in {len(getattr(tui, 'categories', []))} categories")


if __name__ == "__main__":
    demo_tui()

