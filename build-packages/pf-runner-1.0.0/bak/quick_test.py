#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, 'pf-runner')

from pf_parser import parse_pfyfile_text

# Read the test file
with open('simple_test.pf', 'r') as f:
    content = f.read()

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