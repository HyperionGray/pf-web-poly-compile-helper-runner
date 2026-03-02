#!/usr/bin/env python3
"""
Measure rough per-invocation runtime overhead for an instrumented binary.

This is intentionally lightweight: it runs the binary N times and reports
aggregate timing. It does not attempt CPU pinning or statistical rigor.
"""

from __future__ import annotations

import argparse
import subprocess
import time
from pathlib import Path


def _input_bytes(value: str) -> bytes:
    candidate = Path(value).expanduser()
    if candidate.is_file():
        return candidate.read_bytes()
    if value == "-":
        return b""
    return value.encode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="Profile sanitizer overhead for a binary")
    parser.add_argument("binary", help="Path to binary to execute")
    parser.add_argument("test_input", help="Path to input file, '-', or a raw string")
    parser.add_argument("iterations", nargs="?", type=int, default=100, help="Number of iterations (default: 100)")
    args = parser.parse_args()

    binary = Path(args.binary).expanduser()
    if not binary.is_file():
        raise SystemExit(f"Binary not found: {binary}")

    data = _input_bytes(args.test_input)

    start = time.perf_counter()
    ok = 0
    for _ in range(max(1, args.iterations)):
        try:
            proc = subprocess.run(
                [str(binary)],
                input=data,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=False,
            )
            if proc.returncode == 0:
                ok += 1
        except subprocess.TimeoutExpired:
            pass
    end = time.perf_counter()

    total = end - start
    avg = total / max(1, args.iterations)
    print(f"Iterations: {args.iterations}")
    print(f"Successful exits: {ok}")
    print(f"Total time (s): {total:.6f}")
    print(f"Avg per run (s): {avg:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

