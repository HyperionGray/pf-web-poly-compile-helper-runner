#!/usr/bin/env python3
"""Control Flow Graph Extraction"""
import sys
from pathlib import Path

def extract_cfg(binary_path, output_dir):
    print(f"[*] Extracting control flow graph from {binary_path}")
    print(f"[*] Output directory: {output_dir}")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"\n[!] This is a stub implementation")
    print(f"[*] For full CFG extraction, use:")
    print(f"    pf reverse-radare2 binary={binary_path}")
    print(f"    or install Ghidra for advanced CFG analysis")

if __name__ == '__main__':
    binary = sys.argv[1] if len(sys.argv) > 1 else None
    output = sys.argv[2] if len(sys.argv) > 2 else './cfg_output'
    if binary:
        extract_cfg(binary, output)
