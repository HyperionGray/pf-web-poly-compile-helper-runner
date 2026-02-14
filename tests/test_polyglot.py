#!/usr/bin/env python3
"""
Test script to verify pf_polyglot.py syntax and imports
"""

import sys
import os

# Add pf-runner to path
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
pf_runner_path = os.path.join(repo_root, 'pf-runner')
sys.path.insert(0, pf_runner_path)

def test_syntax():
    """Test that pf_polyglot.py has valid syntax"""
    try:
        import py_compile
        polyglot_file = os.path.join(pf_runner_path, 'pf_polyglot.py')
        py_compile.compile(polyglot_file, doraise=True)
        print("✅ Syntax check passed")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Syntax error: {e}")
        return False

def test_imports():
    """Test that pf_polyglot.py can be imported"""
    try:
        import pf_polyglot
        print("✅ Import successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during import: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality of the module"""
    try:
        import pf_polyglot
        
        # Test getting supported languages
        langs = pf_polyglot.get_supported_languages()
        print(f"✅ Found {len(langs)} supported languages")
        
        # Test language aliases
        aliases = pf_polyglot.get_language_aliases()
        print(f"✅ Found {len(aliases)} language aliases")
        
        # Test language support check
        is_python_supported = pf_polyglot.is_supported_language("python")
        print(f"✅ Python support check: {is_python_supported}")
        
        return True
    except Exception as e:
        print(f"❌ Functionality test error: {e}")
        return False

if __name__ == "__main__":
    print("Testing pf_polyglot.py...")
    
    success = True
    success &= test_syntax()
    success &= test_imports()
    success &= test_basic_functionality()
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)