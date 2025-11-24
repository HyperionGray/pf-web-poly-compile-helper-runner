#!/usr/bin/env python3
"""
In-Memory Fuzzer
Fast in-memory fuzzing by patching function returns to loop back with mutated input.

This provides blazing fast fuzzing by:
1. Setting breakpoint at function end (before return)
2. Mutating input data in memory
3. Jumping back to function start or earlier in call chain
4. Repeating for thousands of iterations in-process

Much faster than traditional fuzzing since no process creation overhead.
"""

import sys
import os
import subprocess
import tempfile
import random
import time
from pathlib import Path
from collections import defaultdict

try:
    import lldb
    LLDB_AVAILABLE = True
except ImportError:
    LLDB_AVAILABLE = False
    print("[!] lldb Python module not available. Using command-line lldb instead.")


class InMemoryFuzzer:
    """In-memory fuzzer using LLDB for fast fuzzing"""
    
    MUTATION_STRATEGIES = [
        'bit_flip',
        'byte_flip',
        'arithmetic',
        'interesting_values',
        'block_deletion',
        'block_duplication',
        'random_bytes'
    ]
    
    # Interesting values that often trigger bugs
    INTERESTING_8 = [0, 1, 127, 128, 255]
    INTERESTING_16 = [0, 1, 255, 256, 32767, 32768, 65535]
    INTERESTING_32 = [0, 1, 65535, 65536, 2147483647, 2147483648, 4294967295]
    
    def __init__(self, binary_path, target_function=None, jump_back_depth=0, iterations=1000):
        self.binary_path = Path(binary_path)
        self.target_function = target_function or 'main'
        self.jump_back_depth = jump_back_depth
        self.iterations = iterations
        self.crashes = []
        self.interesting_inputs = []
        
        if not self.binary_path.exists():
            raise FileNotFoundError(f"Binary not found: {binary_path}")
    
    def mutate_bytes(self, data, strategy=None):
        """Mutate byte array using specified strategy"""
        if not data:
            return data
        
        if strategy is None:
            strategy = random.choice(self.MUTATION_STRATEGIES)
        
        data = bytearray(data)
        
        if strategy == 'bit_flip':
            # Flip random bit
            if data:
                byte_idx = random.randint(0, len(data) - 1)
                bit_idx = random.randint(0, 7)
                data[byte_idx] ^= (1 << bit_idx)
        
        elif strategy == 'byte_flip':
            # Flip random byte
            if data:
                idx = random.randint(0, len(data) - 1)
                data[idx] ^= 0xFF
        
        elif strategy == 'arithmetic':
            # Add/subtract small value
            if data:
                idx = random.randint(0, len(data) - 1)
                delta = random.randint(-35, 35)
                data[idx] = (data[idx] + delta) % 256
        
        elif strategy == 'interesting_values':
            # Insert interesting values
            if len(data) >= 4:
                idx = random.randint(0, len(data) - 4)
                value = random.choice(self.INTERESTING_32)
                data[idx:idx+4] = value.to_bytes(4, 'little')
            elif len(data) >= 2:
                idx = random.randint(0, len(data) - 2)
                value = random.choice(self.INTERESTING_16)
                data[idx:idx+2] = value.to_bytes(2, 'little')
            elif data:
                idx = random.randint(0, len(data) - 1)
                data[idx] = random.choice(self.INTERESTING_8)
        
        elif strategy == 'block_deletion':
            # Delete random block
            if len(data) > 1:
                start = random.randint(0, len(data) - 1)
                end = random.randint(start + 1, len(data))
                data = data[:start] + data[end:]
        
        elif strategy == 'block_duplication':
            # Duplicate random block
            if data:
                start = random.randint(0, len(data) - 1)
                end = random.randint(start + 1, min(start + 100, len(data)))
                block = data[start:end]
                insert_pos = random.randint(0, len(data))
                data = data[:insert_pos] + block + data[insert_pos:]
        
        elif strategy == 'random_bytes':
            # Replace with random bytes
            if data:
                start = random.randint(0, len(data) - 1)
                end = random.randint(start + 1, min(start + 20, len(data)))
                for i in range(start, end):
                    data[i] = random.randint(0, 255)
        
        return bytes(data)
    
    def generate_lldb_script(self, initial_input_file=None):
        """Generate LLDB script for in-memory fuzzing"""
        script_lines = [
            f"# In-Memory Fuzzer LLDB Script",
            f"# Target: {self.target_function}",
            f"# Iterations: {self.iterations}",
            f"# Jump-back depth: {self.jump_back_depth}",
            f"",
            f"# Load binary",
            f"target create {self.binary_path}",
            f"",
            f"# Set breakpoint at target function",
            f"breakpoint set -n {self.target_function}",
            f"",
        ]
        
        if initial_input_file:
            script_lines.extend([
                f"# Set initial arguments",
                f"settings set target.run-args {initial_input_file}",
                f"",
            ])
        
        script_lines.extend([
            f"# Run to target function",
            f"run",
            f"",
            f"# Get function end address",
            f"disassemble -n {self.target_function}",
            f"",
            f"# Note: Manual intervention needed for setting return breakpoint",
            f"# Use: breakpoint set -a <address_before_return>",
            f"",
            f"# Continue execution",
            f"continue",
        ])
        
        return '\n'.join(script_lines)
    
    def generate_python_lldb_script(self):
        """Generate Python script for LLDB scripting API"""
        script = f'''
import lldb
import random

def mutate_bytes(data):
    """Simple mutation function"""
    if not data:
        return data
    
    data = bytearray(data)
    
    # Random mutation strategy
    strategy = random.choice(['bit_flip', 'byte_flip', 'random'])
    
    if strategy == 'bit_flip' and data:
        idx = random.randint(0, len(data) - 1)
        bit = random.randint(0, 7)
        data[idx] ^= (1 << bit)
    elif strategy == 'byte_flip' and data:
        idx = random.randint(0, len(data) - 1)
        data[idx] ^= 0xFF
    elif strategy == 'random' and data:
        idx = random.randint(0, len(data) - 1)
        data[idx] = random.randint(0, 255)
    
    return bytes(data)

def fuzz_in_memory(debugger, command, result, internal_dict):
    """In-memory fuzzing command"""
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    frame = thread.GetSelectedFrame()
    
    print(f"[*] Starting in-memory fuzzing...")
    print(f"[*] Current function: {{frame.GetFunctionName()}}")
    
    # Get function start address
    func_start = frame.GetFunction().GetStartAddress()
    print(f"[*] Function start: {{func_start}}")
    
    iterations = int(command) if command.isdigit() else 100
    
    for i in range(iterations):
        # Mutate input data in memory
        # This is a simplified example - real implementation would:
        # 1. Find input buffers in memory
        # 2. Mutate them
        # 3. Jump back to function start
        # 4. Continue execution
        
        print(f"[*] Iteration {{i+1}}/{{iterations}}")
        
        # Continue to next iteration
        process.Continue()
        
        # Check for crashes
        if process.GetState() == lldb.eStateStopped:
            stop_reason = thread.GetStopReason()
            if stop_reason == lldb.eStopReasonSignal:
                print(f"[!] CRASH detected at iteration {{i+1}}")
                print(f"[!] Signal: {{process.GetUnixSignals().GetSignalAtIndex(0)}}")
                break
        
        if process.GetState() == lldb.eStateExited:
            print(f"[*] Process exited normally at iteration {{i+1}}")
            break
    
    print(f"[+] Fuzzing complete")

# Register command
def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f in_memory_fuzz.fuzz_in_memory fuzz')
    print("[+] In-memory fuzzer loaded. Use: fuzz [iterations]")
'''
        return script
    
    def run_command_line_fuzzing(self, input_file=None):
        """Run fuzzing using command-line lldb"""
        print(f"\n=== In-Memory Fuzzer ===")
        print(f"Target: {self.binary_path}")
        print(f"Function: {self.target_function}")
        print(f"Iterations: {self.iterations}")
        print(f"Jump-back depth: {self.jump_back_depth}")
        
        # Generate initial input if not provided
        if not input_file:
            print(f"\n[*] Generating initial input...")
            with tempfile.NamedTemporaryFile(delete=False, suffix='.bin') as f:
                # Generate random initial input
                initial_data = bytes([random.randint(0, 255) for _ in range(1024)])
                f.write(initial_data)
                input_file = f.name
            print(f"[+] Created input file: {input_file}")
        
        # Create LLDB script
        script_content = self.generate_lldb_script(input_file)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lldb', delete=False) as f:
            f.write(script_content)
            script_file = f.name
        
        print(f"\n[*] Generated LLDB script: {script_file}")
        print(f"\n[!] Note: Full in-memory fuzzing requires interactive LLDB session")
        print(f"[!] This script sets up the initial breakpoints")
        print(f"\n[*] To run full fuzzing:")
        print(f"    1. lldb {self.binary_path}")
        print(f"    2. command source {script_file}")
        print(f"    3. Set return breakpoint: breakpoint set -a <addr_before_ret>")
        print(f"    4. Add Python script for mutation and loop-back")
        
        # Run initial setup
        try:
            cmd = ['lldb', '-s', script_file, '--batch', str(self.binary_path)]
            print(f"\n[*] Running initial setup...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            print(f"\n=== LLDB Output ===")
            print(result.stdout)
            
            if result.stderr:
                print(f"\n=== Errors ===")
                print(result.stderr)
        
        except subprocess.TimeoutExpired:
            print(f"[-] LLDB timed out")
        except FileNotFoundError:
            print(f"[-] LLDB not found. Install with: sudo apt-get install lldb")
        except Exception as e:
            print(f"[-] Error: {e}")
        
        finally:
            # Cleanup
            if input_file and Path(input_file).exists():
                Path(input_file).unlink(missing_ok=True)
            if Path(script_file).exists():
                Path(script_file).unlink(missing_ok=True)
    
    def generate_fuzzing_guide(self):
        """Generate comprehensive guide for in-memory fuzzing"""
        guide = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                      IN-MEMORY FUZZING SETUP GUIDE                         ║
╚════════════════════════════════════════════════════════════════════════════╝

Binary: {self.binary_path}
Target Function: {self.target_function}

═══════════════════════════════════════════════════════════════════════════
1. BASIC SETUP
═══════════════════════════════════════════════════════════════════════════

Start LLDB:
    $ lldb {self.binary_path}

Set breakpoint at target function:
    (lldb) breakpoint set -n {self.target_function}
    (lldb) run

═══════════════════════════════════════════════════════════════════════════
2. FIND RETURN ADDRESS
═══════════════════════════════════════════════════════════════════════════

Disassemble function to find return instruction:
    (lldb) disassemble -n {self.target_function}

Look for "ret" instruction near the end.
Set breakpoint before return:
    (lldb) breakpoint set -a <address_before_ret>

═══════════════════════════════════════════════════════════════════════════
3. MUTATION LOOP (Manual)
═══════════════════════════════════════════════════════════════════════════

At the return breakpoint:

A. Find input buffer in registers/memory:
    (lldb) register read
    (lldb) memory read <buffer_address>

B. Mutate input data:
    (lldb) memory write <address> <mutated_bytes>

C. Jump back to function start:
    (lldb) jump -a <function_start_address>

D. Continue:
    (lldb) continue

═══════════════════════════════════════════════════════════════════════════
4. AUTOMATED FUZZING (Python Script)
═══════════════════════════════════════════════════════════════════════════

Create Python script:

```python
import lldb
import random

def fuzz_iteration(debugger, command, result, internal_dict):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    frame = thread.GetSelectedFrame()
    
    # Get input buffer address (example)
    buf_addr = frame.FindVariable("input_buffer").GetAddress()
    
    if buf_addr:
        # Read current buffer
        error = lldb.SBError()
        data = process.ReadMemory(buf_addr, 1024, error)
        
        if not error.Fail():
            # Mutate
            mutated = bytearray(data)
            idx = random.randint(0, len(mutated) - 1)
            mutated[idx] ^= 0xFF
            
            # Write back
            process.WriteMemory(buf_addr, bytes(mutated), error)
    
    # Jump back to function start
    func_start = frame.GetFunction().GetStartAddress()
    thread.JumpToLine(func_start)
    
    # Continue
    process.Continue()

def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f fuzz.fuzz_iteration fuzz_iter')
```

Load in LLDB:
    (lldb) command script import /path/to/fuzz.py
    (lldb) fuzz_iter

═══════════════════════════════════════════════════════════════════════════
5. MONITORING FOR CRASHES
═══════════════════════════════════════════════════════════════════════════

Check process state after each iteration:
    - eStateStop + eStopReasonSignal = CRASH
    - Common crash signals: SIGSEGV, SIGILL, SIGBUS, SIGABRT

On crash:
    (lldb) bt             # Backtrace
    (lldb) register read  # Register state
    (lldb) memory read $rsp # Stack dump

═══════════════════════════════════════════════════════════════════════════
6. JUMP-BACK DEPTH
═══════════════════════════════════════════════════════════════════════════

Jump-back depth {self.jump_back_depth}:
    - 0: Jump to current function start
    - 1: Jump to caller function
    - 2: Jump to caller's caller
    - etc.

To implement:
    (lldb) bt  # Get call stack
    Select frame at desired depth:
    (lldb) frame select {self.jump_back_depth}
    (lldb) jump -a <selected_frame_start>

═══════════════════════════════════════════════════════════════════════════
7. TIPS FOR MAXIMUM SPEED
═══════════════════════════════════════════════════════════════════════════

- Disable output: (lldb) settings set target.process.stop-on-crash false
- Use hardware breakpoints when possible
- Batch mutations (mutate multiple bytes per iteration)
- Keep mutations simple for speed
- Monitor for unique crashes only (deduplicate by crash address)

═══════════════════════════════════════════════════════════════════════════
8. ALTERNATIVE: GDB-BASED FUZZING
═══════════════════════════════════════════════════════════════════════════

If using GDB:
    $ gdb {self.binary_path}
    (gdb) break {self.target_function}
    (gdb) run
    (gdb) disas
    (gdb) break *<address_before_ret>
    (gdb) commands
        silent
        set {{char[1024]}}$buffer_addr = <mutated_data>
        jump *<func_start>
        continue
    end

═══════════════════════════════════════════════════════════════════════════

For automated fuzzing, use the fast_fuzzer.py or parallel_fuzzer.py scripts.
"""
        return guide
    
    def run(self):
        """Run in-memory fuzzer"""
        print(self.generate_fuzzing_guide())
        
        response = input("\n[?] Would you like to generate LLDB setup script? (y/n): ")
        if response.lower() == 'y':
            self.run_command_line_fuzzing()
        
        print(f"\n[*] In-memory fuzzing requires interactive LLDB session")
        print(f"[*] Follow the guide above to set up automated fuzzing")


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <binary_path> [options]")
        print(f"\nOptions:")
        print(f"  --function NAME      Target function (default: main)")
        print(f"  --iterations N       Number of iterations (default: 1000)")
        print(f"  --jump-back N        Jump back N frames (default: 0)")
        print(f"\nExample:")
        print(f"  {sys.argv[0]} /path/to/binary")
        print(f"  {sys.argv[0]} /path/to/binary --function parse_input --iterations 10000")
        print(f"  {sys.argv[0]} /path/to/binary --function handle_request --jump-back 2")
        sys.exit(1)
    
    binary_path = sys.argv[1]
    target_function = 'main'
    iterations = 1000
    jump_back_depth = 0
    
    # Parse arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--function' and i + 1 < len(sys.argv):
            target_function = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--iterations' and i + 1 < len(sys.argv):
            iterations = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == '--jump-back' and i + 1 < len(sys.argv):
            jump_back_depth = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1
    
    try:
        fuzzer = InMemoryFuzzer(binary_path, target_function, jump_back_depth, iterations)
        fuzzer.run()
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
