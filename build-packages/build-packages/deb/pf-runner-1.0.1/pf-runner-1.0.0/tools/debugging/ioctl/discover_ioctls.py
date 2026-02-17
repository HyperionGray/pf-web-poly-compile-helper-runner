#!/usr/bin/env python3
"""
IOCTL Discovery Tool
Analyzes kernel drivers and binaries to discover IOCTL codes and their handlers.
"""

import sys
import os
import re
import subprocess
import json
from pathlib import Path

class IOCTLDiscovery:
    """Discover IOCTLs in kernel modules and drivers"""
    
    # Common IOCTL magic numbers and patterns
    IOCTL_PATTERNS = [
        rb'_IO[RW]*\s*\(',           # Linux IOCTL macros
        rb'IOCTL_[A-Z_]+',           # Common IOCTL naming
        rb'0x[0-9A-Fa-f]{8}',        # IOCTL codes in hex
    ]
    
    def __init__(self, binary_path, output_dir=None):
        self.binary_path = Path(binary_path)
        self.output_dir = Path(output_dir) if output_dir else Path('./output')
        self.ioctls = []
        
        if not self.binary_path.exists():
            raise FileNotFoundError(f"Binary not found: {binary_path}")
            
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_with_strings(self):
        """Extract potential IOCTL strings from binary"""
        print(f"[*] Analyzing strings in {self.binary_path.name}...")
        
        try:
            result = subprocess.run(
                ['strings', str(self.binary_path)],
                capture_output=True,
                text=True
            )
            
            ioctl_strings = []
            for line in result.stdout.splitlines():
                if 'IOCTL' in line.upper() or '_IO' in line:
                    ioctl_strings.append(line.strip())
            
            print(f"[+] Found {len(ioctl_strings)} potential IOCTL strings")
            return ioctl_strings
            
        except Exception as e:
            print(f"[-] Error running strings: {e}")
            return []
    
    def analyze_with_objdump(self):
        """Disassemble binary to find IOCTL patterns"""
        print(f"[*] Disassembling with objdump...")
        
        try:
            result = subprocess.run(
                ['objdump', '-d', str(self.binary_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Look for IOCTL handler patterns
            ioctl_handlers = []
            lines = result.stdout.splitlines()
            
            for i, line in enumerate(lines):
                # Look for common IOCTL switch/case patterns
                if 'cmp' in line and i+2 < len(lines):
                    # Check next few lines for jump patterns
                    context = '\n'.join(lines[i:i+5])
                    if 'je' in context or 'jne' in context:
                        ioctl_handlers.append({
                            'line': line.strip(),
                            'context': context
                        })
            
            print(f"[+] Found {len(ioctl_handlers)} potential IOCTL handlers")
            return ioctl_handlers
            
        except subprocess.TimeoutExpired:
            print("[-] objdump timed out")
            return []
        except Exception as e:
            print(f"[-] Error running objdump: {e}")
            return []
    
    def analyze_with_radare2(self):
        """Use radare2 for deeper analysis"""
        print(f"[*] Analyzing with radare2...")
        
        try:
            # Check if r2 is available
            subprocess.run(['r2', '-v'], capture_output=True, check=True)
            
            # Run r2 commands to find IOCTLs
            r2_script = f"""
            aa
            afl~ioctl
            iz~IOCTL
            """
            
            result = subprocess.run(
                ['r2', '-q', '-c', r2_script, str(self.binary_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            r2_findings = result.stdout.strip().splitlines()
            print(f"[+] radare2 found {len(r2_findings)} IOCTL-related items")
            return r2_findings
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[-] radare2 not available, skipping")
            return []
        except subprocess.TimeoutExpired:
            print("[-] radare2 analysis timed out")
            return []
        except Exception as e:
            print(f"[-] Error with radare2: {e}")
            return []
    
    def extract_ioctl_codes(self, data):
        """Extract IOCTL command codes from various data sources"""
        codes = set()
        
        # Extract hex codes
        hex_pattern = re.compile(r'0x[0-9A-Fa-f]{4,8}')
        for item in data:
            if isinstance(item, str):
                matches = hex_pattern.findall(item)
                codes.update(matches)
            elif isinstance(item, dict):
                text = str(item)
                matches = hex_pattern.findall(text)
                codes.update(matches)
        
        return sorted(list(codes))
    
    def discover(self):
        """Run complete IOCTL discovery"""
        print(f"\n=== IOCTL Discovery for {self.binary_path.name} ===\n")
        
        # Gather data from multiple sources
        strings_data = self.analyze_with_strings()
        objdump_data = self.analyze_with_objdump()
        r2_data = self.analyze_with_radare2()
        
        # Extract IOCTL codes
        all_data = strings_data + [str(x) for x in objdump_data] + r2_data
        ioctl_codes = self.extract_ioctl_codes(all_data)
        
        # Build results
        results = {
            'binary': str(self.binary_path),
            'discovered_codes': ioctl_codes,
            'strings': strings_data[:20],  # Limit output
            'handlers': len(objdump_data),
            'r2_findings': len(r2_data)
        }
        
        # Save results
        output_file = self.output_dir / f"{self.binary_path.stem}_ioctls.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n[+] Discovery complete!")
        print(f"[+] Found {len(ioctl_codes)} potential IOCTL codes")
        print(f"[+] Results saved to: {output_file}")
        
        # Print summary
        if ioctl_codes:
            print(f"\n[*] Discovered IOCTL codes:")
            for code in ioctl_codes[:10]:  # Show first 10
                print(f"    {code}")
            if len(ioctl_codes) > 10:
                print(f"    ... and {len(ioctl_codes) - 10} more")
        
        return results

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <binary_path> [output_dir]")
        print(f"\nExample:")
        print(f"  {sys.argv[0]} /path/to/driver.ko ./output")
        sys.exit(1)
    
    binary_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else './output'
    
    try:
        discovery = IOCTLDiscovery(binary_path, output_dir)
        discovery.discover()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
