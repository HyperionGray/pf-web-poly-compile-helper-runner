#!/usr/bin/env python3
"""Final Test Execution - Run all tests three times as requested."""

import os
import sys
import subprocess
import time
from pathlib import Path


def repo_root() -> Path:
    for env_var in ("PF_WORKSPACE", "WORKSPACE"):
        env_path = os.environ.get(env_var)
        if env_path:
            candidate = Path(env_path).expanduser()
            if candidate.exists():
                return candidate
    return Path(__file__).resolve().parent


def main():
    """Execute the comprehensive test suite three times."""
    print("🎯 FINAL TEST EXECUTION")
    print("Testing it all again and again and again. That's thrice!")
    print("Nay ye canne deny it workes.")
    print("=" * 70)
    
    repo_root_path = repo_root()
    test_runner = repo_root_path / 'test_all_comprehensive.py'

    # Ensure we're in the right directory
    os.chdir(repo_root_path)
    
    # Make the comprehensive test runner executable
    if test_runner.exists():
        os.chmod(test_runner, 0o755)
        print("✅ Made test_all_comprehensive.py executable")
    
    # Execute the comprehensive test runner
    print("\n🚀 Executing comprehensive test suite...")
    print("This will run all discovered tests three times with fresh environments.")
    print("")
    
    try:
        # Run the comprehensive test suite  
        print(f"🚀 Executing: python3 {test_runner}")
        result = subprocess.run([
            sys.executable, str(test_runner)
        ], cwd=repo_root_path)
        
        print(f"\n🏁 Test execution completed with exit code: {result.returncode}")
        
        if result.returncode == 0:
            print("🎉 SUCCESS: All tests completed successfully!")
            print("✅ Nay ye canne deny it workes!")
        else:
            print("⚠️  Some tests had issues. Check the detailed report above.")
        
        return result.returncode
        
    except subprocess.TimeoutExpired:
        print("\n⏰ Test execution timed out")
        return 124
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Error executing tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\n🏁 Final exit code: {exit_code}")
    sys.exit(exit_code)
