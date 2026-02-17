#!/usr/bin/env python3
"""
Compare two sanitizer log files and generate a small HTML diff report.
"""

from __future__ import annotations

import argparse
import difflib
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare sanitizer logs and generate an HTML diff")
    parser.add_argument("baseline_log", help="Baseline log file")
    parser.add_argument("current_log", help="Current log file")
    parser.add_argument(
        "output",
        nargs="?",
        default="comparison.html",
        help="Output HTML file (default: comparison.html)",
    )
    args = parser.parse_args()

    baseline = Path(args.baseline_log).expanduser()
    current = Path(args.current_log).expanduser()
    if not baseline.is_file():
        raise SystemExit(f"Baseline log not found: {baseline}")
    if not current.is_file():
        raise SystemExit(f"Current log not found: {current}")

    baseline_lines = baseline.read_text(encoding="utf-8", errors="replace").splitlines()
    current_lines = current.read_text(encoding="utf-8", errors="replace").splitlines()

    diff = difflib.HtmlDiff(tabsize=4, wrapcolumn=120)
    html_report = diff.make_file(
        baseline_lines,
        current_lines,
        fromdesc=str(baseline),
        todesc=str(current),
        context=True,
        numlines=3,
    )

    out_path = Path(args.output).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_report, encoding="utf-8")
    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

