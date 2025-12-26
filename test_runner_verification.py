#!/usr/bin/env python3
"""
Simple test to verify the comprehensive test runner functionality
"""

import sys
import os
import time

def test_basic_functionality():
    """Basic test that should always pass"""
    print("🧪 Running basic functionality test...")
    print("✅ Basic test passed!")
    return True

def test_with_output():
    """Test that produces some output"""
    print("🧪 Running test with output...")
    print("This is stdout output")
    print("Some more output lines")
    print("✅ Output test passed!")
    return True

def test_environment_variables():
    """Test that checks environment variables"""
    print("🧪 Testing environment variables...")
    
    # Check if we're in a fresh environment
    if 'PF_FRESH_ENV' in os.environ:
        print(f"✅ Fresh environment detected (run #{os.environ.get('PF_TEST_RUN', 'unknown')})")
    else:
        print("⚠️  No fresh environment marker found")
    
    # Check temp directory
    temp_dir = os.environ.get('TMPDIR', '/tmp')
    print(f"📁 Using temp directory: {temp_dir}")
    
    return True

def main():
    """Main test function"""
    print("🚀 Simple Test Runner Verification")
    print("=" * 40)
    
    tests = [
        test_basic_functionality,
        test_with_output,
        test_environment_variables
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_func.__name__} failed")
        except Exception as e:
            print(f"💥 {test_func.__name__} error: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All verification tests passed!")
        return 0
    else:
        print("❌ Some verification tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())