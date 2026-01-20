#!/usr/bin/env python3
"""
Test script to validate the sync_workflows.py script syntax and basic functionality.
"""

import sys
import os

def test_import():
    """Test that the script can be imported without syntax errors."""
    try:
        import sync_workflows
        print("✅ sync_workflows.py imports successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing sync_workflows.py: {e}")
        return False

def test_help():
    """Test that the script shows help without errors."""
    try:
        # Save original argv
        original_argv = sys.argv.copy()
        
        # Set argv to show help
        sys.argv = ['sync_workflows.py', '--help']
        
        try:
            import sync_workflows
            sync_workflows.main()
        except SystemExit as e:
            # Help should exit with code 0
            if e.code == 0:
                print("✅ Help command works correctly")
                return True
            else:
                print(f"❌ Help command exited with code {e.code}")
                return False
        
    except Exception as e:
        print(f"❌ Error testing help: {e}")
        return False
    finally:
        # Restore original argv
        sys.argv = original_argv

def test_dry_run():
    """Test dry run functionality."""
    if not os.environ.get('GITHUB_TOKEN'):
        print("⚠️  Skipping dry run test - no GITHUB_TOKEN set")
        return True
    
    try:
        # Save original argv
        original_argv = sys.argv.copy()
        
        # Set argv for dry run
        sys.argv = ['sync_workflows.py', 'P4X-ng', '--dry-run']
        
        try:
            import sync_workflows
            sync_workflows.main()
            print("✅ Dry run completed successfully")
            return True
        except SystemExit as e:
            if e.code == 0:
                print("✅ Dry run completed successfully")
                return True
            else:
                print(f"❌ Dry run failed with exit code {e.code}")
                return False
        
    except Exception as e:
        print(f"❌ Error testing dry run: {e}")
        return False
    finally:
        # Restore original argv
        sys.argv = original_argv

def main():
    """Run all tests."""
    print("🧪 Testing sync_workflows.py script...")
    print()
    
    tests = [
        ("Import test", test_import),
        ("Help test", test_help),
        ("Dry run test", test_dry_run),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())