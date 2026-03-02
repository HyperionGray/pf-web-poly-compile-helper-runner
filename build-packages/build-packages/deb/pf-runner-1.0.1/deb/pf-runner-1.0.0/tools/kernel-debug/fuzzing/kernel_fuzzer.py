#!/usr/bin/env python3
"""
Fast Kernel Fuzzer

A lightweight, high-performance fuzzer designed for kernel interfaces,
particularly IOCTLs and system calls.
"""

import os
import sys
import time
import random
import struct
import threading
import multiprocessing
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Generator
from dataclasses import dataclass, asdict
import argparse
import json

@dataclass
class FuzzCase:
    """Individual fuzz test case"""
    target: str
    input_data: bytes
    ioctl_cmd: Optional[int] = None
    expected_result: Optional[int] = None
    crash_detected: bool = False
    execution_time: float = 0.0
    
@dataclass
class FuzzStats:
    """Fuzzing statistics"""
    total_cases: int = 0
    crashes: int = 0
    hangs: int = 0
    unique_crashes: int = 0
    exec_per_sec: float = 0.0
    start_time: float = 0.0

class KernelFuzzer:
    """Fast kernel interface fuzzer"""
    
    def __init__(self, target_device: str = "/dev/null"):
        self.target_device = target_device
        self.stats = FuzzStats()
        self.crash_log = []
        self.running = False
        self.mutation_strategies = [
            self._mutate_random_bytes,
            self._mutate_bit_flip,
            self._mutate_arithmetic,
            self._mutate_interesting_values,
            self._mutate_splice
        ]
        self.interesting_values = self._generate_interesting_values()
    
    def _generate_interesting_values(self) -> List[bytes]:
        """Generate interesting values for fuzzing"""
        values = []
        
        # Integer boundaries
        for size in [1, 2, 4, 8]:
            max_val = (1 << (size * 8)) - 1
            for val in [0, 1, max_val // 2, max_val - 1, max_val]:
                values.append(struct.pack(f'<Q', val)[:size])
        
        # String patterns
        patterns = [
            b'A' * 256,
            b'\x00' * 256,
            b'\xff' * 256,
            b'%s%s%s%s',
            b'../../../../etc/passwd',
            b'\x90' * 100 + b'\xcc',  # NOP sled + int3
        ]
        values.extend(patterns)
        
        return values
    
    def _mutate_random_bytes(self, data: bytes) -> bytes:
        """Random byte mutation"""
        if not data:
            return os.urandom(random.randint(1, 1024))
        
        data = bytearray(data)
        num_mutations = random.randint(1, min(len(data), 10))
        
        for _ in range(num_mutations):
            pos = random.randint(0, len(data) - 1)
            data[pos] = random.randint(0, 255)
        
        return bytes(data)
    
    def _mutate_bit_flip(self, data: bytes) -> bytes:
        """Bit flip mutation"""
        if not data:
            return b'\x01'
        
        data = bytearray(data)
        bit_pos = random.randint(0, len(data) * 8 - 1)
        byte_pos = bit_pos // 8
        bit_offset = bit_pos % 8
        
        data[byte_pos] ^= (1 << bit_offset)
        return bytes(data)
    
    def _mutate_arithmetic(self, data: bytes) -> bytes:
        """Arithmetic mutation"""
        if len(data) < 4:
            return data
        
        data = bytearray(data)
        pos = random.randint(0, len(data) - 4)
        
        # Interpret as 32-bit integer and modify
        val = struct.unpack('<I', data[pos:pos+4])[0]
        operations = [
            lambda x: x + 1,
            lambda x: x - 1,
            lambda x: x * 2,
            lambda x: x // 2 if x > 0 else 0,
            lambda x: x ^ 0xffffffff
        ]
        
        new_val = random.choice(operations)(val) & 0xffffffff
        struct.pack_into('<I', data, pos, new_val)
        
        return bytes(data)
    
    def _mutate_interesting_values(self, data: bytes) -> bytes:
        """Replace with interesting values"""
        if not self.interesting_values:
            return data
        
        return random.choice(self.interesting_values)
    
    def _mutate_splice(self, data: bytes) -> bytes:
        """Splice mutation - combine parts of data"""
        if len(data) < 2:
            return data
        
        data = bytearray(data)
        pos1 = random.randint(0, len(data) - 1)
        pos2 = random.randint(0, len(data) - 1)
        
        if pos1 > pos2:
            pos1, pos2 = pos2, pos1
        
        # Duplicate or remove section
        if random.choice([True, False]):
            # Duplicate
            section = data[pos1:pos2]
            data[pos1:pos1] = section
        else:
            # Remove
            del data[pos1:pos2]
        
        return bytes(data)
    
    def generate_fuzz_case(self, seed_data: bytes = None) -> FuzzCase:
        """Generate a single fuzz test case"""
        if seed_data is None:
            seed_data = os.urandom(random.randint(1, 512))
        
        # Apply random mutations
        mutated_data = seed_data
        num_mutations = random.randint(1, 5)
        
        for _ in range(num_mutations):
            strategy = random.choice(self.mutation_strategies)
            mutated_data = strategy(mutated_data)
        
        return FuzzCase(
            target=self.target_device,
            input_data=mutated_data,
            ioctl_cmd=random.randint(0, 0xffffffff) if random.random() < 0.5 else None
        )
    
    def execute_fuzz_case(self, case: FuzzCase) -> FuzzCase:
        """Execute a single fuzz test case"""
        start_time = time.time()
        
        try:
            if case.ioctl_cmd is not None:
                # IOCTL fuzzing
                result = self._execute_ioctl(case)
            else:
                # File operation fuzzing
                result = self._execute_file_ops(case)
            
            case.expected_result = result
            
        except Exception as e:
            # Potential crash or hang detected
            case.crash_detected = True
            self.crash_log.append({
                'case': asdict(case),
                'error': str(e),
                'timestamp': time.time()
            })
        
        case.execution_time = time.time() - start_time
        return case
    
    def _execute_ioctl(self, case: FuzzCase) -> int:
        """Execute IOCTL operation"""
        import fcntl
        
        try:
            with open(case.target, 'rb+') as f:
                # Create argument buffer
                if len(case.input_data) > 0:
                    arg_buffer = case.input_data
                else:
                    arg_buffer = b'\x00' * 8
                
                # Execute IOCTL
                result = fcntl.ioctl(f.fileno(), case.ioctl_cmd, arg_buffer)
                return result
        except OSError as e:
            # Expected for many invalid IOCTLs
            return e.errno
    
    def _execute_file_ops(self, case: FuzzCase) -> int:
        """Execute file operations"""
        try:
            with open(case.target, 'wb') as f:
                f.write(case.input_data)
            return 0
        except OSError as e:
            return e.errno
    
    def run_fuzzing_session(self, duration: int = 60, 
                          max_cases: int = None) -> FuzzStats:
        """Run a fuzzing session"""
        self.stats = FuzzStats()
        self.stats.start_time = time.time()
        self.running = True
        
        print(f"Starting fuzzing session on {self.target_device}")
        print(f"Duration: {duration}s, Max cases: {max_cases or 'unlimited'}")
        
        case_count = 0
        start_time = time.time()
        
        try:
            while self.running:
                # Check termination conditions
                elapsed = time.time() - start_time
                if elapsed >= duration:
                    break
                if max_cases and case_count >= max_cases:
                    break
                
                # Generate and execute test case
                case = self.generate_fuzz_case()
                executed_case = self.execute_fuzz_case(case)
                
                # Update statistics
                case_count += 1
                self.stats.total_cases = case_count
                
                if executed_case.crash_detected:
                    self.stats.crashes += 1
                
                if executed_case.execution_time > 1.0:  # Potential hang
                    self.stats.hangs += 1
                
                # Calculate execution rate
                if elapsed > 0:
                    self.stats.exec_per_sec = case_count / elapsed
                
                # Progress reporting
                if case_count % 1000 == 0:
                    print(f"Cases: {case_count}, Crashes: {self.stats.crashes}, "
                          f"Rate: {self.stats.exec_per_sec:.1f}/sec")
        
        except KeyboardInterrupt:
            print("\nFuzzing interrupted by user")
        
        finally:
            self.running = False
            self.stats.unique_crashes = len(set(
                case['error'] for case in self.crash_log
            ))
        
        return self.stats
    
    def parallel_fuzzing(self, num_processes: int = None, 
                        duration: int = 60) -> Dict:
        """Run parallel fuzzing across multiple processes"""
        if num_processes is None:
            num_processes = multiprocessing.cpu_count()
        
        print(f"Starting parallel fuzzing with {num_processes} processes")
        
        # Create process pool
        with multiprocessing.Pool(num_processes) as pool:
            # Start fuzzing processes
            results = []
            for i in range(num_processes):
                result = pool.apply_async(
                    self._worker_process,
                    args=(i, duration)
                )
                results.append(result)
            
            # Collect results
            all_stats = []
            for result in results:
                try:
                    stats = result.get(timeout=duration + 10)
                    all_stats.append(stats)
                except Exception as e:
                    print(f"Worker process error: {e}")
        
        # Aggregate results
        total_stats = FuzzStats()
        for stats in all_stats:
            total_stats.total_cases += stats.total_cases
            total_stats.crashes += stats.crashes
            total_stats.hangs += stats.hangs
            total_stats.exec_per_sec += stats.exec_per_sec
        
        return {
            'total_stats': asdict(total_stats),
            'individual_stats': [asdict(s) for s in all_stats],
            'crash_log': self.crash_log
        }
    
    def _worker_process(self, worker_id: int, duration: int) -> FuzzStats:
        """Worker process for parallel fuzzing"""
        # Create separate fuzzer instance for this process
        fuzzer = KernelFuzzer(self.target_device)
        return fuzzer.run_fuzzing_session(duration)

def main():
    parser = argparse.ArgumentParser(description='Fast Kernel Fuzzer')
    parser.add_argument('target', help='Target device or file')
    parser.add_argument('--duration', '-d', type=int, default=60,
                       help='Fuzzing duration in seconds')
    parser.add_argument('--max-cases', '-m', type=int,
                       help='Maximum number of test cases')
    parser.add_argument('--parallel', '-p', type=int,
                       help='Number of parallel processes')
    parser.add_argument('--output', '-o', help='Output file for results')
    parser.add_argument('--seed-file', help='Seed file for mutations')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.target):
        print(f"Error: Target {args.target} does not exist")
        sys.exit(1)
    
    fuzzer = KernelFuzzer(args.target)
    
    # Load seed data if provided
    seed_data = None
    if args.seed_file and os.path.exists(args.seed_file):
        with open(args.seed_file, 'rb') as f:
            seed_data = f.read()
    
    # Run fuzzing
    if args.parallel:
        results = fuzzer.parallel_fuzzing(args.parallel, args.duration)
    else:
        stats = fuzzer.run_fuzzing_session(args.duration, args.max_cases)
        results = {
            'stats': asdict(stats),
            'crash_log': fuzzer.crash_log
        }
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
    else:
        print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()