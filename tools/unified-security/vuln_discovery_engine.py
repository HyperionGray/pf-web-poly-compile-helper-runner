#!/usr/bin/env python3
"""
Vulnerability Discovery Engine
Lightweight vulnerability discovery from a binary and its prior analysis JSON.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _strings(binary: Path) -> str:
    try:
        res = subprocess.run(["strings", str(binary)], capture_output=True, text=True)
        if res.returncode != 0:
            return ""
        return res.stdout
    except Exception:
        return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover likely vulnerabilities from a binary")
    parser.add_argument("--binary", required=True, help="Binary path")
    parser.add_argument("--analysis", required=True, help="Input analysis JSON (from exploit_target_analyzer)")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    binary_path = Path(args.binary)
    if not binary_path.exists():
        raise SystemExit(f"Binary not found: {binary_path}")

    analysis: Dict[str, Any] = {}
    analysis_path = Path(args.analysis)
    if analysis_path.exists():
        analysis = _load_json(str(analysis_path)) or {}

    s = _strings(binary_path)

    vulns: List[Dict[str, Any]] = []
    if any(tok in s for tok in ["strcpy", "strcat", "sprintf", "gets"]):
        vulns.append(
            {
                "type": "buffer_overflow",
                "severity": "high",
                "description": "Dangerous C string functions detected in binary strings",
            }
        )
    if any(tok in s for tok in ["%n", "%x", "%p", "%s"]):
        vulns.append(
            {
                "type": "format_string",
                "severity": "medium",
                "description": "Potential format string patterns detected in binary strings",
            }
        )
    if any(tok in s for tok in ["system(", "popen(", "exec", "/bin/sh"]):
        vulns.append(
            {
                "type": "command_injection",
                "severity": "high",
                "description": "Command execution indicators detected in binary strings",
            }
        )

    output: Dict[str, Any] = {
        "analysis_type": "vulnerability_discovery",
        "generated_at": datetime.now().isoformat(),
        "binary": str(binary_path),
        "input_analysis": str(analysis_path),
        "vulnerabilities": vulns,
        "notes": [
            "This is heuristic-only discovery (strings-based).",
            "Confirm with dynamic analysis and coverage-guided fuzzing before exploitation.",
        ],
        "analysis_excerpt": {
            "checksec_ok": bool((analysis.get("checksec") or {}).get("ok", False)),
            "function_count": int(((analysis.get("functions") or {}).get("count")) or 0),
        },
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"📁 Vulnerabilities written: {out_path} (count={len(vulns)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

