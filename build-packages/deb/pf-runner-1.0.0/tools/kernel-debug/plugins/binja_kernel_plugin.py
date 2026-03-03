#!/usr/bin/env python3
"""
Binary Ninja Kernel Analysis Plugin

Provides automated kernel vulnerability detection and analysis for Binary Ninja.
"""

try:
    import binaryninja as bn
    from binaryninja import *
    BINJA_AVAILABLE = True
except ImportError:
    BINJA_AVAILABLE = False
    print("Binary Ninja not available - plugin will run in standalone mode")

import re
from typing import List, Dict, Optional, Tuple

class KernelVulnAnalyzer:
    """Kernel vulnerability analyzer for Binary Ninja"""
    
    def __init__(self, bv=None):
        self.bv = bv
        self.vulnerabilities = []
        self.ioctl_handlers = []
        
        # Vulnerability patterns
        self.vuln_patterns = {
            'buffer_overflow': [
                'strcpy', 'sprintf', 'gets', 'strcat', 'strcpy_s'
            ],
            'format_string': [
                'printf', 'sprintf', 'fprintf', 'snprintf'
            ],
            'use_after_free': [
                'free', 'kfree', 'vfree', 'kzfree'
            ],
            'double_free': [
                'free', 'kfree', 'vfree'
            ],
            'integer_overflow': [
                'malloc', 'kmalloc', 'vmalloc', 'kcalloc'
            ],
            'race_condition': [
                'mutex_lock', 'spin_lock', 'atomic_inc', 'atomic_dec'
            ]
        }
    
    def analyze_binary(self, binary_path: str = None):
        """Analyze binary for kernel vulnerabilities"""
        if not BINJA_AVAILABLE:
            print("Binary Ninja not available - using standalone analysis")
            return self._standalone_analysis(binary_path)
        
        if not self.bv and binary_path:
            self.bv = bn.open_view(binary_path)
        
        if not self.bv:
            raise ValueError("No binary view available")
        
        # Analyze functions
        for func in self.bv.functions:
            self._analyze_function(func)
        
        # Find IOCTL handlers
        self._find_ioctl_handlers()
        
        return {
            'vulnerabilities': self.vulnerabilities,
            'ioctl_handlers': self.ioctl_handlers,
            'summary': self._generate_summary()
        }
    
    def _analyze_function(self, func):
        """Analyze individual function for vulnerabilities"""
        if not BINJA_AVAILABLE:
            return
        
        func_name = func.name
        
        # Check for dangerous function calls
        for vuln_type, patterns in self.vuln_patterns.items():
            for pattern in patterns:
                if pattern in func_name.lower():
                    self.vulnerabilities.append({
                        'type': vuln_type,
                        'function': func_name,
                        'address': hex(func.start),
                        'description': f'Potentially dangerous function: {pattern}'
                    })
        
        # Analyze function calls within the function
        for block in func.basic_blocks:
            for instr in block:
                self._analyze_instruction(instr, func_name)
    
    def _analyze_instruction(self, instr, func_name):
        """Analyze individual instruction for vulnerabilities"""
        if not BINJA_AVAILABLE:
            return
        
        # Check for calls to dangerous functions
        if instr.operation == bn.LowLevelILOperation.LLIL_CALL:
            target = instr.dest
            if hasattr(target, 'constant') and target.constant:
                # Resolve function name
                target_func = self.bv.get_function_at(target.constant)
                if target_func:
                    self._check_dangerous_call(target_func.name, func_name, instr.address)
    
    def _check_dangerous_call(self, called_func: str, caller_func: str, address: int):
        """Check if function call is potentially dangerous"""
        for vuln_type, patterns in self.vuln_patterns.items():
            if called_func in patterns:
                self.vulnerabilities.append({
                    'type': vuln_type,
                    'function': caller_func,
                    'called_function': called_func,
                    'address': hex(address),
                    'description': f'Call to dangerous function: {called_func}'
                })
    
    def _find_ioctl_handlers(self):
        """Find IOCTL handler functions"""
        if not BINJA_AVAILABLE:
            return
        
        # Look for functions with IOCTL-like signatures
        for func in self.bv.functions:
            if self._is_ioctl_handler(func):
                self.ioctl_handlers.append({
                    'name': func.name,
                    'address': hex(func.start),
                    'size': len(func),
                    'commands': self._extract_ioctl_commands(func)
                })
    
    def _is_ioctl_handler(self, func) -> bool:
        """Check if function is likely an IOCTL handler"""
        if not BINJA_AVAILABLE:
            return False
        
        # Check function name
        name_indicators = ['ioctl', 'unlocked_ioctl', 'compat_ioctl']
        if any(indicator in func.name.lower() for indicator in name_indicators):
            return True
        
        # Check function signature (simplified)
        if len(func.parameter_vars) >= 3:
            return True
        
        return False
    
    def _extract_ioctl_commands(self, func) -> List[int]:
        """Extract IOCTL command values from function"""
        commands = []
        
        if not BINJA_AVAILABLE:
            return commands
        
        # Look for switch statements and comparisons with constants
        for block in func.basic_blocks:
            for instr in block:
                if instr.operation == bn.LowLevelILOperation.LLIL_CMP_E:
                    # Check if comparing with a constant that looks like IOCTL cmd
                    if hasattr(instr.right, 'constant'):
                        const = instr.right.constant
                        if 0x1000 <= const <= 0xffffffff:
                            commands.append(const)
        
        return commands
    
    def _generate_summary(self) -> Dict:
        """Generate analysis summary"""
        vuln_counts = {}
        for vuln in self.vulnerabilities:
            vuln_type = vuln['type']
            vuln_counts[vuln_type] = vuln_counts.get(vuln_type, 0) + 1
        
        return {
            'total_vulnerabilities': len(self.vulnerabilities),
            'vulnerability_types': vuln_counts,
            'ioctl_handlers_found': len(self.ioctl_handlers),
            'risk_score': self._calculate_risk_score()
        }
    
    def _calculate_risk_score(self) -> int:
        """Calculate overall risk score (0-10)"""
        score = 0
        
        # Weight different vulnerability types
        weights = {
            'buffer_overflow': 3,
            'use_after_free': 3,
            'format_string': 2,
            'double_free': 2,
            'integer_overflow': 2,
            'race_condition': 1
        }
        
        for vuln in self.vulnerabilities:
            vuln_type = vuln['type']
            score += weights.get(vuln_type, 1)
        
        return min(score, 10)
    
    def _standalone_analysis(self, binary_path: str) -> Dict:
        """Standalone analysis without Binary Ninja"""
        if not binary_path:
            return {'error': 'No binary path provided'}
        
        try:
            # Use objdump or similar for basic analysis
            import subprocess
            result = subprocess.run(['objdump', '-t', binary_path], 
                                  capture_output=True, text=True)
            
            symbols = result.stdout
            vulnerabilities = []
            
            # Simple pattern matching on symbols
            for vuln_type, patterns in self.vuln_patterns.items():
                for pattern in patterns:
                    if pattern in symbols:
                        vulnerabilities.append({
                            'type': vuln_type,
                            'pattern': pattern,
                            'description': f'Found symbol: {pattern}'
                        })
            
            return {
                'vulnerabilities': vulnerabilities,
                'ioctl_handlers': [],
                'summary': {
                    'total_vulnerabilities': len(vulnerabilities),
                    'analysis_method': 'standalone'
                }
            }
        
        except Exception as e:
            return {'error': str(e)}

