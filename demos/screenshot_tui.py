#!/usr/bin/env python3
"""Render a static, non-interactive TUI menu snapshot."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from demos.tui_common import (
    load_console_class,
    load_tui_with_summary,
    print_demo_banner,
)


def show_menu_screenshot(
    pfyfile: Optional[str] = None,
    max_categories: int = 8,
    summary_json: bool = False,
) -> int:
    """Render a static menu snapshot suitable for docs/screenshots."""
    try:
        Console = load_console_class()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    console = Console()
    print_demo_banner(console, "pf TUI Menu Snapshot")

    try:
        tui, summary = load_tui_with_summary(
            pfyfile=pfyfile, max_categories=max_categories
        )
    except Exception as exc:
        console.print(f"[red]Failed to build TUI snapshot: {exc}[/red]")
        return 1

    if summary_json:
        console.print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    tui.show_header("DEMO MODE - static menu snapshot")
    console.print("\n[bold cyan]Main Menu[/bold cyan]")
    console.print("  [1] Browse Pfyfiles")
    console.print("  [2] All Tasks by Category")
    console.print("  [3] Search Tasks")
    console.print("  [4] Syntax Checker")
    console.print("  [5] Debugging Tools")
    console.print("  [6] Exploit Tools")
    console.print("  [q] Quit")

    console.print("\n[bold]Category Summary[/bold]")
    for index, item in enumerate(summary["categories"], start=1):
        console.print(f"  {index}. {item['name']} ({item['task_count']} tasks)")

    if "truncated_categories" in summary:
        console.print(
            f"  ... and {summary['truncated_categories']} more categories"
        )

    console.print(
        f"\n[bold]Total:[/bold] {summary['total_tasks']} tasks "
        f"in {summary['category_count']} categories"
    )
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entrypoint for screenshot script."""
    parser = argparse.ArgumentParser(description="Render a static pf TUI snapshot")
    parser.add_argument(
        "--pfyfile",
        help="Optional Pfyfile path to load instead of auto-discovery",
    )
    parser.add_argument(
        "--max-categories",
        type=int,
        default=8,
        help="Maximum categories to include in output",
    )
    parser.add_argument(
        "--summary-json",
        action="store_true",
        help="Print machine-readable summary JSON",
    )
    args = parser.parse_args(argv)
    return show_menu_screenshot(
        pfyfile=args.pfyfile,
        max_categories=args.max_categories,
        summary_json=args.summary_json,
    )


if __name__ == "__main__":
    raise SystemExit(main())
