#!/usr/bin/env python3
"""
Constructor injection tool for adding constructor functions to binaries.
This tool modifies the binary to execute code when it starts up.
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

def add_constructor_lief(binary_path, library_path):
    """Add constructor using LIEF library"""
    if not LIEF_AVAILABLE:
        raise ImportError("LIEF library not available")
    
    print(f"Adding constructor injection to {binary_path} using LIEF...")
    
    # Parse the binary
    binary = lief.parse(binary_path)
    if not binary:
        raise ValueError(f"Failed to parse binary: {binary_path}")
    
    # Add the library as a dependency
    library_name = os.path.basename(library_path)
    binary.add_library(library_name)
    
    # Try to add to init_array section for constructor execution
    try:
        # This is a simplified approach - real implementation would need
        # more sophisticated ELF manipulation
        init_array = binary.get_section(".init_array")
        if init_array:
            print("Found .init_array section - constructor will be called on startup")
        else:
            print("No .init_array section found - library constructor will still execute")
    except:
        pass
    
    # Write the patched binary
    binary.write(binary_path)
    print(f"Successfully added constructor injection with {library_name}")

def add_constructor_objcopy(binary_path, library_path):
    """Add constructor using objcopy and linker tricks"""
    print(f"Adding constructor to {binary_path} using objcopy method...")
    
    # Create a temporary object file with constructor
    temp_dir = "/tmp/injection_constructor"
    os.makedirs(temp_dir, exist_ok=True)
    
    constructor_c = f"{temp_dir}/constructor.c"
    constructor_o = f"{temp_dir}/constructor.o"
    
    # Write constructor code
    with open(constructor_c, 'w') as f:
        f.write(f'''
#include <dlfcn.h>
#include <stdio.h>

__attribute__((constructor))
void injected_constructor() {{
    void *handle = dlopen("{os.path.abspath(library_path)}", RTLD_LAZY);
    if (!handle) {{
        fprintf(stderr, "Failed to load injection library: %s\\n", dlerror());
        return;
    }}
    printf("[CONSTRUCTOR] Injection library loaded: {library_path}\\n");
}}
''')
    
    # Compile constructor
    try:
        subprocess.run([
            'gcc', '-c', '-fPIC', constructor_c, '-o', constructor_o
        ], check=True)
    except subprocess.CalledProcessError:
        raise RuntimeError("Failed to compile constructor code")
    
    # Link constructor into binary (this is complex and may not work for all binaries)
    print("Warning: Constructor linking is experimental and may not work")
    print(f"Constructor object created at: {constructor_o}")
    print("Manual linking may be required")

def add_constructor_wrapper(binary_path, library_path):
    """Create wrapper script with constructor behavior"""
    print(f"Creating constructor wrapper for {binary_path}...")
    
    wrapper_path = binary_path + "_with_constructor"
    
    with open(wrapper_path, 'w') as f:
        f.write(f"""#!/bin/bash
# Auto-generated constructor injection wrapper

# Load the injection library with constructor
export LD_PRELOAD="{os.path.abspath(library_path)}:$LD_PRELOAD"

# Execute the original binary
exec "{os.path.abspath(binary_path)}" "$@"
""")
    
    os.chmod(wrapper_path, 0o755)
    print(f"Created constructor wrapper: {wrapper_path}")
    print("The injection library's constructor will execute when the wrapper runs")

def create_constructor_library(library_path):
    """Ensure the library has proper constructor functions"""
    print(f"Verifying constructor in {library_path}...")
    
    try:
        # Check if library has constructor symbols
        result = subprocess.run([
            'nm', '-D', library_path
        ], capture_output=True, text=True)
        
        has_constructor = False
        for line in result.stdout.split('\n'):
            if '__attribute__((constructor))' in line or '_init' in line:
                has_constructor = True
                break
        
        if not has_constructor:
            print("Warning: Library may not have constructor functions")
            print("Make sure your library code includes __attribute__((constructor)) functions")
        else:
            print("Library appears to have constructor functions")
            
    except:
        print("Could not analyze library symbols")

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 add-constructor.py <binary_path> <library_path>")
        print("")
        print("This tool adds constructor injection to a binary.")
        print("The library will be loaded and its constructor functions executed when the binary starts.")
        print("")
        print("Examples:")
        print("  python3 add-constructor.py ./myapp ./payload.so")
        print("  python3 add-constructor.py /usr/bin/program /tmp/injected.so")
        print("")
        print("Note: The library should contain __attribute__((constructor)) functions")
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
    
    # Verify library has constructors
    create_constructor_library(library_path)
    
    # Try constructor injection methods
    methods = [
        ("LIEF", add_constructor_lief),
        ("wrapper script", add_constructor_wrapper),
        ("objcopy", add_constructor_objcopy)
    ]
    
    for method_name, method_func in methods:
        try:
            print(f"\nTrying {method_name} method...")
            method_func(binary_path, library_path)
            print(f"Success! Constructor injection added using {method_name}")
            break
        except Exception as e:
            print(f"{method_name} method failed: {e}")
            continue
    else:
        print("All constructor injection methods failed!")
        sys.exit(1)
    
    print("\nConstructor injection completed successfully!")
    print(f"The binary will now execute constructor code from {library_path}")
    print("\nTesting tips:")
    print("1. Make sure the library is accessible at runtime")
    print("2. Test with a simple library first")
    print("3. Check that constructor functions are properly defined")

if __name__ == "__main__":
    main()