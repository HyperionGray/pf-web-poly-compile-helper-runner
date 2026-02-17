#!/usr/bin/env python3
"""
Radare2 Kernel Analysis Plugin

Provides automated kernel-specific analysis capabilities for radare2,
including IOCTL detection, vulnerability identification, and CFG analysis.
"""

import r2pipe
import json
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

@dataclass
class KernelFunction:
    """Kernel function information"""
    name: str
    address: int
    size: int
    calls: List[str]
    vulnerabilities: List[str]
    ioctl_cmds: List[int]

class R2KernelAnalyzer:
    """Radare2-based kernel analyzer"""
    
    def __init__(self, binary_path: str):
        self.r2 = r2pipe.open(binary_path)
        self.r2.cmd('aaa')  # Analyze all
        self.vuln_patterns = self._load_vuln_patterns()
    
    def _load_vuln_patterns(self) -> Dict[str, List[str]]:
        """Load vulnerability detection patterns"""
        return {
            'buffer_overflow': ['strcpy', 'sprintf', 'gets', 'strcat'],
            'format_string': ['printf', 'sprintf', 'fprintf'],
            'use_after_free': ['free', 'kfree', 'vfree'],
            'double_free': ['free', 'kfree'],
            'null_deref': ['NULL'],
            'race_condition': ['mutex', 'spinlock', 'atomic']
        }
    
    def analyze_ioctls(self) -> List[Dict]:
        """Analyze IOCTL handlers in the binary"""
        ioctls = []
        
        # Find IOCTL-related functions
        functions = self.r2.cmdj('aflj')
        
        for func in functions:
            if any(keyword in func['name'].lower() 
                   for keyword in ['ioctl', 'compat_ioctl', 'unlocked_ioctl']):
                
                ioctl_info = self._analyze_ioctl_function(func)
                if ioctl_info:
                    ioctls.append(ioctl_info)
        
        return ioctls
    
    def _analyze_ioctl_function(self, func: Dict) -> Optional[Dict]:
        """Analyze individual IOCTL function"""
        self.r2.cmd(f's {func["offset"]}')
        disasm = self.r2.cmd('pdf')
        
        # Extract IOCTL commands
        ioctl_cmds = self._extract_ioctl_commands(disasm)
        
        # Check for vulnerabilities
        vulns = self._check_vulnerabilities(disasm)
        
        return {
            'name': func['name'],
            'address': func['offset'],
            'size': func['size'],
            'ioctl_commands': ioctl_cmds,
            'vulnerabilities': vulns,
            'disassembly': disasm
        }
    
    def _extract_ioctl_commands(self, disasm: str) -> List[int]:
        """Extract IOCTL command values from disassembly"""
        commands = []
        
        # Look for immediate values that might be IOCTL commands
        pattern = r'cmp.*0x([0-9a-fA-F]+)'
        matches = re.findall(pattern, disasm)
        
        for match in matches:
            try:
                cmd = int(match, 16)
                if 0x1000 <= cmd <= 0xffffffff:  # Reasonable IOCTL range
                    commands.append(cmd)
            except ValueError:
                continue
        
        return commands
    
    def _check_vulnerabilities(self, disasm: str) -> List[str]:
        """Check for vulnerability patterns in disassembly"""
        vulns = []
        
        for vuln_type, patterns in self.vuln_patterns.items():
            for pattern in patterns:
                if pattern in disasm:
                    vulns.append(vuln_type)
                    break
        
        return vulns
    
    def generate_cfg(self, function_name: str = None) -> Dict:
        """Generate control flow graph"""
        if function_name:
            self.r2.cmd(f's sym.{function_name}')
        
        # Generate CFG in JSON format
        cfg_json = self.r2.cmdj('agfj')
        return cfg_json
    
    def find_dangerous_functions(self) -> List[Dict]:
        """Find potentially dangerous function calls"""
        dangerous = []
        functions = self.r2.cmdj('aflj')
        
        dangerous_funcs = [
            'strcpy', 'sprintf', 'gets', 'strcat',
            'memcpy', 'memmove', 'copy_from_user',
            'copy_to_user', '__copy_from_user'
        ]
        
        for func in functions:
            self.r2.cmd(f's {func["offset"]}')
            xrefs = self.r2.cmdj('axtj')
            
            for xref in xrefs or []:
                if any(df in xref.get('opcode', '') for df in dangerous_funcs):
                    dangerous.append({
                        'function': func['name'],
                        'address': func['offset'],
                        'dangerous_call': xref.get('opcode', ''),
                        'call_address': xref.get('from', 0)
                    })
        
        return dangerous
    
    def close(self):
        """Close radare2 session"""
        self.r2.quit()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Radare2 Kernel Analysis')
    parser.add_argument('binary', help='Binary file to analyze')
    parser.add_argument('--ioctls', action='store_true',
                       help='Analyze IOCTL handlers')
    parser.add_argument('--dangerous', action='store_true',
                       help='Find dangerous function calls')
    parser.add_argument('--cfg', help='Generate CFG for function')
    parser.add_argument('--output', '-o', help='Output file')
    
    args = parser.parse_args()
    
    analyzer = R2KernelAnalyzer(args.binary)
    
    results = {}
    
    try:
        if args.ioctls:
            results['ioctls'] = analyzer.analyze_ioctls()
        
        if args.dangerous:
            results['dangerous_functions'] = analyzer.find_dangerous_functions()
        
        if args.cfg:
            results['cfg'] = analyzer.generate_cfg(args.cfg)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
        else:
            print(json.dumps(results, indent=2))
    
    finally:
        analyzer.close()

if __name__ == '__main__':
    main()