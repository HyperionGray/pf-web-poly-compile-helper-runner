#!/usr/bin/env python3
"""
Automatic Breakpoint Generator
Generates LLDB/GDB breakpoints with complex conditionals based on binary analysis.
"""

import sys
from pathlib import Path

def generate_breakpoints(binary_path, functions=None, conditions=None):
    """Generate breakpoint script"""
    print(f"[*] Generating automatic breakpoints for {binary_path}")
    
    # Default dangerous functions to monitor
    default_functions = [
        'malloc', 'free', 'realloc', 'calloc',
        'strcpy', 'strcat', 'sprintf', 'gets',
        'memcpy', 'memmove', 'strncpy'
    ]
    
    target_functions = functions.split(',') if functions else default_functions
    
    print(f"[+] Targeting {len(target_functions)} functions")
    
    # Generate LLDB script
    script_lines = ["# Auto-generated breakpoint script\n"]
    
    for func in target_functions:
        func = func.strip()
        script_lines.append(f"break set -n {func}")
        
        # Add automatic logging
        script_lines.append("break command add -s python")
        script_lines.append(f"print('[BREAKPOINT] {func} called')")
        script_lines.append("frame = lldb.thread.GetSelectedFrame()")
        script_lines.append("print('  Args:', [str(frame.FindVariable(f'arg{i}')) for i in range(3)])")
        script_lines.append("DONE\n")
    
    # Add conditional breakpoints if specified
    if conditions:
        script_lines.append("# Conditional breakpoints")
        for cond in conditions.split(';'):
            if ':' in cond:
                func, condition = cond.split(':', 1)
                script_lines.append(f"break set -n {func.strip()} -c '{condition.strip()}'")
    
    script = '\n'.join(script_lines)
    
    # Save script
    output_file = Path(binary_path).stem + '_breakpoints.lldb'
    with open(output_file, 'w') as f:
        f.write(script)
    
    print(f"\n[+] Breakpoint script saved to: {output_file}")
    print(f"\nUse with:")
    print(f"  lldb -s {output_file} {binary_path}")
    print(f"  or")
    print(f"  pf reverse-lldb binary={binary_path} script={output_file}")
    
    return output_file

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <binary> [functions] [conditions]")
        print(f"\nExample:")
        print(f"  {sys.argv[0]} /path/to/binary")
        print(f"  {sys.argv[0]} /path/to/binary malloc,free")
        print(f"  {sys.argv[0]} /path/to/binary malloc 'malloc:size>1024'")
        sys.exit(1)
    
    binary = sys.argv[1]
    functions = sys.argv[2] if len(sys.argv) > 2 else None
    conditions = sys.argv[3] if len(sys.argv) > 3 else None
    
    generate_breakpoints(binary, functions, conditions)

if __name__ == '__main__':
    main()
