#!/usr/bin/env python3
"""
Crash Triager
Consumes fuzzing results JSON and produces a crash triage summary.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Triage crashes from fuzzing results")
    parser.add_argument("--results", required=True, help="Fuzzing results JSON")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    results_path = Path(args.results)
    if not results_path.exists():
        raise SystemExit(f"Results file not found: {results_path}")

    results: Dict[str, Any] = _load_json(str(results_path)) or {}
    crashes = int(results.get("crashes", 0) or 0)
    unique = int(results.get("unique_crashes", 0) or 0)

    output = {
        "analysis_type": "crash_triage",
        "generated_at": datetime.now().isoformat(),
        "input_results": str(results_path),
        "summary": {
            "crashes": crashes,
            "unique_crashes": unique,
            "triage_status": "none" if crashes == 0 else "requires_attention",
        },
        "recommendations": (
            [
                "Minimize and deduplicate crashing inputs.",
                "Reproduce with ASAN/UBSAN enabled and collect stack traces.",
                "Symbolize traces and file issues with repro steps.",
            ]
            if crashes
            else ["No crashes reported; consider increasing duration or improving input generation."]
        ),
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"📊 Crash triage written: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

