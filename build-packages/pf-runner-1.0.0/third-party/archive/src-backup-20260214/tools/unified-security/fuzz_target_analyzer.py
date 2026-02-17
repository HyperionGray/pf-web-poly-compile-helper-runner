#!/usr/bin/env python3
"""
Fuzz Target Analyzer
Analyzes a target (binary path or URL) and emits fuzzing target metadata.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


def _run(cmd: List[str]) -> Dict[str, Any]:
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        return {"ok": res.returncode == 0, "code": res.returncode, "stdout": res.stdout, "stderr": res.stderr}
    except Exception as e:
        return {"ok": False, "code": None, "stdout": "", "stderr": str(e)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze a target to prepare fuzzing inputs")
    parser.add_argument("target", help="Target to analyze (binary path, directory, or URL)")
    parser.add_argument("--output", required=True, help="Output JSON path")
    args = parser.parse_args()

    target = args.target
    tpath = Path(target)

    targets: List[Dict[str, Any]] = []
    if target.startswith(("http://", "https://")):
        targets.append({"id": "web_0", "type": "web", "url": target, "strategy": "http-parameter-fuzz"})
    elif tpath.exists() and tpath.is_file():
        file_info = _run(["file", str(tpath)])
        nm = _run(["nm", str(tpath)])
        parse_funcs: List[str] = []
        if nm.get("ok"):
            for line in str(nm.get("stdout", "")).splitlines():
                if " T " in line or " t " in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        name = parts[-1]
                        if any(k in name.lower() for k in ["parse", "read", "recv", "input", "process"]):
                            parse_funcs.append(name)
        targets.append(
            {
                "id": "bin_0",
                "type": "binary",
                "path": str(tpath),
                "strategy": "stdin-bytes",
                "file": file_info,
                "parse_functions": parse_funcs[:50],
            }
        )
    else:
        targets.append({"id": "unknown_0", "type": "unknown", "value": target, "strategy": "manual"})

    output = {
        "analysis_type": "fuzz_target_analysis",
        "generated_at": datetime.now().isoformat(),
        "input_target": target,
        "targets": targets,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"📁 Fuzz targets written: {out_path} (targets={len(targets)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

