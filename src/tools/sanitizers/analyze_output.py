#!/usr/bin/env python3
"""
Sanitizer output analyzer (lightweight).

Generates a small HTML report and a JSON summary from a sanitizer log file.
Intended to be safe to run locally and used by `pf sanitizer-analyze`.
"""

from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path


def _count_markers(text: str) -> dict:
    markers = {
        "ERROR:": 0,
        "WARNING:": 0,
        "runtime error:": 0,
        "AddressSanitizer": 0,
        "UndefinedBehaviorSanitizer": 0,
        "MemorySanitizer": 0,
        "ThreadSanitizer": 0,
    }
    for k in list(markers.keys()):
        markers[k] = text.count(k)
    return markers


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze sanitizer log output and generate a report")
    parser.add_argument("log_file", help="Path to sanitizer log file")
    parser.add_argument(
        "output",
        nargs="?",
        default="sanitizer_report.html",
        help="Output HTML report path (default: sanitizer_report.html)",
    )
    args = parser.parse_args()

    log_path = Path(args.log_file).expanduser()
    if not log_path.is_file():
        raise SystemExit(f"Log file not found: {log_path}")

    text = log_path.read_text(encoding="utf-8", errors="replace")
    counts = _count_markers(text)
    excerpt_lines = text.splitlines()[:400]
    excerpt = "\n".join(excerpt_lines)

    out_path = Path(args.output).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()

    summary = {
        "generated_at": now,
        "log_file": str(log_path),
        "output": str(out_path),
        "counts": counts,
        "excerpt_lines": len(excerpt_lines),
    }

    report_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Sanitizer Report</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; padding: 16px; }}
    code, pre {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 8px; }}
    .card {{ border: 1px solid #ddd; border-radius: 8px; padding: 12px; }}
    .k {{ color: #555; font-size: 12px; }}
    .v {{ font-size: 20px; font-weight: 700; }}
    pre {{ background: #0b1020; color: #e8eefc; padding: 12px; border-radius: 8px; overflow-x: auto; }}
  </style>
</head>
<body>
  <h1>Sanitizer Report</h1>
  <p><b>Generated:</b> {html.escape(now)} (UTC)</p>
  <p><b>Log:</b> <code>{html.escape(str(log_path))}</code></p>

  <h2>Counts</h2>
  <div class="grid">
    {''.join(f'<div class="card"><div class="k">{html.escape(k)}</div><div class="v">{v}</div></div>' for k, v in counts.items())}
  </div>

  <h2>Excerpt (first {len(excerpt_lines)} lines)</h2>
  <pre>{html.escape(excerpt)}</pre>

  <hr />
  <p><i>Tip:</i> For deep symbolization, use <code>pf sanitizer-symbolize</code>.</p>
</body>
</html>
"""

    out_path.write_text(report_html, encoding="utf-8")
    out_json = out_path.with_suffix(".json")
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Wrote report: {out_path}")
    print(f"Wrote summary: {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

