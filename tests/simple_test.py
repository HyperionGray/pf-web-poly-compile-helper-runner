import py_compile
import sys
import os

# Test syntax compilation
try:
    py_compile.compile('/workspace/pf-runner/pf_polyglot.py', doraise=True)
    print("SUCCESS: pf_polyglot.py syntax is valid")
except py_compile.PyCompileError as e:
    print(f"ERROR: Syntax error in pf_polyglot.py: {e}")
    sys.exit(1)

# Test basic import
sys.path.insert(0, '/workspace/pf-runner')
try:
    import pf_polyglot
    print("SUCCESS: pf_polyglot.py imports successfully")
    
    # Test basic functionality
    langs = pf_polyglot.get_supported_languages()
    print(f"SUCCESS: Found {len(langs)} supported languages")
    
    aliases = pf_polyglot.get_language_aliases()
    print(f"SUCCESS: Found {len(aliases)} language aliases")
    
    is_python_supported = pf_polyglot.is_supported_language("python")
    print(f"SUCCESS: Python support check: {is_python_supported}")
    
except Exception as e:
    print(f"ERROR: Failed to import or test pf_polyglot.py: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("All tests passed!")