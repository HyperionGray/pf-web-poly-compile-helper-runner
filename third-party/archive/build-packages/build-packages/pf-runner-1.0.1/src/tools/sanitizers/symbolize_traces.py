#!/usr/bin/env python3
"""
Sanitizer trace symbolizer (best-effort).

For now, this is a lightweight passthrough that preserves logs and provides a
place to add llvm-symbolizer / addr2line integration later.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Symbolize sanitizer stack traces (best-effort)")
    parser.add_argument("binary", help="Path to the instrumented binary (used for symbolization)")
    parser.add_argument("log_file", help="Path to sanitizer log file")
    parser.add_argument(
        "output",
        nargs="?",
        default="symbolized.log",
        help="Output path (default: symbolized.log)",
    )
    args = parser.parse_args()

    log_path = Path(args.log_file).expanduser()
    if not log_path.is_file():
        raise SystemExit(f"Log file not found: {log_path}")

    out_path = Path(args.output).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Best-effort: preserve the log verbatim for now.
    out_path.write_text(log_path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")

    print(f"Wrote: {out_path}")
    print("Note: symbolization is currently best-effort (verbatim copy).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

