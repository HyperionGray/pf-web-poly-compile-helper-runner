#!/usr/bin/env python3
"""
Execute the comprehensive test suite - "Test it all again and again and again. That's thrice."
"""

import subprocess
import sys
import os

def main():
    """Execute the comprehensive test suite"""
    print("🎯 EXECUTING COMPREHENSIVE TEST SUITE")
    print("Testing it all again and again and again. That's thrice!")
    print("=" * 70)
    
    # Change to workspace directory
    os.chdir('/workspace')
    
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
        result = subprocess.run([
            sys.executable, 'test_all_comprehensive.py'
        ], cwd='/workspace')
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Error executing tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())