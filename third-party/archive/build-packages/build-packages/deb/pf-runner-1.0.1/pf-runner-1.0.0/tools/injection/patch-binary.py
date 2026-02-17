#!/usr/bin/env python3
"""
Binary patching tool for injecting shared libraries into ELF binaries.
This tool modifies the binary to load a specified shared library.
"""

import sys
import os
import struct
import subprocess
from pathlib import Path

try:
    import lief
    LIEF_AVAILABLE = True
except ImportError:
    LIEF_AVAILABLE = False

def patch_with_lief(binary_path, library_path):
    """Patch binary using LIEF library (preferred method)"""
    if not LIEF_AVAILABLE:
        raise ImportError("LIEF library not available")
    
    print(f"Patching {binary_path} to load {library_path} using LIEF...")
    
    # Parse the binary
    binary = lief.parse(binary_path)
    if not binary:
        raise ValueError(f"Failed to parse binary: {binary_path}")
    
    # Add the library as a dependency
    library_name = os.path.basename(library_path)
    binary.add_library(library_name)
    
    # Write the patched binary
    binary.write(binary_path)
    print(f"Successfully patched binary to load {library_name}")

def patch_with_patchelf(binary_path, library_path):
    """Patch binary using patchelf (Linux fallback)"""
    print(f"Patching {binary_path} to load {library_path} using patchelf...")
    
    # Check if patchelf is available
    try:
        subprocess.run(['patchelf', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError("patchelf not found. Install with: sudo apt-get install patchelf")
    
    # Get absolute path of library
    abs_library_path = os.path.abspath(library_path)
    
    # Add the library as a needed dependency
    try:
        subprocess.run([
            'patchelf', 
            '--add-needed', 
            abs_library_path, 
            binary_path
        ], check=True)
        print(f"Successfully added {abs_library_path} as dependency")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"patchelf failed: {e}")

def patch_with_dd(binary_path, library_path):
    """Simple binary patching using dd (basic fallback)"""
    print(f"Warning: Using basic dd-based patching for {binary_path}")
    print("This method has limited compatibility and may not work for all binaries")
    
    # This is a very basic approach - in practice, proper ELF manipulation is needed
    # We'll create a simple LD_PRELOAD wrapper script instead
    
    wrapper_path = binary_path + "_injected_wrapper"
    
    with open(wrapper_path, 'w') as f:
        f.write(f"""#!/bin/bash
# Auto-generated injection wrapper
export LD_PRELOAD="{os.path.abspath(library_path)}:$LD_PRELOAD"
exec "{os.path.abspath(binary_path)}" "$@"
""")
    
    os.chmod(wrapper_path, 0o755)
    print(f"Created injection wrapper: {wrapper_path}")
    print(f"Run with: {wrapper_path}")

def analyze_binary(binary_path):
    """Analyze binary to determine best patching method"""
    print(f"Analyzing {binary_path}...")
    
    # Check if it's an ELF binary
    try:
        with open(binary_path, 'rb') as f:
            magic = f.read(4)
            if magic != b'\x7fELF':
                print("Warning: Not an ELF binary")
                return False
    except IOError:
        print(f"Error: Cannot read {binary_path}")
        return False
    
    # Check file permissions
    if not os.access(binary_path, os.W_OK):
        print("Warning: Binary is not writable")
        return False
    
    # Get basic info
    try:
        result = subprocess.run(['file', binary_path], capture_output=True, text=True)
        print(f"File type: {result.stdout.strip()}")
    except:
        pass
    
    try:
        result = subprocess.run(['ldd', binary_path], capture_output=True, text=True)
        print("Current dependencies:")
        for line in result.stdout.strip().split('\n')[:5]:  # Show first 5 deps
            print(f"  {line}")
        if len(result.stdout.strip().split('\n')) > 5:
            print("  ...")
    except:
        print("Could not analyze dependencies")
    
    return True

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 patch-binary.py <binary_path> <library_path>")
        print("")
        print("This tool patches a binary to load a specified shared library.")
        print("The library will be loaded when the binary starts.")
        print("")
        print("Examples:")
        print("  python3 patch-binary.py ./myapp ./payload.so")
        print("  python3 patch-binary.py /usr/bin/program /tmp/injected.so")
        sys.exit(1)
    
    binary_path = sys.argv[1]
    library_path = sys.argv[2]
    
    # Validate inputs
    if not os.path.exists(binary_path):
        print(f"Error: Binary not found: {binary_path}")
        sys.exit(1)
    
    if not os.path.exists(library_path):
        print(f"Error: Library not found: {library_path}")
        sys.exit(1)
    
    # Analyze the binary
    if not analyze_binary(binary_path):
        print("Binary analysis failed")
        sys.exit(1)
    
    # Try patching methods in order of preference
    methods = [
        ("LIEF", patch_with_lief),
        ("patchelf", patch_with_patchelf),
        ("wrapper script", patch_with_dd)
    ]
    
    for method_name, method_func in methods:
        try:
            print(f"\nTrying {method_name} method...")
            method_func(binary_path, library_path)
            print(f"Success! Binary patched using {method_name}")
            break
        except Exception as e:
            print(f"{method_name} method failed: {e}")
            continue
    else:
        print("All patching methods failed!")
        sys.exit(1)
    
    print("\nPatching completed successfully!")
    print(f"The binary {binary_path} will now load {library_path}")
    print("\nNote: Make sure the library is accessible at runtime")
    print("You may need to set LD_LIBRARY_PATH or copy the library to a standard location")

if __name__ == "__main__":
    main()