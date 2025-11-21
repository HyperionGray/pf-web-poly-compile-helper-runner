#!/usr/bin/env python3
"""
Fast Fuzzer
A basic but fast fuzzer for finding crashes and hangs in binaries.
"""

import sys
import os
import subprocess
import random
import time
import signal
import tempfile
from pathlib import Path
from multiprocessing import Pool, cpu_count

class FastFuzzer:
    """Fast fuzzer implementation"""
    
    def __init__(self, binary_path, iterations=10000, timeout=5):
        self.binary_path = Path(binary_path)
        self.iterations = iterations
        self.timeout = timeout
        self.crashes = []
        self.hangs = []
        
        if not self.binary_path.exists():
            raise FileNotFoundError(f"Binary not found: {binary_path}")
    
    def generate_input(self, size=None, strategy=None):
        """Generate fuzzing input"""
        if size is None:
            size = random.choice([1, 10, 100, 1000, 4096, 8192, 65536])
        
        if strategy is None:
            strategy = random.choice([
                'random', 'zeros', 'ones', 'pattern',
                'ascii', 'format_strings', 'boundaries'
            ])
        
        if strategy == 'random':
            return bytes([random.randint(0, 255) for _ in range(size)])
        
        elif strategy == 'zeros':
            return b'\x00' * size
        
        elif strategy == 'ones':
            return b'\xff' * size
        
        elif strategy == 'pattern':
            # Cyclic pattern for finding offsets
            pattern = b''
            chars = b'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            for i in range(0, size, len(chars)):
                pattern += chars[:min(len(chars), size - i)]
            return pattern
        
        elif strategy == 'ascii':
            # ASCII printable characters
            return bytes([random.randint(32, 126) for _ in range(size)])
        
        elif strategy == 'format_strings':
            # Format string payloads
            payloads = [b'%x', b'%s', b'%n', b'%p'] * (size // 2)
            return b''.join(random.sample(payloads, min(len(payloads), size)))[:size]
        
        elif strategy == 'boundaries':
            # Boundary values
            values = [0, 1, 127, 128, 255, 256, 32767, 32768, 65535, 65536]
            data = b''
            while len(data) < size:
                val = random.choice(values)
                data += val.to_bytes(4, 'little')
            return data[:size]
        
        return b''
    
    def run_target(self, input_data):
        """Run target binary with input"""
        try:
            # Create temporary input file
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(input_data)
                input_file = f.name
            
            try:
                # Run binary with timeout
                # Try feeding input via file argument first
                result = subprocess.run(
                    [str(self.binary_path), input_file],
                    capture_output=True,
                    timeout=self.timeout,
                    stdin=subprocess.DEVNULL
                )
                
                return {
                    'status': 'normal',
                    'returncode': result.returncode,
                    'crashed': result.returncode < 0,
                    'signal': -result.returncode if result.returncode < 0 else None
                }
                
            except subprocess.TimeoutExpired:
                return {
                    'status': 'timeout',
                    'returncode': None,
                    'crashed': False,
                    'hang': True
                }
            
            finally:
                # Clean up temp file
                Path(input_file).unlink(missing_ok=True)
        
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'crashed': False
            }
    
    def fuzz_iteration(self, iteration):
        """Single fuzzing iteration"""
        # Generate input
        input_data = self.generate_input()
        
        # Run target
        result = run_target_wrapper(self.binary_path, input_data, self.timeout)
        
        # Check results
        if result.get('crashed'):
            return {
                'type': 'crash',
                'iteration': iteration,
                'signal': result.get('signal'),
                'input_size': len(input_data),
                'input_hash': hash(input_data)
            }
        
        elif result.get('hang'):
            return {
                'type': 'hang',
                'iteration': iteration,
                'input_size': len(input_data)
            }
        
        return None
    
    def fuzz(self):
        """Run fuzzing campaign"""
        print(f"\n=== Fast Fuzzer ===")
        print(f"Target: {self.binary_path}")
        print(f"Iterations: {self.iterations}")
        print(f"Timeout: {self.timeout}s")
        print(f"Workers: {cpu_count()}")
        
        print(f"\n[*] Starting fuzzing campaign...")
        
        start_time = time.time()
        crashes = []
        hangs = []
        
        # Single-threaded fuzzing for simplicity
        for i in range(self.iterations):
            result = self.fuzz_iteration(i)
            
            if result:
                if result['type'] == 'crash':
                    crashes.append(result)
                    print(f"\n[!] CRASH found at iteration {i}")
                    print(f"    Signal: {result.get('signal')}")
                    print(f"    Input size: {result['input_size']}")
                
                elif result['type'] == 'hang':
                    hangs.append(result)
                    print(f"\n[!] HANG detected at iteration {i}")
            
            # Progress update
            if (i + 1) % 100 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                print(f"\r[*] Progress: {i+1}/{self.iterations} "
                      f"({rate:.1f} exec/sec, crashes: {len(crashes)}, hangs: {len(hangs)})", 
                      end='', flush=True)
        
        print()  # New line after progress
        
        elapsed = time.time() - start_time
        
        print(f"\n=== Fuzzing Complete ===")
        print(f"Total time: {elapsed:.1f}s")
        print(f"Executions per second: {self.iterations / elapsed:.1f}")
        print(f"Crashes found: {len(crashes)}")
        print(f"Hangs found: {len(hangs)}")
        
        self.crashes = crashes
        self.hangs = hangs
        
        return {
            'crashes': len(crashes),
            'hangs': len(hangs),
            'executions': self.iterations,
            'time': elapsed
        }

def run_target_wrapper(binary_path, input_data, timeout):
    """Wrapper for running target (for multiprocessing)"""
    try:
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(input_data)
            input_file = f.name
        
        try:
            result = subprocess.run(
                [str(binary_path), input_file],
                capture_output=True,
                timeout=timeout,
                stdin=subprocess.DEVNULL
            )
            
            return {
                'status': 'normal',
                'returncode': result.returncode,
                'crashed': result.returncode < 0,
                'signal': -result.returncode if result.returncode < 0 else None
            }
            
        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'crashed': False,
                'hang': True
            }
        
        finally:
            Path(input_file).unlink(missing_ok=True)
    
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'crashed': False
        }

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <binary_path> [iterations] [timeout]")
        print(f"\nExample:")
        print(f"  {sys.argv[0]} /path/to/binary 10000 5")
        print(f"\nNote: This fuzzer feeds input via command-line arguments")
        sys.exit(1)
    
    binary_path = sys.argv[1]
    iterations = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
    timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    try:
        fuzzer = FastFuzzer(binary_path, iterations, timeout)
        results = fuzzer.fuzz()
        
        if results['crashes'] > 0 or results['hangs'] > 0:
            print(f"\n[!] Found issues! Consider deeper analysis with:")
            print(f"    pf reverse-lldb binary={binary_path}")
            print(f"    pf vuln-scan binary={binary_path}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
