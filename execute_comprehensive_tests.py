#!/usr/bin/env python3
"""
FINAL EXECUTION - Test it all again and again and again. That's thrice!
"""

import os
import sys
from pathlib import Path

# Resolve repository root relative to this script
repo_root = Path(__file__).resolve().parent
os.chdir(repo_root)

# Make the comprehensive test runner executable
os.chmod(repo_root / 'test_all_comprehensive.py', 0o755)

print("🎯 FINAL TEST EXECUTION")
print("Testing it all again and again and again. That's thrice!")
print("Nay ye canne deny it workes.")
print("=" * 70)
print()

# Import and run the comprehensive test runner directly
sys.path.insert(0, str(repo_root))

try:
    from test_all_comprehensive import ComprehensiveTestRunner
    
    runner = ComprehensiveTestRunner()
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
    result = subprocess.run([sys.executable, str(repo_root / 'test_all_comprehensive.py')])
    sys.exit(result.returncode)
