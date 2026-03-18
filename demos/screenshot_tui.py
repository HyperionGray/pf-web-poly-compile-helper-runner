#!/usr/bin/env python3
"""
Script to render and optionally save a TUI snapshot.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Optional, Sequence

try:
    from demos.tui_common import ensure_runner_on_path, print_demo_banner, set_pfyfile_env
except ImportError:
    from tui_common import ensure_runner_on_path, print_demo_banner, set_pfyfile_env


try:
    ensure_runner_on_path()
    from pf_tui import PfTUI  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    PfTUI = Any  # type: ignore[misc,assignment]

try:
    from rich.console import Console  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    Console = Any  # type: ignore[misc,assignment]


def _build_snapshot_payload(tui) -> dict[str, Any]:
    categories = [
        {"name": category.name, "task_count": len(category.tasks)}
        for category in tui.categories
    ]
    return {
        "menu_options": [
            "1) List all tasks by category",
            "2) Run a task",
            "3) Check task syntax",
            "4) View debugging tools",
            "5) Search tasks",
            "6) Exploit development tools",
            "q) Quit",
        ],
        "total_tasks": len(tui.tasks),
        "total_categories": len(tui.categories),
        "categories": categories,
    }


def _render_text_snapshot(payload: dict[str, Any]) -> str:
    lines = [
        "pf TUI Snapshot (DEMO MODE)",
        "",
        "Main Menu:",
    ]
    lines.extend(f"  {option}" for option in payload["menu_options"])
    lines.append("")
    lines.append("Categories:")
    for index, category in enumerate(payload["categories"], start=1):
        lines.append(f"  {index}. {category['name']} ({category['task_count']} tasks)")
    lines.append("")
    lines.append(
        f"Totals: {payload['total_tasks']} tasks in {payload['total_categories']} categories"
    )
    return "\n".join(lines)


def _render_markdown_snapshot(payload: dict[str, Any]) -> str:
    lines = [
        "# pf TUI Snapshot (DEMO MODE)",
        "",
        "## Main Menu",
    ]
    lines.extend(f"- {option}" for option in payload["menu_options"])
    lines.append("")
    lines.append("## Categories")
    for category in payload["categories"]:
        lines.append(f"- **{category['name']}**: {category['task_count']} tasks")
    lines.append("")
    lines.append(
        f"**Totals:** {payload['total_tasks']} tasks in {payload['total_categories']} categories"
    )
    return "\n".join(lines)


def _serialize_snapshot(payload: dict[str, Any], fmt: str) -> str:
    if fmt == "json":
        return json.dumps(payload, indent=2, sort_keys=True)
    if fmt == "markdown":
        return _render_markdown_snapshot(payload)
    return _render_text_snapshot(payload)


def show_menu_screenshot(
    output_path: Optional[str] = None,
    snapshot_format: str = "text",
    pfyfile: Optional[str] = None,
) -> int:
    """Show a TUI menu snapshot and optionally write it to a file."""
    set_pfyfile_env(pfyfile)
    console = Console()
    print_demo_banner(console, "pf TUI snapshot renderer")

    tui = PfTUI(pfyfile=pfyfile)
    if not tui.load_tasks():
        console.print("[red]Failed to load tasks[/red]")
        return 1
    tui.categorize_tasks()
    tui.show_header(subtitle_text="DEMO SNAPSHOT")

    payload = _build_snapshot_payload(tui)
    rendered = _serialize_snapshot(payload, snapshot_format)

    console.print(rendered)
    if output_path:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered + "\n", encoding="utf-8")
        console.print(f"[green]Wrote snapshot to {target}[/green]")

    return 0


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a pf TUI snapshot for docs/previews."
    )
    parser.add_argument(
        "--output",
        dest="output",
        default=None,
        help="Optional file path to write the snapshot output.",
    )
    parser.add_argument(
        "--format",
        dest="snapshot_format",
        choices=("text", "markdown", "json"),
        default="text",
        help="Snapshot output format.",
    )
    parser.add_argument(
        "--file",
        dest="pfyfile",
        default=None,
        help="Optional Pfyfile path to load (sets PFY_FILE for this run).",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    return show_menu_screenshot(
        output_path=args.output,
        snapshot_format=args.snapshot_format,
        pfyfile=args.pfyfile,
    )


if __name__ == "__main__":
    raise SystemExit(main())
