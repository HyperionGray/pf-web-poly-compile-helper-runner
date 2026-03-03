#!/usr/bin/env python3
"""
Quick fix for pfy shlex import error.

This script patches the pfy installation to add the missing shlex import.
Run this if you encounter: "NameError: name 'shlex' is not defined" when using pf commands.

Usage:
    python scripts/patch_pfy_shlex.py
"""

import sys
import os
from pathlib import Path


def find_pf_main():
    """Find the pf_main.py file in the pfy installation."""
    common_paths = [
        "/usr/local/lib/pf-runner/pf_main.py",
        "/usr/lib/pf-runner/pf_main.py",
        Path.home() / ".local/lib/pf-runner/pf_main.py",
    ]
    
    for path in common_paths:
        path = Path(path)
        if path.exists():
            return path
    
    return None


def check_if_shlex_imported(content):
    """Check if shlex is already imported."""
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('import shlex') or line.startswith('from shlex '):
            return True
    return False


def patch_file(file_path):
    """Add shlex import to the file if it's missing."""
    try:
        content = file_path.read_text()
        
        if check_if_shlex_imported(content):
            print(f"[ok] {file_path} already has shlex imported")
            return True
        
        # Find a good place to add the import (after other imports)
        lines = content.split('\n')
        import_index = 0
        
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                import_index = i + 1
        
        # Insert the import
        lines.insert(import_index, 'import shlex')
        new_content = '\n'.join(lines)
        
        # Create backup
        backup_path = file_path.with_suffix('.py.backup')
        file_path.rename(backup_path)
        print(f"[ok] Created backup: {backup_path}")
        
        # Write patched file
        file_path.write_text(new_content)
        print(f"[ok] Patched {file_path} - added 'import shlex'")
        
        return True
        
    except PermissionError:
        print("[fail] Permission denied. Try running with sudo:")
        print(f"  sudo python3 {__file__}")
        return False
    except Exception as e:
        print(f"[fail] Error patching file: {e}")
        return False


def main():
    print("Pfy Shlex Import Patcher")
    print("=" * 40)
    
    pf_main = find_pf_main()
    
    if not pf_main:
        print("[fail] Could not find pf_main.py")
        print("\nSearched locations:")
        print("  - /usr/local/lib/pf-runner/pf_main.py")
        print("  - /usr/lib/pf-runner/pf_main.py")
        print(f"  - {Path.home()}/.local/lib/pf-runner/pf_main.py")
        print("\nIf pfy is installed elsewhere, please patch manually by adding:")
        print("  import shlex")
        print("at the top of pf_main.py with the other imports.")
        return 1
    
    print(f"Found pf_main.py: {pf_main}")
    
    if patch_file(pf_main):
        print("\n[ok] Patch completed successfully")
        print("You can now run pf commands normally.")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
