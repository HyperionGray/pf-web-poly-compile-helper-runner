import py_compile
import sys
import os
from pathlib import Path


def repo_root() -> Path:
    """Resolve the repository root without assuming /workspace."""
    for env_var in ("PF_WORKSPACE", "WORKSPACE"):
        env_path = os.environ.get(env_var)
        if env_path:
            candidate = Path(env_path).expanduser()
            if candidate.exists():
                return candidate
    return Path(__file__).resolve().parent


REPO_ROOT = repo_root()
PF_RUNNER_DIR = REPO_ROOT / "pf-runner"
PF_POLYGLOT_PATH = PF_RUNNER_DIR / "pf_polyglot.py"

if not PF_POLYGLOT_PATH.exists():
    raise FileNotFoundError(f"pf_polyglot.py not found at expected location: {PF_POLYGLOT_PATH}")

# Test syntax compilation
try:
    py_compile.compile(str(PF_POLYGLOT_PATH), doraise=True)
    print("SUCCESS: pf_polyglot.py syntax is valid")
except py_compile.PyCompileError as e:
    print(f"ERROR: Syntax error in pf_polyglot.py: {e}")
    sys.exit(1)

# Test basic import
sys.path.insert(0, str(PF_RUNNER_DIR))
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
