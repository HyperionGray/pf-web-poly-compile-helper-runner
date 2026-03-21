#!/usr/bin/env python3
"""Shared helpers for non-interactive TUI demo scripts."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


def _repo_root(start: Optional[Path] = None) -> Path:
    """Best-effort repository root discovery."""
    current = (start or Path(__file__).resolve()).parent
    while True:
        if (current / ".git").exists() or (current / "pf-files").exists():
            return current
        if current.parent == current:
            return Path.cwd()
        current = current.parent


def _runner_candidates(repo_root: Path) -> Tuple[Path, ...]:
    return (
        repo_root / "pf-runner-full",
        repo_root / "pf-runner",
        repo_root / "build-packages" / "pf-runner-1.0.0" / "pf-runner",
    )


def load_console_class():
    """Load rich Console lazily with a friendly error."""
    try:
        from rich.console import Console  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - runtime dependency
        raise RuntimeError(
            "rich is not installed; run: python3 -m pip install --user rich"
        ) from exc
    return Console


def load_pf_tui_class(repo_root: Optional[Path] = None):
    """Resolve and import PfTUI from an available runner directory."""
    root = repo_root or _repo_root()
    for candidate in _runner_candidates(root):
        pf_tui_path = candidate / "pf_tui.py"
        if not pf_tui_path.is_file():
            continue
        candidate_str = str(candidate)
        if candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)
        module = importlib.import_module("pf_tui")
        return module.PfTUI

    searched = ", ".join(str(path) for path in _runner_candidates(root))
    raise RuntimeError(f"Could not locate pf_tui.py. Searched: {searched}")


def load_tui_with_summary(
    pfyfile: Optional[str] = None,
    max_categories: int = 8,
) -> Tuple[Any, Dict[str, Any]]:
    """Load PfTUI and return `(tui_instance, summary_dict)`."""
    if max_categories < 1:
        raise ValueError("max_categories must be >= 1")

    PfTUI = load_pf_tui_class()
    tui = PfTUI(pfyfile)
    if not tui.load_tasks():
        raise RuntimeError("Unable to load tasks from Pfyfile")
    tui.categorize_tasks()

    categories = []
    for category in tui.categories[:max_categories]:
        categories.append(
            {
                "name": str(category.name),
                "task_count": len(category.tasks),
            }
        )

    summary: Dict[str, Any] = {
        "total_tasks": len(tui.tasks),
        "category_count": len(tui.categories),
        "categories": categories,
    }
    if len(tui.categories) > max_categories:
        summary["truncated_categories"] = len(tui.categories) - max_categories

    return tui, summary


def print_demo_banner(console: Any, title: str) -> None:
    """Print a large, plain DEMO banner for clarity."""
    bar = "=" * 70
    console.print(f"\n[bold yellow]{bar}[/bold yellow]")
    console.print("[bold yellow]DEMO MODE[/bold yellow]")
    console.print(f"[bold cyan]{title}[/bold cyan]")
    console.print(f"[bold yellow]{bar}[/bold yellow]\n")

