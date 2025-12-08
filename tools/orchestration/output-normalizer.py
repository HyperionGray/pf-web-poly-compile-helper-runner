#!/usr/bin/env python3

"""
Output Normalizer for Security Tools
Standardizes output from different security tools into consistent JSON format
"""

import json
import re
import sys
import argparse
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class NormalizedResult:
    """Standardized result format for all security tools"""
    tool_name: str
    tool_version: str
    target: str
    timestamp: str
    success: bool
    raw_output: str
    parsed_data: Dict[str, Any]
    findings: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class OutputNormalizer:
    """Normalizes output from various security tools"""
    
    def __init__(self):
        self.parsers = {
            'checksec': self.parse_checksec,
            'file': self.parse_file,
            'strings': self.parse_strings,
            'readelf': self.parse_readelf,
            'objdump': self.parse_objdump,
            'ROPgadget': self.parse_ropgadget,
            'radare2': self.parse_radare2,
            'nmap': self.parse_nmap,
            'gdb': self.parse_gdb,
            'lldb': self.parse_lldb
        }
    
    def normalize(self, tool_name: str, raw_output: str, target: str, 
                  tool_version: str = "unknown") -> NormalizedResult:
        """Normalize output from any supported tool"""
        
        parser = self.parsers.get(tool_name, self.parse_generic)
        parsed_data, findings = parser(raw_output)
        
        return NormalizedResult(
            tool_name=tool_name,
            tool_version=tool_version,
            target=target,
            timestamp=datetime.now().isoformat(),
            success=True,
            raw_output=raw_output,
            parsed_data=parsed_data,
            findings=findings,
            metadata={"parser_version": "1.0"}
        )
    
    def parse_checksec(self, output: str) -> tuple:
        """Parse checksec output"""
        findings = []
        parsed_data = {}
        
        # Parse security features
        features = {
            'canary': 'canary found' in output.lower(),
            'nx': 'nx enabled' in output.lower(),
            'pie': 'pie enabled' in output.lower() or 'dso' in output.lower(),
            'relro': 'full relro' in output.lower() or 'partial relro' in output.lower(),
            'rpath': 'rpath' in output.lower(),
            'runpath': 'runpath' in output.lower(),
            'symbols': 'no symbols' not in output.lower()
        }
        
        parsed_data['security_features'] = features
        
        # Generate findings based on missing protections
        if not features['canary']:
            findings.append({
                'type': 'vulnerability',
                'severity': 'medium',
                'title': 'Stack Canary Disabled',
                'description': 'Binary lacks stack canary protection, vulnerable to buffer overflows'
            })
        
        if not features['nx']:
            findings.append({
                'type': 'vulnerability',
                'severity': 'high',
                'title': 'NX Bit Disabled',
                'description': 'Executable stack allows shellcode execution'
            })
        
        if not features['pie']:
            findings.append({
                'type': 'vulnerability',
                'severity': 'medium',
                'title': 'PIE Disabled',
                'description': 'Predictable memory layout aids exploitation'
            })
        
        return parsed_data, findings
    
    def parse_file(self, output: str) -> tuple:
        """Parse file command output"""
        parsed_data = {}
        findings = []
        
        # Extract file type information
        if 'ELF' in output:
            parsed_data['file_type'] = 'ELF'
            if '64-bit' in output:
                parsed_data['architecture'] = 'x86_64'
            elif '32-bit' in output:
                parsed_data['architecture'] = 'x86'
            
            if 'not stripped' in output:
                findings.append({
                    'type': 'info',
                    'severity': 'low',
                    'title': 'Debug Symbols Present',
                    'description': 'Binary contains debug symbols, easier to analyze'
                })
            
            if 'statically linked' in output:
                findings.append({
                    'type': 'info',
                    'severity': 'low',
                    'title': 'Statically Linked',
                    'description': 'All dependencies are included in the binary'
                })
        
        parsed_data['raw_file_info'] = output.strip()
        return parsed_data, findings
    
    def parse_strings(self, output: str) -> tuple:
        """Parse strings output"""
        strings_list = [s.strip() for s in output.split('\n') if s.strip()]
        
        parsed_data = {
            'string_count': len(strings_list),
            'strings': strings_list[:100]  # Limit to first 100
        }
        
        findings = []
        
        # Look for interesting strings
        interesting_patterns = {
            'passwords': [r'password', r'passwd', r'pwd'],
            'urls': [r'https?://[^\s]+'],
            'file_paths': [r'/[a-zA-Z0-9_/.-]+'],
            'functions': [r'[a-zA-Z_][a-zA-Z0-9_]*\(\)'],
            'format_strings': [r'%[sdxp]']
        }
        
        for category, patterns in interesting_patterns.items():
            matches = []
            for pattern in patterns:
                for string in strings_list:
                    if re.search(pattern, string, re.IGNORECASE):
                        matches.append(string)
            
            if matches:
                findings.append({
                    'type': 'info',
                    'severity': 'low',
                    'title': f'Interesting {category.title()} Found',
                    'description': f'Found {len(matches)} {category}',
                    'data': matches[:10]  # Limit to first 10
                })
        
        return parsed_data, findings
    
    def parse_readelf(self, output: str) -> tuple:
        """Parse readelf output"""
        parsed_data = {}
        findings = []
        
        # Parse sections
        sections = []
        in_section_headers = False
        
        for line in output.split('\n'):
            if 'Section Headers:' in line:
                in_section_headers = True
                continue
            elif in_section_headers and line.strip().startswith('['):
                parts = line.split()
                if len(parts) >= 2:
                    sections.append(parts[1])
        
        parsed_data['sections'] = sections
        
        # Look for interesting sections
        dangerous_sections = ['.got', '.plt', '.dynamic']
        for section in dangerous_sections:
            if section in sections:
                findings.append({
                    'type': 'info',
                    'severity': 'low',
                    'title': f'Section {section} Present',
                    'description': f'Binary contains {section} section'
                })
        
        return parsed_data, findings
    
    def parse_objdump(self, output: str) -> tuple:
        """Parse objdump disassembly output"""
        parsed_data = {}
        findings = []
        
        # Count instructions
        instruction_count = len([line for line in output.split('\n') 
                               if re.match(r'\s*[0-9a-f]+:', line)])
        
        parsed_data['instruction_count'] = instruction_count
        
        # Look for dangerous functions
        dangerous_functions = ['strcpy', 'strcat', 'sprintf', 'gets', 'scanf']
        found_functions = []
        
        for func in dangerous_functions:
            if func in output:
                found_functions.append(func)
        
        if found_functions:
            findings.append({
                'type': 'vulnerability',
                'severity': 'medium',
                'title': 'Dangerous Functions Found',
                'description': f'Binary uses potentially unsafe functions: {", ".join(found_functions)}',
                'data': found_functions
            })
        
        return parsed_data, findings
    
    def parse_ropgadget(self, output: str) -> tuple:
        """Parse ROPgadget output"""
        gadgets = []
        
        for line in output.split('\n'):
            if ' : ' in line and ('pop' in line or 'ret' in line):
                parts = line.split(' : ')
                if len(parts) == 2:
                    address = parts[0].strip()
                    instruction = parts[1].strip()
                    gadgets.append({'address': address, 'instruction': instruction})
        
        parsed_data = {
            'gadget_count': len(gadgets),
            'gadgets': gadgets[:50]  # Limit to first 50
        }
        
        findings = []
        if len(gadgets) > 10:
            findings.append({
                'type': 'info',
                'severity': 'medium',
                'title': 'ROP Gadgets Available',
                'description': f'Found {len(gadgets)} ROP gadgets, exploitation may be possible'
            })
        
        return parsed_data, findings
    
    def parse_radare2(self, output: str) -> tuple:
        """Parse radare2 output"""
        parsed_data = {'raw_analysis': output}
        findings = []
        
        # Basic analysis of radare2 output
        if 'main' in output:
            findings.append({
                'type': 'info',
                'severity': 'low',
                'title': 'Main Function Found',
                'description': 'Successfully identified main function'
            })
        
        return parsed_data, findings
    
    def parse_nmap(self, output: str) -> tuple:
        """Parse nmap output"""
        parsed_data = {}
        findings = []
        
        # Parse open ports
        open_ports = []
        for line in output.split('\n'):
            if '/tcp' in line and 'open' in line:
                port_info = line.split()
                if len(port_info) >= 3:
                    port = port_info[0].split('/')[0]
                    service = port_info[2] if len(port_info) > 2 else 'unknown'
                    open_ports.append({'port': port, 'service': service})
        
        parsed_data['open_ports'] = open_ports
        
        for port_info in open_ports:
            findings.append({
                'type': 'info',
                'severity': 'low',
                'title': f'Open Port {port_info["port"]}',
                'description': f'Service: {port_info["service"]}'
            })
        
        return parsed_data, findings
    
    def parse_gdb(self, output: str) -> tuple:
        """Parse GDB output"""
        return {'raw_gdb_output': output}, []
    
    def parse_lldb(self, output: str) -> tuple:
        """Parse LLDB output"""
        return {'raw_lldb_output': output}, []
    
    def parse_generic(self, output: str) -> tuple:
        """Generic parser for unknown tools"""
        return {'raw_output': output}, []

def main():
    parser = argparse.ArgumentParser(description='Normalize security tool output')
    parser.add_argument('tool', help='Tool name')
    parser.add_argument('target', help='Target that was analyzed')
    parser.add_argument('--input', '-i', help='Input file (default: stdin)')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--version', help='Tool version')
    
    args = parser.parse_args()
    
    # Read input
    if args.input:
        with open(args.input, 'r') as f:
            raw_output = f.read()
    else:
        raw_output = sys.stdin.read()
    
    # Normalize output
    normalizer = OutputNormalizer()
    result = normalizer.normalize(args.tool, raw_output, args.target, args.version or "unknown")
    
    # Write output
    output_json = json.dumps(asdict(result), indent=2)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_json)
    else:
        print(output_json)

if __name__ == '__main__':
    main()