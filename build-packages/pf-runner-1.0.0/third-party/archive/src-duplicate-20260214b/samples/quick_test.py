#!/usr/bin/env python3
"""
Parse a tiny sample Pfyfile and print the parsed tasks.

Kept path-agnostic so it works after the repo restructure.
"""

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent

sys.path.insert(0, str(REPO_ROOT / "pf-runner"))

from pf_parser import parse_pfyfile_text  # type: ignore


def main() -> int:
    pf_path = HERE / "simple_test.pf"
    content = pf_path.read_text(encoding="utf-8")

    print("=== Original content ===")
    print(content)

    print("\n=== Parsed tasks ===")
    tasks = parse_pfyfile_text(content)

    for task_name, task in tasks.items():
        print(f"\nTask: {task_name}")
        print(f"Description: {task.description}")
        print(f"Lines ({len(task.lines)}):")
        for i, line in enumerate(task.lines, 1):
            print(f"  {i}: {line}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
