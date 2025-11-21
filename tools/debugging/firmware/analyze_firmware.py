#!/usr/bin/env python3
"""
Firmware Analyzer
Analyzes firmware images for security issues and extracts metadata.
"""

import sys
import os
import subprocess
import hashlib
from pathlib import Path

class FirmwareAnalyzer:
    """Analyze firmware images for vulnerabilities and interesting patterns"""
    
    def __init__(self, image_path):
        self.image_path = Path(image_path)
        if not self.image_path.exists():
            raise FileNotFoundError(f"Firmware image not found: {image_path}")
        
        self.results = {
            'file': str(self.image_path),
            'size': self.image_path.stat().st_size,
            'hashes': {},
            'file_type': None,
            'entropy': 0.0,
            'strings': [],
            'vulnerabilities': []
        }
    
    def calculate_hashes(self):
        """Calculate file hashes"""
        print(f"[*] Calculating hashes...")
        
        with open(self.image_path, 'rb') as f:
            data = f.read()
            
        self.results['hashes'] = {
            'md5': hashlib.md5(data).hexdigest(),
            'sha1': hashlib.sha1(data).hexdigest(),
            'sha256': hashlib.sha256(data).hexdigest()
        }
        
        print(f"[+] MD5:    {self.results['hashes']['md5']}")
        print(f"[+] SHA256: {self.results['hashes']['sha256']}")
    
    def identify_file_type(self):
        """Identify firmware file type"""
        print(f"\n[*] Identifying file type...")
        
        try:
            # Use file command
            result = subprocess.run(
                ['file', '-b', str(self.image_path)],
                capture_output=True,
                text=True
            )
            self.results['file_type'] = result.stdout.strip()
            print(f"[+] Type: {self.results['file_type']}")
        except Exception as e:
            print(f"[-] Could not identify file type: {e}")
    
    def calculate_entropy(self):
        """Calculate Shannon entropy (indicates encryption/compression)"""
        print(f"\n[*] Calculating entropy...")
        
        try:
            with open(self.image_path, 'rb') as f:
                data = f.read(1024 * 1024)  # First 1MB
            
            if not data:
                return
            
            # Calculate byte frequency
            freq = [0] * 256
            for byte in data:
                freq[byte] += 1
            
            # Calculate entropy
            import math
            entropy = 0.0
            for count in freq:
                if count > 0:
                    p = count / len(data)
                    entropy -= p * math.log2(p)
            
            self.results['entropy'] = entropy
            print(f"[+] Entropy: {entropy:.2f} bits/byte")
            
            if entropy > 7.5:
                print(f"[!] High entropy detected - likely encrypted or compressed")
            elif entropy < 4.0:
                print(f"[!] Low entropy - likely unencrypted with repetitive data")
                
        except Exception as e:
            print(f"[-] Could not calculate entropy: {e}")
    
    def extract_strings(self):
        """Extract interesting strings from firmware"""
        print(f"\n[*] Extracting interesting strings...")
        
        try:
            result = subprocess.run(
                ['strings', '-n', '6', str(self.image_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            all_strings = result.stdout.splitlines()
            
            # Filter for interesting patterns
            interesting_patterns = [
                'password', 'passwd', 'admin', 'root', 'user',
                'key', 'secret', 'token', 'api',
                'http://', 'https://', 'ftp://',
                'telnet', 'ssh', 'uart',
                '/dev/', '/etc/', '/bin/',
                'debug', 'test', 'backdoor'
            ]
            
            interesting = []
            for s in all_strings:
                s_lower = s.lower()
                if any(pattern in s_lower for pattern in interesting_patterns):
                    interesting.append(s)
            
            self.results['strings'] = interesting[:50]  # Limit
            
            print(f"[+] Found {len(all_strings)} total strings")
            print(f"[+] Found {len(interesting)} interesting strings")
            
            if interesting:
                print(f"\n[*] Sample interesting strings:")
                for s in interesting[:10]:
                    print(f"    {s}")
                    
        except Exception as e:
            print(f"[-] Could not extract strings: {e}")
    
    def scan_vulnerabilities(self):
        """Scan for common firmware vulnerabilities"""
        print(f"\n[*] Scanning for common vulnerabilities...")
        
        vulns = []
        
        try:
            with open(self.image_path, 'rb') as f:
                # Read chunks to avoid memory issues
                chunk_size = 1024 * 1024
                data = f.read(chunk_size)
            
            # Check for hardcoded credentials
            cred_patterns = [
                (b'admin:admin', 'Hardcoded default credentials'),
                (b'root:root', 'Hardcoded root credentials'),
                (b'password=', 'Cleartext password'),
                (b'secret=', 'Cleartext secret'),
            ]
            
            for pattern, desc in cred_patterns:
                if pattern in data:
                    vulns.append({
                        'type': 'hardcoded_credential',
                        'description': desc,
                        'severity': 'HIGH'
                    })
            
            # Check for debug interfaces
            debug_patterns = [
                (b'UART', 'UART debug interface'),
                (b'JTAG', 'JTAG debug interface'),
                (b'/bin/sh', 'Shell access'),
                (b'telnetd', 'Telnet daemon'),
            ]
            
            for pattern, desc in debug_patterns:
                if pattern in data:
                    vulns.append({
                        'type': 'debug_interface',
                        'description': desc,
                        'severity': 'MEDIUM'
                    })
            
            self.results['vulnerabilities'] = vulns
            
            if vulns:
                print(f"[!] Found {len(vulns)} potential vulnerabilities:")
                for vuln in vulns:
                    print(f"    [{vuln['severity']}] {vuln['description']}")
            else:
                print(f"[+] No obvious vulnerabilities detected")
                
        except Exception as e:
            print(f"[-] Vulnerability scan error: {e}")
    
    def analyze(self):
        """Run complete firmware analysis"""
        print(f"\n=== Firmware Analysis for {self.image_path.name} ===\n")
        print(f"Size: {self.results['size']:,} bytes ({self.results['size'] / 1024 / 1024:.2f} MB)")
        
        self.calculate_hashes()
        self.identify_file_type()
        self.calculate_entropy()
        self.extract_strings()
        self.scan_vulnerabilities()
        
        print(f"\n=== Analysis Complete ===")
        print(f"\nRecommendations:")
        print(f"  1. Run 'binwalk -e {self.image_path}' to extract filesystem")
        print(f"  2. Use 'pf firmware-extract image={self.image_path}' for automated extraction")
        print(f"  3. Examine extracted files for additional vulnerabilities")
        
        return self.results

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <firmware_image>")
        print(f"\nExample:")
        print(f"  {sys.argv[0]} /path/to/firmware.bin")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    try:
        analyzer = FirmwareAnalyzer(image_path)
        analyzer.analyze()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
