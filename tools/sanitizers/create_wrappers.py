#!/usr/bin/env python3
"""
Create sanitizer wrapper scripts for easy compiler usage.
Part of the pf-runner sanitizer integration framework.
"""

import os
import stat
from pathlib import Path

def create_wrapper_script(name, sanitizer_flags, description):
    """Create a wrapper script for a specific sanitizer configuration."""
    script_content = f'''#!/bin/bash
# {description}
# Auto-generated sanitizer wrapper script

# Add debug info and frame pointers for better stack traces
SANITIZER_FLAGS="{sanitizer_flags} -fno-omit-frame-pointer -g"

# Determine if we're compiling or linking
if [[ "$*" == *"-c"* ]]; then
    # Compilation only - add sanitizer flags to CFLAGS
    exec clang $SANITIZER_FLAGS "$@"
else
    # Linking - add sanitizer flags to both compile and link
    exec clang $SANITIZER_FLAGS "$@"
fi
'''
    
    wrapper_path = Path.home() / ".local" / "bin" / name
    wrapper_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(wrapper_path, 'w') as f:
        f.write(script_content)
    
    # Make executable
    wrapper_path.chmod(wrapper_path.stat().st_mode | stat.S_IEXEC)
    print(f"✅ Created {name} wrapper: {wrapper_path}")

def create_cxx_wrapper(base_name, sanitizer_flags, description):
    """Create C++ version of wrapper script."""
    cxx_name = base_name.replace('clang', 'clang++')
    cxx_script_content = f'''#!/bin/bash
# {description} (C++ version)
# Auto-generated sanitizer wrapper script

# Add debug info and frame pointers for better stack traces
SANITIZER_FLAGS="{sanitizer_flags} -fno-omit-frame-pointer -g"

# Determine if we're compiling or linking
if [[ "$*" == *"-c"* ]]; then
    # Compilation only - add sanitizer flags to CXXFLAGS
    exec clang++ $SANITIZER_FLAGS "$@"
else
    # Linking - add sanitizer flags to both compile and link
    exec clang++ $SANITIZER_FLAGS "$@"
fi
'''
    
    wrapper_path = Path.home() / ".local" / "bin" / cxx_name
    
    with open(wrapper_path, 'w') as f:
        f.write(cxx_script_content)
    
    # Make executable
    wrapper_path.chmod(wrapper_path.stat().st_mode | stat.S_IEXEC)
    print(f"✅ Created {cxx_name} wrapper: {wrapper_path}")

def main():
    """Create all sanitizer wrapper scripts."""
    print("Creating sanitizer wrapper scripts...")
    
    # AddressSanitizer
    create_wrapper_script(
        "clang-asan",
        "-fsanitize=address",
        "AddressSanitizer wrapper - detects memory errors"
    )
    create_cxx_wrapper(
        "clang-asan",
        "-fsanitize=address",
        "AddressSanitizer wrapper - detects memory errors"
    )
    
    # MemorySanitizer
    create_wrapper_script(
        "clang-msan",
        "-fsanitize=memory",
        "MemorySanitizer wrapper - detects uninitialized memory"
    )
    create_cxx_wrapper(
        "clang-msan",
        "-fsanitize=memory",
        "MemorySanitizer wrapper - detects uninitialized memory"
    )
    
    # UndefinedBehaviorSanitizer
    create_wrapper_script(
        "clang-ubsan",
        "-fsanitize=undefined",
        "UndefinedBehaviorSanitizer wrapper - detects undefined behavior"
    )
    create_cxx_wrapper(
        "clang-ubsan",
        "-fsanitize=undefined",
        "UndefinedBehaviorSanitizer wrapper - detects undefined behavior"
    )
    
    # ThreadSanitizer
    create_wrapper_script(
        "clang-tsan",
        "-fsanitize=thread",
        "ThreadSanitizer wrapper - detects data races"
    )
    create_cxx_wrapper(
        "clang-tsan",
        "-fsanitize=thread",
        "ThreadSanitizer wrapper - detects data races"
    )
    
    # Combined sanitizers (ASan + UBSan)
    create_wrapper_script(
        "clang-asan-ubsan",
        "-fsanitize=address,undefined",
        "Combined AddressSanitizer + UBSan wrapper"
    )
    create_cxx_wrapper(
        "clang-asan-ubsan",
        "-fsanitize=address,undefined",
        "Combined AddressSanitizer + UBSan wrapper"
    )
    
    print("\n🎯 Sanitizer wrapper scripts created successfully!")
    print("Add ~/.local/bin to your PATH to use them:")
    print("  export PATH=\"$HOME/.local/bin:$PATH\"")
    print("\nUsage examples:")
    print("  clang-asan -o myprogram myprogram.c")
    print("  clang++-msan -o myprogram myprogram.cpp")
    print("  CC=clang-asan make")

if __name__ == "__main__":
    main()