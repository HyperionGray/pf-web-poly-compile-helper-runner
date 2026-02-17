#!/usr/bin/env python3
"""
IOCTL Analyzer
Analyzes IOCTL structure and parameter expectations in drivers.
"""

import sys
import subprocess
import re
from pathlib import Path

class IOCTLAnalyzer:
    """Analyze IOCTL handlers and their parameter structures"""
    
    def __init__(self, binary_path):
        self.binary_path = Path(binary_path)
        if not self.binary_path.exists():
            raise FileNotFoundError(f"Binary not found: {binary_path}")
    
    def analyze_structure_sizes(self):
        """Analyze likely structure sizes from IOCTL handlers"""
        print(f"[*] Analyzing structure sizes...")
        
        try:
            # Use objdump to find size comparisons
            result = subprocess.run(
                ['objdump', '-d', str(self.binary_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            sizes = set()
            for line in result.stdout.splitlines():
                # Look for size comparisons (cmp with immediate values)
                match = re.search(r'cmp.*\$0x([0-9a-f]+)', line)
                if match:
                    size = int(match.group(1), 16)
                    if 4 <= size <= 4096:  # Reasonable struct sizes
                        sizes.add(size)
            
            print(f"[+] Found {len(sizes)} potential structure sizes")
            return sorted(sizes)
            
        except Exception as e:
            print(f"[-] Error analyzing sizes: {e}")
            return []
    
    def find_validation_checks(self):
        """Find input validation in IOCTL handlers"""
        print(f"[*] Searching for validation checks...")
        
        try:
            result = subprocess.run(
                ['objdump', '-d', str(self.binary_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            validations = []
            lines = result.stdout.splitlines()
            
            for i, line in enumerate(lines):
                # Look for bounds checking patterns
                if 'cmp' in line and ('jb' in lines[i+1:i+3] or 'ja' in lines[i+1:i+3]):
                    validations.append({
                        'type': 'bounds_check',
                        'line': line.strip()
                    })
                # Look for NULL checks
                elif 'test' in line and 'jz' in lines[i+1:i+2]:
                    validations.append({
                        'type': 'null_check',
                        'line': line.strip()
                    })
            
            print(f"[+] Found {len(validations)} validation checks")
            return validations
            
        except Exception as e:
            print(f"[-] Error finding validations: {e}")
            return []
    
    def detect_ioctl_patterns(self):
        """Detect common IOCTL implementation patterns"""
        print(f"[*] Detecting IOCTL patterns...")
        
        patterns = {
            'switch_statement': False,
            'function_table': False,
            'if_else_chain': False
        }
        
        try:
            result = subprocess.run(
                ['objdump', '-d', str(self.binary_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            disasm = result.stdout
            
            # Look for switch statement (jump table)
            if 'jmpq   *' in disasm or 'jmp    *' in disasm:
                patterns['switch_statement'] = True
            
            # Look for function pointer table
            if re.search(r'call.*\[.*\]', disasm):
                patterns['function_table'] = True
            
            # Look for if-else chain (multiple conditional jumps)
            lines = disasm.splitlines()
            consecutive_cmps = 0
            for line in lines:
                if 'cmp' in line:
                    consecutive_cmps += 1
                    if consecutive_cmps >= 3:
                        patterns['if_else_chain'] = True
                        break
                else:
                    consecutive_cmps = 0
            
            print(f"[+] Detected patterns: {patterns}")
            return patterns
            
        except Exception as e:
            print(f"[-] Error detecting patterns: {e}")
            return patterns
    
    def analyze(self):
        """Run complete IOCTL structure analysis"""
        print(f"\n=== IOCTL Structure Analysis for {self.binary_path.name} ===\n")
        
        sizes = self.analyze_structure_sizes()
        validations = self.find_validation_checks()
        patterns = self.detect_ioctl_patterns()
        
        print(f"\n=== Analysis Results ===")
        
        if sizes:
            print(f"\nPotential structure sizes (bytes):")
            for size in sizes[:20]:
                print(f"  {size} (0x{size:x})")
            if len(sizes) > 20:
                print(f"  ... and {len(sizes) - 20} more")
        
        if validations:
            print(f"\nValidation checks found: {len(validations)}")
            print(f"  Bounds checks: {sum(1 for v in validations if v['type'] == 'bounds_check')}")
            print(f"  NULL checks: {sum(1 for v in validations if v['type'] == 'null_check')}")
        
        print(f"\nIOCTL Implementation Pattern:")
        if patterns['switch_statement']:
            print(f"  ✓ Uses switch statement (jump table)")
        if patterns['function_table']:
            print(f"  ✓ Uses function pointer table")
        if patterns['if_else_chain']:
            print(f"  ✓ Uses if-else chain")
        
        print(f"\n[+] Analysis complete!")
        
        return {
            'sizes': sizes,
            'validations': len(validations),
            'patterns': patterns
        }

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <binary_path>")
        print(f"\nExample:")
        print(f"  {sys.argv[0]} /path/to/driver.ko")
        sys.exit(1)
    
    binary_path = sys.argv[1]
    
    try:
        analyzer = IOCTLAnalyzer(binary_path)
        analyzer.analyze()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
