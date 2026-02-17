#!/usr/bin/env python3
import subprocess
import sys
import os
from pathlib import Path

repo_root = Path(os.environ.get("WORKSPACE", Path(__file__).resolve().parent.parent))
os.chdir(repo_root)
result = subprocess.run([sys.executable, 'tests/simple_syntax_validator.py'], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print("Return code:", result.returncode)
