#!/usr/bin/env python3
"""
Execute the comprehensive test suite - "Test it all again and again and again. That's thrice."
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Execute the comprehensive test suite"""
    print("🎯 EXECUTING COMPREHENSIVE TEST SUITE")
    print("Testing it all again and again and again. That's thrice!")
    print("=" * 70)
    
    # Change to repository root (directory containing this script)
    repo_root = Path(__file__).resolve().parent
    os.chdir(repo_root)
    
    # Make sure scripts are executable
    scripts_to_make_executable = [
        'test_all_comprehensive.py',
        'test_runner_verification.py', 
        'run_tests.sh',
        'quick_verify.sh'
    ]
    
    for script in scripts_to_make_executable:
        if os.path.exists(script):
            os.chmod(script, 0o755)
    
    print("🚀 Starting comprehensive test execution...")
    print("")
    
    # Run the comprehensive test suite
    try:
        runner_path = repo_root / "test_all_comprehensive.py"
        result = subprocess.run([
            sys.executable, str(runner_path)
        ], cwd=repo_root)
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Error executing tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