# Binary Ninja plugin integration
if BINJA_AVAILABLE:
    def analyze_kernel_vulns(bv):
        """Binary Ninja plugin entry point"""
        analyzer = KernelVulnAnalyzer(bv)
        results = analyzer.analyze_binary()
        
        # Display results in Binary Ninja
        report = f"Kernel Vulnerability Analysis Results:\n\n"
        report += f"Total Vulnerabilities: {results['summary']['total_vulnerabilities']}\n"
        report += f"Risk Score: {results['summary']['risk_score']}/10\n\n"
        
        for vuln in results['vulnerabilities']:
            report += f"- {vuln['type']}: {vuln['description']} at {vuln['address']}\n"
        
        if results['ioctl_handlers']:
            report += f"\nIOCTL Handlers Found: {len(results['ioctl_handlers'])}\n"
            for handler in results['ioctl_handlers']:
                report += f"- {handler['name']} at {handler['address']}\n"
        
        bn.show_plain_text_report("Kernel Vulnerability Analysis", report)
    
    # Register plugin
    bn.PluginCommand.register(
        "Kernel Vulnerability Analysis",
        "Analyze binary for kernel-specific vulnerabilities",
        analyze_kernel_vulns
    )

def main():
    """Standalone execution"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Binary Ninja Kernel Analysis Plugin')
    parser.add_argument('binary', help='Binary file to analyze')
    parser.add_argument('--output', '-o', help='Output file for results')
    parser.add_argument('--format', choices=['json', 'text'], default='json',
                       help='Output format')
    
    args = parser.parse_args()
    
    analyzer = KernelVulnAnalyzer()
    results = analyzer.analyze_binary(args.binary)
    
    if args.format == 'json':
        output = json.dumps(results, indent=2)
    else:
        output = f"Kernel Vulnerability Analysis Results:\n\n"
        output += f"Total Vulnerabilities: {results['summary']['total_vulnerabilities']}\n"
        output += f"Risk Score: {results['summary'].get('risk_score', 0)}/10\n\n"
        
        for vuln in results['vulnerabilities']:
            output += f"- {vuln['type']}: {vuln['description']}\n"
        
        if results['ioctl_handlers']:
            output += f"\nIOCTL Handlers Found: {len(results['ioctl_handlers'])}\n"
            for handler in results['ioctl_handlers']:
                output += f"- {handler['name']} at {handler['address']}\n"
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
    else:
        print(output)

if __name__ == '__main__':
    main()