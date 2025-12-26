#!/usr/bin/env python3
"""
Final Test Execution - Run all tests three times as requested
"""

import os
import sys
import subprocess
import time

def main():
    """Execute the comprehensive test suite three times"""
    print("🎯 FINAL TEST EXECUTION")
    print("Testing it all again and again and again. That's thrice!")
    print("Nay ye canne deny it workes.")
    print("=" * 70)
    
    # Ensure we're in the right directory
    os.chdir('/workspace')
    
    # Make the comprehensive test runner executable
    if os.path.exists('test_all_comprehensive.py'):
        os.chmod('test_all_comprehensive.py', 0o755)
        print("✅ Made test_all_comprehensive.py executable")
    
    # Execute the comprehensive test runner
    print("\n🚀 Executing comprehensive test suite...")
    print("This will run all discovered tests three times with fresh environments.")
    print("")
    
    try:
        # Run the comprehensive test suite  
        print("🚀 Executing: python3 /workspace/test_all_comprehensive.py")
        result = subprocess.run([
            sys.executable, '/workspace/test_all_comprehensive.py'
        ], cwd='/workspace')
        
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