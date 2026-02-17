#!/usr/bin/env python3
"""
Risk-Focused Testing
Takes a previously generated unified report and prioritizes the highest-risk findings.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def _severity_rank(sev: str) -> int:
    order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
    return order.get((sev or "").lower(), 0)


def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Focus testing on highest-risk unified report findings")
    parser.add_argument("--previous-report", required=True, help="Path to the previous report JSON")
    parser.add_argument("--depth", default="deep", help="Focus depth (shallow|medium|deep)")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    report_path = Path(args.previous_report)
    if not report_path.exists():
        raise SystemExit(f"Report not found: {report_path}")

    report = _load_json(str(report_path))
    findings: List[Dict[str, Any]] = list(report.get("detailed_findings", []) or [])

    focused = [
        f
        for f in findings
        if _severity_rank(str(f.get("severity", ""))) >= _severity_rank("high")
        or int(f.get("risk_score", 0) or 0) >= 7
    ]

    focused.sort(
        key=lambda f: (
            -_severity_rank(str(f.get("severity", ""))),
            -(int(f.get("risk_score", 0) or 0)),
        )
    )

    by_target: Dict[str, int] = {}
    for f in focused:
        tgt = str(f.get("target", "unknown"))
        by_target[tgt] = by_target.get(tgt, 0) + 1

    output = {
        "analysis_type": "risk_focused_testing",
        "generated_at": datetime.now().isoformat(),
        "source_report": str(report_path),
        "depth": args.depth,
        "total_findings": len(findings),
        "focused_findings": focused,
        "summary": {
            "focused_count": len(focused),
            "by_target": by_target,
            "critical_count": sum(1 for f in focused if str(f.get("severity", "")).lower() == "critical"),
            "high_count": sum(1 for f in focused if str(f.get("severity", "")).lower() == "high"),
        },
        "recommended_next_steps": [
            "Review the focused findings (sorted by severity then risk_score).",
            "For binary targets: run `pf exploit-develop-smart binary=<path>`.",
            "For web targets: rerun targeted testing against the affected endpoint(s).",
            "Capture evidence and reproduce crashes deterministically before exploitation.",
        ],
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"✅ Focused testing report written: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

