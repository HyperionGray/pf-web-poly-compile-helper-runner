#!/usr/bin/env python3
"""Lightweight binary analyzer stub."""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: binary_analyzer.py <binary> [--comprehensive]")
        return 1
    binary = sys.argv[1]
    root = Path(__file__).resolve().parents[2]
    checker = root / "tools" / "smart-workflows" / "unified_checksec.py"
    if not checker.exists():
        print(f"unified_checksec missing at {checker}", file=sys.stderr)
        return 1
    cmd = [sys.executable, str(checker), binary]
    cmd.extend(arg for arg in sys.argv[2:] if arg != "--comprehensive")
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
