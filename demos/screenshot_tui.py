#!/usr/bin/env python3
"""Render a static TUI menu snapshot for docs and demos."""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

try:
    from demos.tui_demo_utils import (
        build_tui_summary,
        load_console_class,
        load_tui_class,
        print_demo_banner,
        write_summary_json,
    )
except ModuleNotFoundError:
    # Support direct execution: `python3 demos/screenshot_tui.py`
    from tui_demo_utils import (  # type: ignore[no-redef]
        build_tui_summary,
        load_console_class,
        load_tui_class,
        print_demo_banner,
        write_summary_json,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for snapshot mode."""
    parser = argparse.ArgumentParser(
        description="Render a static pf TUI menu snapshot (non-interactive)."
    )
    parser.add_argument(
        "--pfyfile",
        default=None,
        help="Optional Pfyfile path to load instead of auto-discovery.",
    )
    parser.add_argument(
        "--max-categories",
        type=int,
        default=8,
        help="Maximum number of categories to print in the snapshot.",
    )
    parser.add_argument(
        "--json-out",
        default=None,
        help="Optional JSON output path for machine-readable summary.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on loading/categorization errors.",
    )
    return parser


def show_menu_screenshot(
    pfyfile: Optional[str] = None,
    max_categories: int = 8,
    json_out: Optional[str] = None,
    strict: bool = False,
) -> int:
    """Render static menu text plus category summary."""
    try:
        console = load_console_class()()
    except Exception as exc:
        print(f"Error: could not load rich Console: {exc}", file=sys.stderr)
        return 1

    print_demo_banner(console, "pf TUI menu snapshot")

    try:
        tui = load_tui_class()(pfyfile)
    except Exception as exc:
        console.print(f"[red]Error: could not initialize PfTUI: {exc}[/red]")
        return 1

    load_ok = bool(tui.load_tasks())
    if not load_ok and strict:
        console.print("[red]Error: no tasks were loaded.[/red]")
        return 1

    try:
        tui.categorize_tasks()
    except Exception as exc:
        console.print(f"[yellow]Warning: categorization failed: {exc}[/yellow]")
        if strict:
            return 1

    tui.show_header()
    console.print("\n[bold cyan]Main Menu:[/bold cyan]")
    console.print("  [1] Browse Pfyfiles")
    console.print("  [2] All Tasks by Category")
    console.print("  [3] Search Tasks")
    console.print("  [4] Syntax Checker")
    console.print("  [5] Debugging Tools")
    console.print("  [6] Exploit Tools")
    console.print("  [q] Quit")

    summary = build_tui_summary(tui)
    console.print("\n[bold yellow]Task Categories:[/bold yellow]")
    limit = max(0, int(max_categories))
    shown = summary["categories"][:limit]
    for index, category in enumerate(shown, start=1):
        console.print(f"  {index}. {category['name']} ({category['task_count']} tasks)")
    remaining = summary["category_count"] - len(shown)
    if remaining > 0:
        console.print(f"  ... and {remaining} more categories")

    console.print(
        f"\n[bold]Total:[/bold] {summary['task_count']} tasks in "
        f"{summary['category_count']} categories"
    )
    if json_out:
        write_summary_json(json_out, summary)
        console.print(f"[green]Wrote JSON summary to {json_out}[/green]")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entrypoint."""
    args = build_parser().parse_args(argv)
    return show_menu_screenshot(
        pfyfile=args.pfyfile,
        max_categories=args.max_categories,
        json_out=args.json_out,
        strict=args.strict,
    )


if __name__ == "__main__":
    raise SystemExit(main())
