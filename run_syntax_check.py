#!/usr/bin/env python3
import subprocess
import sys
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
os.chdir(REPO_ROOT)

result = subprocess.run(
    [sys.executable, str(REPO_ROOT / 'simple_syntax_validator.py')],
    capture_output=True,
    text=True,
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print("Return code:", result.returncode)
