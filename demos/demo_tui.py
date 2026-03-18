#!/usr/bin/env python3
"""
Demo script to showcase TUI features non-interactively.
"""

from __future__ import annotations

import argparse
from typing import Any, Optional, Sequence

try:
    from demos.tui_common import ensure_runner_on_path, print_demo_banner, set_pfyfile_env
except ImportError:
    from tui_common import ensure_runner_on_path, print_demo_banner, set_pfyfile_env


# Optional imports: tests patch these symbols, so keep module importable even
# when optional runtime deps aren't installed.
try:
    ensure_runner_on_path()
    from pf_tui import PfTUI  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    PfTUI = Any  # type: ignore[misc,assignment]

try:
    from rich.console import Console  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    Console = Any  # type: ignore[misc,assignment]


def demo_tui(pfyfile: Optional[str] = None) -> int:
    """Demonstrate TUI capabilities."""
    set_pfyfile_env(pfyfile)
    console = Console()
    print_demo_banner(console, "pf TUI demo (non-interactive)")

    tui = PfTUI(pfyfile=pfyfile)

    console.print("[bold]1) Header display[/bold]")
    tui.show_header(subtitle_text="DEMO MODE")

    console.print("\n[bold]2) Loading tasks[/bold]")
    if not tui.load_tasks():
        console.print("[red]Failed to load tasks[/red]")
        return 1
    console.print(f"[green]Loaded {len(tui.tasks)} tasks[/green]")

    console.print("\n[bold]3) Categorizing tasks[/bold]")
    tui.categorize_tasks()
    console.print(f"[green]Organized into {len(tui.categories)} categories[/green]")

    console.print("\n[bold]4) Category summary[/bold]")
    for category in tui.categories:
        console.print(f"  - [cyan]{category.name}[/cyan]: {len(category.tasks)} tasks")

    console.print("\n[bold]5) Debugging tools view[/bold]")
    tui.show_debugging_tools()

    console.print("\n[dim]Run 'pf tui' for the interactive interface.[/dim]")
    return 0


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the non-interactive pf TUI demo.")
    parser.add_argument(
        "--file",
        dest="pfyfile",
        default=None,
        help="Optional Pfyfile path to load (sets PFY_FILE for this run).",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    return demo_tui(pfyfile=args.pfyfile)


if __name__ == "__main__":
    raise SystemExit(main())
