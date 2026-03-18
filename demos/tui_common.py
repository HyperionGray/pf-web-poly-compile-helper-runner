#!/usr/bin/env python3
"""
Shared helpers for TUI demo/snapshot scripts.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable


_RUNNER_DIR_CANDIDATES: tuple[str, ...] = (
    "pf-runner-full",
    "pf-runner",
    "build-packages/pf-runner-1.0.0/pf-runner",
)


def _walk_parents(start: Path) -> Iterable[Path]:
    current = start.resolve()
    while True:
        yield current
        if current.parent == current:
            break
        current = current.parent


def find_repo_root(start: Path | None = None) -> Path:
    """
    Find repository root by locating a directory containing '.git'.
    Falls back to the parent of this file's directory.
    """
    start_dir = (start or Path(__file__)).resolve()
    if start_dir.is_file():
        start_dir = start_dir.parent

    for directory in _walk_parents(start_dir):
        if (directory / ".git").exists():
            return directory

    # Fallback: demos/ lives one level below repository root.
    return Path(__file__).resolve().parent.parent


def find_runner_dir(repo_root: Path | None = None) -> Path:
    """Locate directory containing pf_tui.py."""
    root = (repo_root or find_repo_root()).resolve()
    for rel_path in _RUNNER_DIR_CANDIDATES:
        candidate = root / rel_path
        if (candidate / "pf_tui.py").is_file():
            return candidate
    searched = ", ".join(str(root / rel) for rel in _RUNNER_DIR_CANDIDATES)
    raise FileNotFoundError(f"Could not find pf_tui.py. Searched: {searched}")


def ensure_runner_on_path() -> Path:
    """Add the runner directory to sys.path (if missing) and return it."""
    runner_dir = find_runner_dir()
    runner_path = str(runner_dir)
    if runner_path not in sys.path:
        sys.path.insert(0, runner_path)
    return runner_dir


def print_demo_banner(console, title: str) -> None:
    """
    Print a prominent banner so demo runs are clearly marked.
    """
    line = "=" * 72
    console.print(f"[bold yellow]{line}[/bold yellow]")
    console.print("[bold yellow]DEMO MODE[/bold yellow]")
    console.print(f"[bold yellow]{title}[/bold yellow]")
    console.print(f"[bold yellow]{line}[/bold yellow]")
    console.print()


def set_pfyfile_env(pfyfile: str | None) -> None:
    """Set PFY_FILE only when explicitly provided."""
    if pfyfile:
        os.environ["PFY_FILE"] = pfyfile
