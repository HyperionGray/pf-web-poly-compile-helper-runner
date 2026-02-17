#!/usr/bin/env python3
"""
Simple corpus runner for sanitizer-assisted fuzzing.

This is not a full fuzzer. It repeatedly feeds corpus inputs to a target binary
for a bounded amount of time and records crashes (non-zero exit or timeout).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a binary over a corpus with sanitizer instrumentation enabled")
    parser.add_argument("--sanitizer", required=True, help="Sanitizer name (asan/msan/ubsan/tsan)")
    parser.add_argument("--binary", required=True, help="Path to instrumented binary")
    parser.add_argument("--corpus", required=True, help="Corpus directory (files will be fed via stdin)")
    parser.add_argument("--timeout", type=int, default=3600, help="Total run time limit in seconds (default: 3600)")
    parser.add_argument("--per-run-timeout", type=float, default=2.0, help="Timeout per input in seconds (default: 2)")
    parser.add_argument("--crash-dir", default="crashes", help="Directory to write crash artifacts (default: crashes)")
    args = parser.parse_args()

    binary = Path(args.binary).expanduser()
    corpus_dir = Path(args.corpus).expanduser()
    crash_dir = Path(args.crash_dir).expanduser()

    if not binary.is_file():
        raise SystemExit(f"Binary not found: {binary}")

    corpus_dir.mkdir(parents=True, exist_ok=True)
    crash_dir.mkdir(parents=True, exist_ok=True)

    corpus_files = sorted([p for p in corpus_dir.iterdir() if p.is_file()])
    if not corpus_files:
        (corpus_dir / "README.txt").write_text(
            "Place sample inputs in this directory; fuzz_with_sanitizer.py will feed them to the target via stdin.\n",
            encoding="utf-8",
        )
        print(f"No corpus files found in {corpus_dir}. Added README.txt.")
        return 0

    start = time.time()
    cases = 0
    crashes = 0
    crash_artifacts = []

    i = 0
    while time.time() - start < max(1, args.timeout):
        inp = corpus_files[i % len(corpus_files)]
        i += 1
        cases += 1

        try:
            data = inp.read_bytes()
        except Exception:
            continue

        try:
            proc = subprocess.run(
                [str(binary)],
                input=data,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=args.per_run_timeout,
                check=False,
            )
            rc = proc.returncode
            timed_out = False
        except subprocess.TimeoutExpired as e:
            rc = -1
            timed_out = True
            proc = None

        if timed_out or rc != 0:
            crashes += 1
            stamp = int(time.time() * 1000)
            base = crash_dir / f"crash_{stamp}"
            input_path = base.with_suffix(".input")
            input_path.write_bytes(data)

            meta = {
                "sanitizer": args.sanitizer,
                "binary": str(binary),
                "input": str(inp),
                "stored_input": str(input_path),
                "returncode": rc,
                "timed_out": timed_out,
            }
            if proc is not None:
                (base.with_suffix(".stdout")).write_bytes(proc.stdout)
                (base.with_suffix(".stderr")).write_bytes(proc.stderr)
                meta["stdout"] = str(base.with_suffix(".stdout"))
                meta["stderr"] = str(base.with_suffix(".stderr"))

            meta_path = base.with_suffix(".json")
            meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            crash_artifacts.append(str(meta_path))

    summary = {
        "sanitizer": args.sanitizer,
        "binary": str(binary),
        "corpus": str(corpus_dir),
        "duration_sec": time.time() - start,
        "cases": cases,
        "crashes": crashes,
        "crash_artifacts": crash_artifacts[:200],
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

