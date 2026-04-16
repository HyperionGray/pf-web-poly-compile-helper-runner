#!/usr/bin/env python3
"""Report generator stub."""

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if "--output" in sys.argv:
        out_idx = sys.argv.index("--output")
        try:
            out_path = Path(sys.argv[out_idx + 1])
        except IndexError:
            print("--output requires a path", file=sys.stderr)
            return 1
        args = sys.argv[1:out_idx]
    else:
        out_path = Path("enhanced_report.json")
        args = sys.argv[1:]
    if not args:
        print("Usage: report_generator.py --target <path> [--output file]", file=sys.stderr)
        return 1
    target = args[1] if args[0] == "--target" else args[0]
    root = Path(__file__).resolve().parents[2]
    checker = root / "tools" / "smart-workflows" / "unified_checksec.py"
    if not checker.exists():
        print(f"unified_checksec missing at {checker}", file=sys.stderr)
        return 1
    proc = subprocess.run([sys.executable, str(checker), target, "--json"], capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        return proc.returncode
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = {"raw": proc.stdout}
    out_path.write_text(json.dumps(data, indent=2))
    print(f"Report written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
