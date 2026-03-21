#!/usr/bin/env python3
"""Non-interactive TUI demo with optional JSON summary output."""

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


def demo_tui(
    pfyfile: Optional[str] = None,
    max_categories: int = 8,
    summary_json: bool = False,
) -> int:
    """Render a non-interactive TUI overview."""
    try:
        Console = load_console_class()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    console = Console()

    try:
        tui, summary = load_tui_with_summary(
            pfyfile=pfyfile, max_categories=max_categories
        )
    except Exception as exc:
        console.print(f"[red]Failed to build TUI summary: {exc}[/red]")
        return 1

    if summary_json:
        console.print(json.dumps(summary, indent=2, sort_keys=True))
        return 0

    print_demo_banner(console, "pf TUI Demo (non-interactive)")
    tui.show_header("DEMO MODE - non-interactive overview")
    console.print("[bold]Summary[/bold]")
    console.print(f"  total tasks: {summary['total_tasks']}")
    console.print(f"  categories:  {summary['category_count']}")

    if summary["categories"]:
        console.print("\n[bold]Top categories[/bold]")
        for item in summary["categories"]:
            console.print(f"  - {item['name']}: {item['task_count']} tasks")

    if "truncated_categories" in summary:
        console.print(
            f"\n[dim]... {summary['truncated_categories']} additional categories hidden "
            f"(use --max-categories to show more).[/dim]"
        )

    console.print("\n[dim]Run full interactive mode with: pf tui[/dim]")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entrypoint for demo script."""
    parser = argparse.ArgumentParser(description="Render a non-interactive pf TUI demo")
    parser.add_argument(
        "--pfyfile",
        help="Optional Pfyfile path to load instead of auto-discovery",
    )
    parser.add_argument(
        "--max-categories",
        type=int,
        default=8,
        help="Maximum categories to display in summary output",
    )
    parser.add_argument(
        "--summary-json",
        action="store_true",
        help="Print machine-readable summary JSON instead of human output",
    )
    args = parser.parse_args(argv)
    return demo_tui(
        pfyfile=args.pfyfile,
        max_categories=args.max_categories,
        summary_json=args.summary_json,
    )


if __name__ == "__main__":
    raise SystemExit(main())
