#!/usr/bin/env python3
"""Non-interactive DEMO overview for the pf TUI.

This is the canonical location for the demo script. Root-level wrappers keep
backward compatibility for existing commands (`python3 demo_tui.py`).
"""

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


def demo_tui(
    pfyfile: Optional[str] = None,
    runner_path: Optional[str] = None,
) -> int:
    """Run a non-interactive summary of TUI-discovered tasks/categories."""
    try:
        resolved_runner = _load_dependencies(runner_path)
    except Exception as exc:
        print(f"Error loading demo dependencies: {exc}", file=sys.stderr)
        return 1

    console = Console()
    _print_demo_banner(console, "pf TUI NON-INTERACTIVE SUMMARY")
    console.print(f"runner path: {resolved_runner}")
    if pfyfile:
        console.print(f"pfyfile: {pfyfile}")

    tui = PfTUI(pfyfile)
    if not tui.load_tasks():
        console.print("Failed to load tasks from the selected Pfyfile.")
        return 1

    tui.categorize_tasks()
    total_tasks = len(tui.tasks)
    total_categories = len(tui.categories)
    console.print(f"loaded tasks: {total_tasks}")
    console.print(f"categories: {total_categories}")

    if tui.categories:
        console.print("\nTop categories:")
        for category in tui.categories[:10]:
            category_name = getattr(category, "name", "unknown")
            task_count = len(getattr(category, "tasks", []))
            console.print(f"  - {category_name}: {task_count}")

    console.print("\nRun 'pf tui' for the interactive interface.")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the pf TUI demo summary")
    parser.add_argument(
        "--file",
        dest="pfyfile",
        default=None,
        help="Optional Pfyfile path to load before summarizing tasks",
    )
    parser.add_argument(
        "--runner-path",
        default=None,
        help="Optional path to pf runner directory containing pf_tui.py",
    )
    args = parser.parse_args(argv)
    return demo_tui(pfyfile=args.pfyfile, runner_path=args.runner_path)


if __name__ == "__main__":
    raise SystemExit(main())
