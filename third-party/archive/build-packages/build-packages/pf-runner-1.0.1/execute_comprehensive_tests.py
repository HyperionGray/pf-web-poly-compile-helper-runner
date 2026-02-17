#!/usr/bin/env python3
"""FINAL EXECUTION - Test it all again and again and again. That's thrice!"""

import os
import sys
from pathlib import Path


def repo_root() -> Path:
    for env_var in ("PF_WORKSPACE", "WORKSPACE"):
        env_path = os.environ.get(env_var)
        if env_path:
            candidate = Path(env_path).expanduser()
            if candidate.exists():
                return candidate
    return Path(__file__).resolve().parent


REPO_ROOT = repo_root()
TEST_RUNNER = REPO_ROOT / "test_all_comprehensive.py"

# Ensure we're in the workspace
os.chdir(REPO_ROOT)

# Make the comprehensive test runner executable
if TEST_RUNNER.exists():
    os.chmod(TEST_RUNNER, 0o755)

print("🎯 FINAL TEST EXECUTION")
print("Testing it all again and again and again. That's thrice!")
print("Nay ye canne deny it workes.")
print("=" * 70)
print()

# Import and run the comprehensive test runner directly
sys.path.insert(0, str(REPO_ROOT))

try:
    from test_all_comprehensive import ComprehensiveTestRunner
    
    runner = ComprehensiveTestRunner(workspace_dir=str(REPO_ROOT))
    success = runner.run_all_tests_thrice()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("✅ Nay ye canne deny it workes!")
    else:
        print("⚠️  Some tests had issues - check the detailed report above")
    print("=" * 70)
    
    sys.exit(0 if success else 1)
    
except Exception as e:
    print(f"💥 Error: {e}")
    print("\nFalling back to subprocess execution...")
    
    # Fallback to subprocess
    import subprocess
    result = subprocess.run([sys.executable, str(TEST_RUNNER)], cwd=REPO_ROOT)
    sys.exit(result.returncode)
