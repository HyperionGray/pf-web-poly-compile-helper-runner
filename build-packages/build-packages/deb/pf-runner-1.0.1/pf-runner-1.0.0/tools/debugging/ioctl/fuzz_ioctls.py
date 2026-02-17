#!/usr/bin/env python3
"""
IOCTL Fuzzer
Fuzzes discovered IOCTLs with random data to find crashes and vulnerabilities.
"""

import sys
import os
import json
import fcntl
import struct
import random
import time
from pathlib import Path

class IOCTLFuzzer:
    """Fuzz IOCTLs with various payloads"""
    
    def __init__(self, driver_path, ioctl_list_path=None, iterations=1000):
        self.driver_path = Path(driver_path)
        self.iterations = iterations
        self.crashes = []
        self.ioctls = []
        
        if ioctl_list_path and Path(ioctl_list_path).exists():
            self.load_ioctl_list(ioctl_list_path)
        else:
            # Use common IOCTL codes if no list provided
            self.ioctls = self.generate_common_ioctls()
    
    def load_ioctl_list(self, path):
        """Load IOCTL codes from discovery output"""
        with open(path, 'r') as f:
            data = json.load(f)
            codes = data.get('discovered_codes', [])
            self.ioctls = [int(c, 16) if isinstance(c, str) else c for c in codes]
        print(f"[+] Loaded {len(self.ioctls)} IOCTL codes")
    
    def generate_common_ioctls(self):
        """Generate common IOCTL code ranges for testing"""
        # Common IOCTL ranges
        codes = []
        
        # Linux standard IOCTLs
        for base in [0x5400, 0x5600, 0x7400, 0x8900]:
            for i in range(256):
                codes.append(base + i)
        
        # Random codes in typical ranges
        for _ in range(100):
            codes.append(random.randint(0x1000, 0xFFFF))
        
        print(f"[+] Generated {len(codes)} test IOCTL codes")
        return codes
    
    def generate_payload(self, size=None):
        """Generate random fuzzing payload"""
        if size is None:
            size = random.choice([0, 1, 4, 8, 16, 64, 256, 1024, 4096])
        
        # Different payload strategies
        strategy = random.choice(['random', 'zeros', 'ones', 'pattern', 'boundary'])
        
        if strategy == 'random':
            return bytes([random.randint(0, 255) for _ in range(size)])
        elif strategy == 'zeros':
            return b'\x00' * size
        elif strategy == 'ones':
            return b'\xff' * size
        elif strategy == 'pattern':
            pattern = b'AAAA' * (size // 4) + b'A' * (size % 4)
            return pattern
        elif strategy == 'boundary':
            # Interesting boundary values
            values = [0, 1, 0x7f, 0x80, 0xff, 0x7fff, 0x8000, 0xffff,
                     0x7fffffff, 0x80000000, 0xffffffff]
            data = b''
            while len(data) < size:
                val = random.choice(values)
                data += struct.pack('<I', val)[:min(4, size - len(data))]
            return data[:size]
        
        return b''
    
    def fuzz_ioctl(self, fd, ioctl_code, payload):
        """Execute a single IOCTL with fuzzing payload"""
        try:
            # Try IOCTL with payload
            result = fcntl.ioctl(fd, ioctl_code, payload)
            return {'success': True, 'result': result}
        except OSError as e:
            # Expected for most invalid IOCTLs
            return {'success': False, 'error': str(e)}
        except Exception as e:
            # Unexpected error might indicate a bug
            return {'success': False, 'error': str(e), 'unexpected': True}
    
    def run_fuzzing(self):
        """Run fuzzing campaign"""
        print(f"\n=== IOCTL Fuzzing ===")
        print(f"Target: {self.driver_path}")
        print(f"Iterations: {self.iterations}")
        print(f"IOCTL codes: {len(self.ioctls)}")
        
        if not self.driver_path.exists():
            print(f"[-] Driver device not found: {self.driver_path}")
            print("[!] Note: This fuzzer requires the driver to be loaded")
            print("[!] For kernel modules, ensure they are loaded first")
            return
        
        print(f"\n[*] Starting fuzzing campaign...")
        
        crashes = 0
        errors = 0
        successes = 0
        
        try:
            # Open device
            with open(self.driver_path, 'r+b', buffering=0) as fd:
                for i in range(self.iterations):
                    # Select random IOCTL
                    ioctl_code = random.choice(self.ioctls)
                    
                    # Generate payload
                    payload = self.generate_payload()
                    
                    # Fuzz
                    result = self.fuzz_ioctl(fd.fileno(), ioctl_code, payload)
                    
                    if result.get('success'):
                        successes += 1
                    elif result.get('unexpected'):
                        crashes += 1
                        print(f"[!] Potential crash: IOCTL {hex(ioctl_code)}")
                        self.crashes.append({
                            'ioctl': hex(ioctl_code),
                            'payload_size': len(payload),
                            'error': result.get('error')
                        })
                    else:
                        errors += 1
                    
                    # Progress
                    if (i + 1) % 100 == 0:
                        print(f"[*] Progress: {i+1}/{self.iterations} "
                              f"(successes: {successes}, crashes: {crashes})")
                    
                    # Small delay to avoid overwhelming the system
                    time.sleep(0.001)
        
        except FileNotFoundError:
            print(f"[-] Could not open device: {self.driver_path}")
            print("[!] This is a demonstration fuzzer")
            print("[!] In production, ensure the driver device exists")
            return
        except Exception as e:
            print(f"[-] Fuzzing error: {e}")
            return
        
        # Report results
        print(f"\n=== Fuzzing Complete ===")
        print(f"Total iterations: {self.iterations}")
        print(f"Successes: {successes}")
        print(f"Expected errors: {errors}")
        print(f"Potential crashes: {crashes}")
        
        if self.crashes:
            print(f"\n[!] Found {len(self.crashes)} potential issues:")
            for crash in self.crashes[:5]:
                print(f"    IOCTL {crash['ioctl']}: {crash['error']}")

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <driver_path> [ioctl_list_json] [iterations]")
        print(f"\nExample:")
        print(f"  {sys.argv[0]} /dev/mydriver ./output/driver_ioctls.json 10000")
        print(f"\nNote: This is a demonstration fuzzer for educational purposes.")
        print(f"      Always test on non-production systems.")
        sys.exit(1)
    
    driver_path = sys.argv[1]
    ioctl_list = sys.argv[2] if len(sys.argv) > 2 else None
    iterations = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
    
    try:
        fuzzer = IOCTLFuzzer(driver_path, ioctl_list, iterations)
        fuzzer.run_fuzzing()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
