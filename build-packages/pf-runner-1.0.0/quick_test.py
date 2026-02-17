#!/usr/bin/env python3

"""Quick parser smoke-test for a minimal Pfyfile."""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent
PF_RUNNER_PATH = REPO_ROOT / "pf-runner"
SAMPLE_PF = REPO_ROOT / "tests" / "fixtures" / "simple_test.pf"

if PF_RUNNER_PATH.exists():
    sys.path.insert(0, str(PF_RUNNER_PATH))

from pf_parser import parse_pfyfile_text  # type: ignore  # injected path above

content = SAMPLE_PF.read_text(encoding="utf-8")

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
