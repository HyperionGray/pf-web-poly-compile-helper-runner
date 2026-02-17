#!/usr/bin/env python3
"""
Execute the comprehensive test suite - "Test it all again and again and again. That's thrice."
"""

import subprocess
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

def main():
    """Execute the comprehensive test suite"""
    print("🎯 EXECUTING COMPREHENSIVE TEST SUITE")
    print("Testing it all again and again and again. That's thrice!")
    print("=" * 70)
    
    repo_root_path = repo_root()
    os.chdir(repo_root_path)
    
    # Make sure scripts are executable
    scripts_to_make_executable = [
        'test_all_comprehensive.py',
        'test_runner_verification.py', 
        'run_tests.sh',
        'quick_verify.sh'
    ]
    
    for script in scripts_to_make_executable:
        script_path = repo_root_path / script
        if script_path.exists():
            os.chmod(script_path, 0o755)
    
    print("🚀 Starting comprehensive test execution...")
    print("")
    
    # Run the comprehensive test suite
    try:
        result = subprocess.run([
            sys.executable, str(repo_root_path / 'test_all_comprehensive.py')
        ], cwd=repo_root_path)
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💥 Error executing tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
