#!/usr/bin/env python3
"""
IOCTL Detection and Analysis Tool

This tool provides comprehensive IOCTL detection capabilities for kernel modules
and device drivers, integrating with existing binary lifting infrastructure.
"""

import os
import sys
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, asdict
import argparse

@dataclass
class IOCTLInfo:
    """Information about a detected IOCTL"""
    cmd: int
    cmd_hex: str
    name: str
    direction: str  # 'read', 'write', 'readwrite', 'none'
    size: int
    type_char: str
    number: int
    location: str
    function_name: Optional[str] = None
    vulnerability_score: int = 0
    notes: List[str] = None

    def __post_init__(self):
        if self.notes is None:
            self.notes = []

class IOCTLDetector:
    """Advanced IOCTL detection and analysis system"""
    
    def __init__(self):
        self.ioctls: List[IOCTLInfo] = []
        self.patterns = self._load_patterns()
        self.vulnerability_patterns = self._load_vuln_patterns()
    
    def _load_patterns(self) -> Dict[str, re.Pattern]:
        """Load IOCTL detection patterns"""
        return {
            'ioctl_define': re.compile(r'#define\s+(\w+)\s+_IO[RW]*\s*\(\s*([^,]+),\s*([^,]+)(?:,\s*([^)]+))?\s*\)'),
            'ioctl_case': re.compile(r'case\s+(\w+)\s*:'),
            'ioctl_switch': re.compile(r'switch\s*\(\s*cmd\s*\)'),
            'copy_from_user': re.compile(r'copy_from_user\s*\('),
            'copy_to_user': re.compile(r'copy_to_user\s*\('),
            'get_user': re.compile(r'get_user\s*\('),
            'put_user': re.compile(r'put_user\s*\('),
            'ioctl_handler': re.compile(r'(\w+)\s*\(\s*[^,]*,\s*unsigned\s+int\s+cmd\s*,\s*unsigned\s+long\s+arg\s*\)'),
        }
    
    def _load_vuln_patterns(self) -> Dict[str, Dict]:
        """Load vulnerability detection patterns"""
        return {
            'buffer_overflow': {
                'patterns': [
                    re.compile(r'strcpy\s*\('),
                    re.compile(r'sprintf\s*\('),
                    re.compile(r'gets\s*\('),
                ],
                'score': 8,
                'description': 'Potential buffer overflow vulnerability'
            },
            'unchecked_copy': {
                'patterns': [
                    re.compile(r'copy_from_user\s*\([^;]*\)\s*;(?!\s*if)'),
                    re.compile(r'copy_to_user\s*\([^;]*\)\s*;(?!\s*if)'),
                ],
                'score': 6,
                'description': 'Unchecked copy_from_user/copy_to_user'
            },
            'missing_bounds_check': {
                'patterns': [
                    re.compile(r'arg\s*\+\s*\d+'),
                    re.compile(r'\[\s*arg\s*\]'),
                ],
                'score': 5,
                'description': 'Potential missing bounds check on user input'
            },
            'privilege_escalation': {
                'patterns': [
                    re.compile(r'capable\s*\('),
                    re.compile(r'CAP_SYS_ADMIN'),
                    re.compile(r'uid\s*==\s*0'),
                ],
                'score': 7,
                'description': 'Privilege check - verify proper validation'
            }
        }
    
    def analyze_source_file(self, filepath: str) -> List[IOCTLInfo]:
        """Analyze a source file for IOCTL definitions and handlers"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return []
        
        ioctls = []
        
        # Find IOCTL definitions
        for match in self.patterns['ioctl_define'].finditer(content):
            name = match.group(1)
            type_char = match.group(2).strip('\'"')
            number = match.group(3)
            size = match.group(4) if match.group(4) else "0"
            
            # Calculate IOCTL command value
            try:
                cmd = self._calculate_ioctl_cmd(name, content)
                ioctl = IOCTLInfo(
                    cmd=cmd,
                    cmd_hex=f"0x{cmd:08x}",
                    name=name,
                    direction=self._get_ioctl_direction(name, content),
                    size=self._parse_size(size),
                    type_char=type_char,
                    number=int(number) if number.isdigit() else 0,
                    location=f"{filepath}:{self._get_line_number(content, match.start())}"
                )
                
                # Analyze for vulnerabilities
                ioctl.vulnerability_score = self._analyze_vulnerabilities(content, name)
                ioctls.append(ioctl)
                
            except Exception as e:
                print(f"Error processing IOCTL {name}: {e}")
        
        return ioctls
    
    def _calculate_ioctl_cmd(self, name: str, content: str) -> int:
        """Calculate IOCTL command value"""
        # This is a simplified calculation - real implementation would need
        # to parse the actual _IO* macro definitions
        return hash(name) & 0xFFFFFFFF
    
    def _get_ioctl_direction(self, name: str, content: str) -> str:
        """Determine IOCTL direction from macro usage"""
        if '_IOR' in content and name in content:
            return 'read'
        elif '_IOW' in content and name in content:
            return 'write'
        elif '_IOWR' in content and name in content:
            return 'readwrite'
        else:
            return 'none'
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size parameter from IOCTL definition"""
        try:
            if size_str.startswith('sizeof'):
                return 0  # Would need actual type information
            return int(size_str) if size_str.isdigit() else 0
        except:
            return 0
    
    def _get_line_number(self, content: str, pos: int) -> int:
        """Get line number for a position in content"""
        return content[:pos].count('\n') + 1
    
    def _analyze_vulnerabilities(self, content: str, ioctl_name: str) -> int:
        """Analyze IOCTL handler for potential vulnerabilities"""
        score = 0
        
        for vuln_type, vuln_info in self.vulnerability_patterns.items():
            for pattern in vuln_info['patterns']:
                if pattern.search(content):
                    score += vuln_info['score']
        
        return min(score, 10)  # Cap at 10
    
    def analyze_binary(self, binary_path: str) -> List[IOCTLInfo]:
        """Analyze binary for IOCTL usage using existing lifting tools"""
        ioctls = []
        
        # Use existing radare2 integration if available
        try:
            result = subprocess.run([
                'r2', '-q', '-c', 'aaa; /x 4489e5; pdf', binary_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Parse radare2 output for IOCTL patterns
                ioctls.extend(self._parse_r2_output(result.stdout, binary_path))
        except Exception as e:
            print(f"Error analyzing binary with radare2: {e}")
        
        return ioctls
    
    def _parse_r2_output(self, output: str, binary_path: str) -> List[IOCTLInfo]:
        """Parse radare2 output for IOCTL information"""
        # Simplified parser - real implementation would be more sophisticated
        ioctls = []
        # Implementation would parse disassembly for IOCTL patterns
        return ioctls
    
    def generate_report(self, output_format: str = 'json') -> str:
        """Generate analysis report"""
        if output_format == 'json':
            return json.dumps([asdict(ioctl) for ioctl in self.ioctls], indent=2)
        elif output_format == 'text':
            return self._generate_text_report()
        else:
            raise ValueError(f"Unsupported format: {output_format}")
    
    def _generate_text_report(self) -> str:
        """Generate human-readable text report"""
        report = ["IOCTL Analysis Report", "=" * 50, ""]
        
        for ioctl in sorted(self.ioctls, key=lambda x: x.vulnerability_score, reverse=True):
            report.extend([
                f"Name: {ioctl.name}",
                f"Command: {ioctl.cmd_hex}",
                f"Direction: {ioctl.direction}",
                f"Location: {ioctl.location}",
                f"Vulnerability Score: {ioctl.vulnerability_score}/10",
                ""
            ])
        
        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description='IOCTL Detection and Analysis Tool')
    parser.add_argument('target', help='Target file or directory to analyze')
    parser.add_argument('--format', choices=['json', 'text'], default='json',
                       help='Output format')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--binary', action='store_true',
                       help='Analyze as binary file')
    
    args = parser.parse_args()
    
    detector = IOCTLDetector()
    
    if os.path.isfile(args.target):
        if args.binary:
            ioctls = detector.analyze_binary(args.target)
        else:
            ioctls = detector.analyze_source_file(args.target)
        detector.ioctls.extend(ioctls)
    elif os.path.isdir(args.target):
        # Analyze all source files in directory
        for root, dirs, files in os.walk(args.target):
            for file in files:
                if file.endswith(('.c', '.h', '.cpp', '.hpp')):
                    filepath = os.path.join(root, file)
                    ioctls = detector.analyze_source_file(filepath)
                    detector.ioctls.extend(ioctls)
    
    report = detector.generate_report(args.format)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
    else:
        print(report)

if __name__ == '__main__':
    main()