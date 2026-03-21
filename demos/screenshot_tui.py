#!/usr/bin/env python3
"""Render a static, non-interactive menu snapshot for the pf TUI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Optional

PfTUI: Any = None
Console: Any = None

_RUNNER_CANDIDATES = ("pf-runner-full", "pf-runner")


def _resolve_runner_path(explicit_runner: Optional[str] = None) -> Path:
    """Resolve and add the pf runner path to sys.path."""
    demo_dir = Path(__file__).resolve().parent
    repo_root = demo_dir.parent

    candidates = []
    if explicit_runner:
        candidates.append(Path(explicit_runner))
    else:
        candidates.extend(repo_root / name for name in _RUNNER_CANDIDATES)

    for candidate in candidates:
        candidate = candidate.resolve()
        if (candidate / "pf_tui.py").exists():
            candidate_str = str(candidate)
            if candidate_str not in sys.path:
                sys.path.insert(0, candidate_str)
            return candidate

    looked_in = ", ".join(str(path.resolve()) for path in candidates)
    raise FileNotFoundError(f"Could not find pf_tui.py under: {looked_in}")


def _load_dependencies(explicit_runner: Optional[str] = None) -> Path:
    """Load runtime dependencies lazily so imports stay test-friendly."""
    global PfTUI, Console
    runner_path = _resolve_runner_path(explicit_runner)

    if Console is None:
        try:
            from rich.console import Console as rich_console  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover - environment-dependent
            raise RuntimeError("rich is required for TUI demos: pip install rich") from exc
        Console = rich_console

    if PfTUI is None:
        try:
            from pf_tui import PfTUI as pf_tui_class  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover - environment-dependent
            raise RuntimeError(f"pf_tui import failed from {runner_path}") from exc
        PfTUI = pf_tui_class

    return runner_path


def _print_demo_banner(console: Any, title: str) -> None:
    border = "=" * 72
    console.print(border)
    console.print("DEMO MODE")
    console.print(title)
    console.print(border)


def show_menu_screenshot(
    pfyfile: Optional[str] = None,
    runner_path: Optional[str] = None,
) -> int:
    """Render a static snapshot of the main TUI menu and category counts."""
    try:
        resolved_runner = _load_dependencies(runner_path)
    except Exception as exc:
        print(f"Error loading demo dependencies: {exc}", file=sys.stderr)
        return 1

    console = Console()
    _print_demo_banner(console, "pf TUI MENU SNAPSHOT")
    console.print(f"runner path: {resolved_runner}")
    if pfyfile:
        console.print(f"pfyfile: {pfyfile}")

    tui = PfTUI(pfyfile)
    if not tui.load_tasks():
        console.print("Failed to load tasks from the selected Pfyfile.")
        return 1
    tui.categorize_tasks()

    tui.show_header()
    console.print("\nMain Menu:")
    console.print("  [1] Browse Pfyfiles")
    console.print("  [2] All Tasks by Category")
    console.print("  [3] Search Tasks")
    console.print("  [4] Syntax Checker")
    console.print("  [5] Debugging Tools")
    console.print("  [6] Exploit Tools")
    console.print("  [q] Quit")

    console.print("\nCategory snapshot:")
    shown = 0
    for category in tui.categories[:8]:
        category_name = getattr(category, "name", "unknown")
        task_count = len(getattr(category, "tasks", []))
        shown += 1
        console.print(f"  {shown}. {category_name} ({task_count})")
    if len(tui.categories) > shown:
        console.print(f"  ... and {len(tui.categories) - shown} more categories")

    console.print(f"\nTotal tasks: {len(tui.tasks)}")
    console.print(f"Total categories: {len(tui.categories)}")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Render the pf TUI menu snapshot")
    parser.add_argument(
        "--file",
        dest="pfyfile",
        default=None,
        help="Optional Pfyfile path to load before rendering output",
    )
    parser.add_argument(
        "--runner-path",
        default=None,
        help="Optional path to pf runner directory containing pf_tui.py",
    )
    args = parser.parse_args(argv)
    return show_menu_screenshot(pfyfile=args.pfyfile, runner_path=args.runner_path)


if __name__ == "__main__":
    raise SystemExit(main())
