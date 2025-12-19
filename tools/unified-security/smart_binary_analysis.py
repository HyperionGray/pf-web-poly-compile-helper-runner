#!/usr/bin/env python3
"""
Smart Binary Analysis Engine
Integrates multiple binary analysis tools for comprehensive security assessment
"""

import json
import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

class SmartBinaryAnalyzer:
    """Intelligent binary analysis combining multiple tools"""
    
    def __init__(self):
        self.workspace = Path('/workspace')
        self.results = {}
    
    def analyze_targets(self, targets_file: str) -> Dict[str, Any]:
        """Analyze binary targets from target analyzer results"""
        print("🔬 Starting smart binary analysis...")
        
        # Load targets
        with open(targets_file, 'r') as f:
            targets_data = json.load(f)
        
        results = {
            'analysis_type': 'smart_binary',
            'targets_analyzed': 0,
            'binaries': {},
            'summary': {
                'high_risk_binaries': [],
                'vulnerable_functions': [],
                'exploit_candidates': []
            }
        }
        
        # Find binary targets
        binary_targets = []
        if 'analysis' in targets_data and 'binary' in targets_data['analysis']:
            binary_targets.append(targets_data['analysis']['binary'])
        
        for target in binary_targets:
            if 'path' in target:
                binary_path = target['path']
                print(f"📋 Analyzing binary: {binary_path}")
                
                binary_analysis = self._analyze_single_binary(binary_path)
                results['binaries'][binary_path] = binary_analysis
                results['targets_analyzed'] += 1
                
                # Update summary
                if binary_analysis.get('risk_score', 0) >= 7:
                    results['summary']['high_risk_binaries'].append(binary_path)
        
        return results
    
    def _analyze_single_binary(self, binary_path: str) -> Dict[str, Any]:
        """Comprehensive analysis of a single binary"""
        analysis = {
            'path': binary_path,
            'security_features': {},
            'functions': {},
            'complexity': {},
            'vulnerabilities': [],
            'risk_score': 0
        }
        
        # 1. Security features analysis (checksec)
        print("  🛡️  Analyzing security features...")
        analysis['security_features'] = self._run_checksec(binary_path)
        
        # 2. Function analysis
        print("  🔍 Analyzing functions...")
        analysis['functions'] = self._analyze_functions(binary_path)
        
        # 3. Complexity analysis
        print("  📊 Analyzing complexity...")
        analysis['complexity'] = self._analyze_complexity(binary_path)
        
        # 4. Vulnerability scanning
        print("  🎯 Scanning for vulnerabilities...")
        analysis['vulnerabilities'] = self._scan_vulnerabilities(binary_path)
        
        # 5. Calculate risk score
        analysis['risk_score'] = self._calculate_risk_score(analysis)
        
        return analysis
    
    def _run_checksec(self, binary_path: str) -> Dict[str, Any]:
        """Run checksec analysis"""
        try:
            result = subprocess.run([
                'python3', str(self.workspace / 'tools/security/checksec.py'),
                '--json', binary_path
            ], capture_output=True, text=True, cwd=str(self.workspace))
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {'error': result.stderr}
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_functions(self, binary_path: str) -> Dict[str, Any]:
        """Analyze functions in the binary"""
        functions = {
            'total_count': 0,
            'dangerous_functions': [],
            'parse_functions': [],
            'entry_points': []
        }
        
        try:
            # Get function symbols
            nm_result = subprocess.run(['nm', binary_path], capture_output=True, text=True)
            if nm_result.returncode == 0:
                func_names = []
                for line in nm_result.stdout.split('\n'):
                    if ' T ' in line or ' t ' in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            func_names.append(parts[-1])
                
                functions['total_count'] = len(func_names)
                
                # Identify dangerous functions
                dangerous_patterns = [
                    'strcpy', 'strcat', 'sprintf', 'gets', 'scanf',
                    'system', 'exec', 'popen', 'malloc', 'free'
                ]
                
                for func in func_names:
                    for pattern in dangerous_patterns:
                        if pattern in func.lower():
                            functions['dangerous_functions'].append(func)
                
                # Identify potential parse functions
                parse_patterns = ['parse', 'read', 'input', 'recv', 'process']
                for func in func_names:
                    for pattern in parse_patterns:
                        if pattern in func.lower():
                            functions['parse_functions'].append(func)
        
        except Exception as e:
            functions['error'] = str(e)
        
        return functions
    
    def _analyze_complexity(self, binary_path: str) -> Dict[str, Any]:
        """Analyze binary complexity"""
        complexity = {
            'file_size': 0,
            'sections': [],
            'complexity_score': 0
        }
        
        try:
            # Get file size
            complexity['file_size'] = os.path.getsize(binary_path)
            
            # Get sections info
            objdump_result = subprocess.run([
                'objdump', '-h', binary_path
            ], capture_output=True, text=True)
            
            if objdump_result.returncode == 0:
                sections = []
                for line in objdump_result.stdout.split('\n'):
                    if '.text' in line or '.data' in line or '.bss' in line:
                        sections.append(line.strip())
                complexity['sections'] = sections
            
            # Simple complexity score based on size and function count
            size_score = min(5, complexity['file_size'] // 100000)  # 1 point per 100KB
            complexity['complexity_score'] = size_score
        
        except Exception as e:
            complexity['error'] = str(e)
        
        return complexity
    
    def _scan_vulnerabilities(self, binary_path: str) -> List[Dict[str, Any]]:
        """Scan for potential vulnerabilities"""
        vulnerabilities = []
        
        try:
            # Check for common vulnerability patterns in strings
            strings_result = subprocess.run(['strings', binary_path], capture_output=True, text=True)
            if strings_result.returncode == 0:
                strings_output = strings_result.stdout
                
                # Look for format string vulnerabilities
                if '%s' in strings_output or '%x' in strings_output:
                    vulnerabilities.append({
                        'type': 'format_string',
                        'severity': 'medium',
                        'description': 'Potential format string vulnerability detected'
                    })
                
                # Look for buffer overflow indicators
                if any(func in strings_output for func in ['strcpy', 'strcat', 'sprintf']):
                    vulnerabilities.append({
                        'type': 'buffer_overflow',
                        'severity': 'high',
                        'description': 'Dangerous string functions detected'
                    })
                
                # Look for command injection indicators
                if any(cmd in strings_output for cmd in ['system', 'exec', 'popen']):
                    vulnerabilities.append({
                        'type': 'command_injection',
                        'severity': 'high',
                        'description': 'Command execution functions detected'
                    })
        
        except Exception as e:
            vulnerabilities.append({
                'type': 'analysis_error',
                'severity': 'info',
                'description': f'Error during vulnerability scan: {str(e)}'
            })
        
        return vulnerabilities
    
    def _calculate_risk_score(self, analysis: Dict[str, Any]) -> int:
        """Calculate overall risk score (0-10)"""
        score = 0
        
        # Security features (0-4 points)
        security_features = analysis.get('security_features', {})
        missing_protections = 0
        for feature in ['NX', 'PIE', 'Canary', 'RELRO']:
            if not security_features.get(feature, False):
                missing_protections += 1
        score += missing_protections
        
        # Vulnerabilities (0-4 points)
        vulnerabilities = analysis.get('vulnerabilities', [])
        high_severity_vulns = sum(1 for v in vulnerabilities if v.get('severity') == 'high')
        score += min(4, high_severity_vulns)
        
        # Complexity (0-2 points)
        complexity_score = analysis.get('complexity', {}).get('complexity_score', 0)
        score += min(2, complexity_score)
        
        return min(10, score)

def main():
    parser = argparse.ArgumentParser(description='Smart Binary Analysis Engine')
    parser.add_argument('--targets', required=True, help='Targets file from target analyzer')
    parser.add_argument('--output', required=True, help='Output file for analysis results')
    
    args = parser.parse_args()
    
    analyzer = SmartBinaryAnalyzer()
    results = analyzer.analyze_targets(args.targets)
    
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📁 Binary analysis complete. Results saved to: {args.output}")
    print(f"📊 Analyzed {results['targets_analyzed']} binaries")
    print(f"🔥 High-risk binaries: {len(results['summary']['high_risk_binaries'])}")

if __name__ == '__main__':
    main()