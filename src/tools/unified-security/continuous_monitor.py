#!/usr/bin/env python3
"""
Continuous Monitor
Performs periodic, lightweight checks against a target and saves a timeline.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def _is_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def _snapshot_target(target: str) -> Dict[str, Any]:
    snap: Dict[str, Any] = {"target": target, "timestamp": datetime.now().isoformat()}
    tpath = Path(target)

    if _is_url(target):
        try:
            req = urllib.request.Request(target, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                snap["type"] = "web"
                snap["status"] = resp.getcode()
                snap["headers"] = dict(resp.headers)
        except Exception as e:
            snap["type"] = "web"
            snap["error"] = str(e)
        return snap

    if tpath.exists() and tpath.is_file():
        st = tpath.stat()
        snap["type"] = "file"
        snap["path"] = str(tpath)
        snap["size"] = st.st_size
        snap["mtime"] = st.st_mtime
        return snap

    snap["type"] = "unknown"
    snap["error"] = "Target not found or unsupported"
    return snap


def main() -> int:
    parser = argparse.ArgumentParser(description="Run continuous monitoring against a target")
    parser.add_argument("--target", required=True, help="Target (URL or file path)")
    parser.add_argument("--interval", type=int, default=3600, help="Seconds between checks")
    parser.add_argument("--duration", type=int, default=86400, help="Total monitoring duration in seconds")
    parser.add_argument("--output", required=True, help="Output directory")
    args = parser.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    start = time.time()
    iterations = 0
    timeline_path = out_dir / "timeline.jsonl"

    print(f"🔄 Monitoring started: target={args.target} interval={args.interval}s duration={args.duration}s")

    try:
        while True:
            now = time.time()
            if now - start > args.duration:
                break

            snap = _snapshot_target(args.target)
            with open(timeline_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(snap) + "\n")

            iterations += 1
            remaining = (start + args.duration) - time.time()
            if remaining <= 0:
                break
            time.sleep(max(1, min(args.interval, int(remaining))))
    except KeyboardInterrupt:
        print("⏹️  Monitoring interrupted by user.")

    summary = {
        "analysis_type": "continuous_monitor",
        "generated_at": datetime.now().isoformat(),
        "target": args.target,
        "interval": args.interval,
        "duration": args.duration,
        "iterations": iterations,
        "timeline": str(timeline_path),
    }
    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"✅ Monitoring complete. Results in: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

