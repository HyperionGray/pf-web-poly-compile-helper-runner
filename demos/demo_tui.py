#!/usr/bin/env python3
"""Non-interactive pf TUI demo with optional JSON summary export."""

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
    # Support direct execution: `python3 demos/demo_tui.py`
    from tui_demo_utils import (  # type: ignore[no-redef]
        build_tui_summary,
        load_console_class,
        load_tui_class,
        print_demo_banner,
        write_summary_json,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for the demo script."""
    parser = argparse.ArgumentParser(
        description="Run a non-interactive pf TUI demo and print a task summary."
    )
    parser.add_argument(
        "--pfyfile",
        default=None,
        help="Optional Pfyfile path to load instead of auto-discovery.",
    )
    parser.add_argument(
        "--max-categories",
        type=int,
        default=12,
        help="Maximum number of category rows to print.",
    )
    parser.add_argument(
        "--json-out",
        default=None,
        help="Optional JSON output path for machine-readable summary.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero status if task loading or categorization fails.",
    )
    return parser


def demo_tui(
    pfyfile: Optional[str] = None,
    max_categories: int = 12,
    json_out: Optional[str] = None,
    strict: bool = False,
) -> int:
    """Run the non-interactive demo."""
    try:
        console = load_console_class()()
    except Exception as exc:
        print(f"Error: could not load rich Console: {exc}", file=sys.stderr)
        return 1

    print_demo_banner(console, "pf TUI demo summary")

    try:
        tui = load_tui_class()(pfyfile)
    except Exception as exc:
        console.print(f"[red]Error: could not initialize PfTUI: {exc}[/red]")
        return 1

    load_ok = bool(tui.load_tasks())
    if not load_ok:
        console.print("[yellow]Warning: no tasks were loaded.[/yellow]")
        if strict:
            return 1

    try:
        tui.categorize_tasks()
    except Exception as exc:
        console.print(f"[yellow]Warning: categorization failed: {exc}[/yellow]")
        if strict:
            return 1

    summary = build_tui_summary(tui)
    console.print(
        f"[bold]Loaded {summary['task_count']} tasks across "
        f"{summary['category_count']} categories.[/bold]"
    )

    limit = max(0, int(max_categories))
    shown = summary["categories"][:limit]
    for category in shown:
        console.print(f"  - {category['name']}: {category['task_count']} tasks")
    remaining = summary["category_count"] - len(shown)
    if remaining > 0:
        console.print(f"  ... {remaining} more categories")

    if json_out:
        write_summary_json(json_out, summary)
        console.print(f"[green]Wrote JSON summary to {json_out}[/green]")

    console.print("[dim]Use `pf tui` for the full interactive interface.[/dim]")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entrypoint."""
    args = build_parser().parse_args(argv)
    return demo_tui(
        pfyfile=args.pfyfile,
        max_categories=args.max_categories,
        json_out=args.json_out,
        strict=args.strict,
    )


if __name__ == "__main__":
    raise SystemExit(main())
