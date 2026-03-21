#!/usr/bin/env python3
"""Shared helpers for non-interactive TUI demo scripts."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def repo_root() -> Path:
    """Return the repository root from the demos directory."""
    return Path(__file__).resolve().parent.parent


def ensure_runner_on_path() -> Path:
    """
    Ensure pf runner module path is importable.

    Returns the selected runner directory.
    """
    root = repo_root()
    candidates = [root / "pf-runner-full", root / "pf-runner"]

    for candidate in candidates:
        if (candidate / "pf_tui.py").is_file():
            candidate_str = str(candidate)
            if candidate_str not in sys.path:
                sys.path.insert(0, candidate_str)
            return candidate

    raise FileNotFoundError(
        "Could not locate pf_tui.py in pf-runner-full/ or pf-runner/."
    )


def load_console_class() -> Any:
    """Import and return rich.console.Console."""
    from rich.console import Console

    return Console


def load_tui_class() -> Any:
    """Import and return pf_tui.PfTUI."""
    ensure_runner_on_path()
    from pf_tui import PfTUI

    return PfTUI


def print_demo_banner(console: Any, title: str) -> None:
    """Print a clear DEMO banner required by repository rules."""
    console.print("")
    console.print("=" * 72)
    console.print("                              DEMO MODE")
    console.print("=" * 72)
    console.print(title)
    console.print("=" * 72)


def build_tui_summary(tui: Any) -> Dict[str, Any]:
    """Build a serializable summary from a PfTUI instance."""
    categories: List[Dict[str, Any]] = []
    for category in getattr(tui, "categories", []):
        categories.append(
            {
                "name": str(getattr(category, "name", "")),
                "task_count": len(getattr(category, "tasks", [])),
            }
        )

    categories.sort(key=lambda item: item["name"].lower())
    return {
        "task_count": len(getattr(tui, "tasks", {})),
        "category_count": len(categories),
        "categories": categories,
    }


def write_summary_json(json_path: str, summary: Dict[str, Any]) -> None:
    """Persist TUI summary as pretty JSON."""
    destination = Path(json_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
