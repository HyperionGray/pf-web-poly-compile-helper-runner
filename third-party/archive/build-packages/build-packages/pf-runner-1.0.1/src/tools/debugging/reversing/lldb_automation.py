#!/usr/bin/env python3
"""
LLDB Automation
Automate LLDB debugging sessions with custom breakpoints and scripts.
"""

import sys
import os
import subprocess
import tempfile
from pathlib import Path

class LLDBAutomation:
    """Automate LLDB debugging with scripting"""
    
    def __init__(self, binary_path, script_path=None):
        self.binary_path = Path(binary_path)
        self.script_path = Path(script_path) if script_path else None
        
        if not self.binary_path.exists():
            raise FileNotFoundError(f"Binary not found: {binary_path}")
    
    def generate_default_script(self):
        """Generate a default LLDB script for analysis"""
        script = """
# Auto-generated LLDB script

# Set up breakpoints on interesting functions
break set -n main
break set -n malloc
break set -n free
break set -n strcpy
break set -n sprintf
break set -n memcpy

# Break on system calls
break set -n system
break set -n exec
break set -n fork

# Set conditional breakpoint example
# break set -n vulnerable_function -c 'size > 1024'

# Print registers on breakpoint hit
break command add -s python
frame variable
register read
DONE

# Run the program
run

# Print backtrace on crash
bt

# Continue execution
continue
"""
        return script
    
    def create_advanced_script(self, functions=None, conditions=None):
        """Create advanced LLDB script with custom breakpoints"""
        script_lines = ["# LLDB Automation Script\n"]
        
        # Add breakpoints for specified functions
        if functions:
            script_lines.append("# Custom function breakpoints")
            for func in functions.split(','):
                func = func.strip()
                script_lines.append(f"break set -n {func}")
        
        # Add conditional breakpoints
        if conditions:
            script_lines.append("\n# Conditional breakpoints")
            for condition in conditions.split(';'):
                if ':' in condition:
                    func, cond = condition.split(':', 1)
                    script_lines.append(f"break set -n {func.strip()} -c '{cond.strip()}'")
        
        # Add automatic commands
        script_lines.extend([
            "\n# Automatic commands on breakpoint",
            "break command add -s python",
            "print('Breakpoint hit!')",
            "frame = lldb.thread.GetSelectedFrame()",
            "print('Function:', frame.GetFunctionName())",
            "print('Arguments:', frame.get_arguments())",
            "DONE",
            "\n# Run",
            "run",
            "\n# Continue on crash",
            "bt",
            "continue"
        ])
        
        return '\n'.join(script_lines)
    
    def run_lldb_session(self, script_content):
        """Run LLDB with the provided script"""
        print(f"[*] Starting LLDB session for {self.binary_path.name}...")
        
        # Create temporary script file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lldb', delete=False) as f:
            f.write(script_content)
            script_file = f.name
        
        try:
            # Run LLDB with script
            cmd = ['lldb', '-s', script_file, '--batch', str(self.binary_path)]
            
            print(f"[*] Running: {' '.join(cmd)}")
            print(f"[*] Script:\n{script_content}\n")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            print(f"\n=== LLDB Output ===")
            print(result.stdout)
            
            if result.stderr:
                print(f"\n=== Errors ===")
                print(result.stderr)
            
            print(f"\n[+] LLDB session complete")
            
        except subprocess.TimeoutExpired:
            print(f"[-] LLDB session timed out")
        except FileNotFoundError:
            print(f"[-] LLDB not found. Install with: sudo apt-get install lldb")
        except Exception as e:
            print(f"[-] Error running LLDB: {e}")
        finally:
            # Clean up temp file
            Path(script_file).unlink(missing_ok=True)
    
    def run(self, functions=None, conditions=None):
        """Run automated LLDB session"""
        print(f"\n=== LLDB Automation ===")
        
        # Use provided script or generate one
        if self.script_path and self.script_path.exists():
            print(f"[*] Using script: {self.script_path}")
            with open(self.script_path, 'r') as f:
                script_content = f.read()
        else:
            if functions or conditions:
                print(f"[*] Generating advanced script...")
                script_content = self.create_advanced_script(functions, conditions)
            else:
                print(f"[*] Generating default analysis script...")
                script_content = self.generate_default_script()
        
        self.run_lldb_session(script_content)

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <binary_path> [script_path]")
        print(f"\nExample:")
        print(f"  {sys.argv[0]} /path/to/binary")
        print(f"  {sys.argv[0]} /path/to/binary /path/to/script.lldb")
        print(f"\nEnvironment variables:")
        print(f"  LLDB_FUNCTIONS='func1,func2' - Functions to break on")
        print(f"  LLDB_CONDITIONS='func:cond;func2:cond2' - Conditional breakpoints")
        sys.exit(1)
    
    binary_path = sys.argv[1]
    script_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Get optional parameters from environment
    functions = os.environ.get('LLDB_FUNCTIONS')
    conditions = os.environ.get('LLDB_CONDITIONS')
    
    try:
        automation = LLDBAutomation(binary_path, script_path)
        automation.run(functions, conditions)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
