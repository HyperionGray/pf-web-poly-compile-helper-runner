#!/usr/bin/env python3
"""
Smart Binary Analyzer - Intelligent tool orchestration for binary analysis
Automatically detects target type and runs appropriate analysis tools
Part of the pf smart workflows system
"""

import os
import sys
import json
import argparse
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class SmartAnalyzer:
    """Intelligent binary analyzer that orchestrates multiple tools"""
    
    def __init__(self):
        self.results = {}
        self.target_info = {}
        self.tools_available = self._check_available_tools()
        
    def _check_available_tools(self) -> Dict[str, bool]:
        """Check which analysis tools are available"""
        tools = {
            'file': self._command_exists('file'),
            'checksec': self._command_exists('checksec') or os.path.exists('tools/security/checksec.py'),
            'strings': self._command_exists('strings'),
            'objdump': self._command_exists('objdump'),
            'readelf': self._command_exists('readelf'),
            'nm': self._command_exists('nm'),
            'ldd': self._command_exists('ldd'),
            'strace': self._command_exists('strace'),
            'ltrace': self._command_exists('ltrace'),
            'gdb': self._command_exists('gdb'),
            'radare2': self._command_exists('r2'),
            'ghidra': os.path.exists('/opt/ghidra') or os.path.exists('~/ghidra'),
            'retdec': self._command_exists('retdec-decompiler'),
        }
        return tools
    
    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH"""
        try:
            subprocess.run(['which', command], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def detect_target_type(self, target: str) -> Dict[str, any]:
        """Detect target type and characteristics"""
        if not os.path.exists(target):
            return {'error': f'Target {target} does not exist'}
        
        info = {
            'path': target,
            'size': os.path.getsize(target),
            'is_executable': os.access(target, os.X_OK),
            'file_type': None,
            'architecture': None,
            'format': None,
            'stripped': None,
            'dynamic': None,
            'security_features': {},
        }
        
        # Use file command for basic detection
        if self.tools_available['file']:
            try:
                result = subprocess.run(['file', target], capture_output=True, text=True, check=True)
                file_output = result.stdout.strip()
                info['file_type'] = file_output
                
                # Parse file output for key information
                if 'ELF' in file_output:
                    info['format'] = 'ELF'
                    if 'x86-64' in file_output or 'x86_64' in file_output:
                        info['architecture'] = 'x86_64'
                    elif 'i386' in file_output or 'x86' in file_output:
                        info['architecture'] = 'x86'
                    elif 'ARM' in file_output:
                        info['architecture'] = 'ARM'
                    
                    if 'stripped' in file_output:
                        info['stripped'] = True
                    elif 'not stripped' in file_output:
                        info['stripped'] = False
                        
                    if 'dynamically linked' in file_output:
                        info['dynamic'] = True
                    elif 'statically linked' in file_output:
                        info['dynamic'] = False
                        
                elif 'PE32' in file_output:
                    info['format'] = 'PE'
                elif 'Mach-O' in file_output:
                    info['format'] = 'Mach-O'
                    
            except subprocess.CalledProcessError:
                pass
        
        self.target_info = info
        return info
    
    def run_basic_analysis(self, target: str) -> Dict[str, any]:
        """Run basic analysis tools"""
        results = {}
        
        # File information
        results['file_info'] = self.detect_target_type(target)
        
        # Security features analysis
        if self.tools_available['checksec'] or os.path.exists('tools/security/checksec.py'):
            results['security_features'] = self._run_checksec(target)
        
        # Strings analysis
        if self.tools_available['strings']:
            results['strings'] = self._run_strings_analysis(target)
        
        # Symbol analysis
        if self.tools_available['nm'] or self.tools_available['objdump']:
            results['symbols'] = self._run_symbol_analysis(target)
        
        # Dynamic analysis info
        if self.tools_available['ldd'] and self.target_info.get('dynamic'):
            results['dependencies'] = self._run_ldd(target)
        
        return results
    
    def run_advanced_analysis(self, target: str) -> Dict[str, any]:
        """Run advanced analysis tools"""
        results = {}
        
        # Disassembly analysis
        if self.tools_available['objdump']:
            results['disassembly'] = self._run_disassembly_analysis(target)
        
        # Radare2 analysis
        if self.tools_available['radare2']:
            results['radare2'] = self._run_radare2_analysis(target)
        
        # Vulnerability detection
        results['vulnerabilities'] = self._run_vulnerability_detection(target)
        
        # Function complexity analysis
        results['complexity'] = self._run_complexity_analysis(target)
        
        return results
    
    def _run_checksec(self, target: str) -> Dict[str, any]:
        """Run checksec analysis"""
        try:
            if os.path.exists('tools/security/checksec.py'):
                result = subprocess.run(['python3', 'tools/security/checksec.py', '--json', target], 
                                      capture_output=True, text=True, check=True)
                return json.loads(result.stdout)
            elif self.tools_available['checksec']:
                result = subprocess.run(['checksec', '--format=json', '--file', target], 
                                      capture_output=True, text=True, check=True)
                return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            pass
        return {}
    
    def _run_strings_analysis(self, target: str) -> Dict[str, any]:
        """Run strings analysis"""
        try:
            result = subprocess.run(['strings', target], capture_output=True, text=True, check=True)
            strings = result.stdout.strip().split('\n')
            
            # Analyze strings for interesting patterns
            interesting = {
                'urls': [s for s in strings if 'http' in s.lower()],
                'files': [s for s in strings if '/' in s and len(s) > 3],
                'functions': [s for s in strings if any(func in s for func in ['printf', 'scanf', 'strcpy', 'system'])],
                'total_count': len(strings),
            }
            return interesting
        except subprocess.CalledProcessError:
            return {}
    
    def _run_symbol_analysis(self, target: str) -> Dict[str, any]:
        """Run symbol analysis"""
        symbols = {}
        
        # Try nm first
        if self.tools_available['nm']:
            try:
                result = subprocess.run(['nm', target], capture_output=True, text=True, check=True)
                symbols['nm_output'] = result.stdout
                # Count different symbol types
                lines = result.stdout.strip().split('\n')
                symbol_types = {}
                for line in lines:
                    if len(line.split()) >= 2:
                        sym_type = line.split()[1]
                        symbol_types[sym_type] = symbol_types.get(sym_type, 0) + 1
                symbols['symbol_types'] = symbol_types
            except subprocess.CalledProcessError:
                pass
        
        # Try objdump as fallback
        if not symbols and self.tools_available['objdump']:
            try:
                result = subprocess.run(['objdump', '-t', target], capture_output=True, text=True, check=True)
                symbols['objdump_symbols'] = result.stdout
            except subprocess.CalledProcessError:
                pass
        
        return symbols
    
    def _run_ldd(self, target: str) -> Dict[str, any]:
        """Run ldd to analyze dependencies"""
        try:
            result = subprocess.run(['ldd', target], capture_output=True, text=True, check=True)
            deps = []
            for line in result.stdout.strip().split('\n'):
                if '=>' in line:
                    lib = line.split('=>')[0].strip()
                    path = line.split('=>')[1].split('(')[0].strip()
                    deps.append({'library': lib, 'path': path})
            return {'dependencies': deps, 'count': len(deps)}
        except subprocess.CalledProcessError:
            return {}
    
    def _run_disassembly_analysis(self, target: str) -> Dict[str, any]:
        """Run disassembly analysis"""
        try:
            # Get function list
            result = subprocess.run(['objdump', '-t', target], capture_output=True, text=True, check=True)
            functions = []
            for line in result.stdout.split('\n'):
                if 'F .text' in line:
                    parts = line.split()
                    if len(parts) >= 6:
                        functions.append(parts[-1])
            
            return {
                'function_count': len(functions),
                'functions': functions[:20],  # First 20 functions
            }
        except subprocess.CalledProcessError:
            return {}
    
    def _run_radare2_analysis(self, target: str) -> Dict[str, any]:
        """Run radare2 analysis if available"""
        if not self.tools_available['radare2']:
            return {}
        
        try:
            # Basic r2 analysis
            r2_script = "aaa; aflc; q"
            result = subprocess.run(['r2', '-q', '-c', r2_script, target], 
                                  capture_output=True, text=True, check=True)
            return {'function_analysis': result.stdout.strip()}
        except subprocess.CalledProcessError:
            return {}
    
    def _run_vulnerability_detection(self, target: str) -> Dict[str, any]:
        """Run vulnerability detection"""
        vulns = []
        
        # Check for dangerous functions in strings
        if 'strings' in self.results:
            dangerous_funcs = ['strcpy', 'strcat', 'sprintf', 'gets', 'system']
            for func in dangerous_funcs:
                if any(func in s for s in self.results.get('strings', {}).get('functions', [])):
                    vulns.append({
                        'type': 'dangerous_function',
                        'function': func,
                        'severity': 'medium',
                        'description': f'Use of potentially dangerous function: {func}'
                    })
        
        # Check security features
        if 'security_features' in self.results:
            sec_features = self.results['security_features']
            if not sec_features.get('canary', True):
                vulns.append({
                    'type': 'missing_protection',
                    'protection': 'stack_canary',
                    'severity': 'high',
                    'description': 'Stack canary protection is disabled'
                })
            if not sec_features.get('nx', True):
                vulns.append({
                    'type': 'missing_protection',
                    'protection': 'nx_bit',
                    'severity': 'high',
                    'description': 'NX bit protection is disabled'
                })
        
        return {'vulnerabilities': vulns, 'count': len(vulns)}
    
    def _run_complexity_analysis(self, target: str) -> Dict[str, any]:
        """Run function complexity analysis"""
        # This is a simplified version - in practice, you'd use more sophisticated tools
        complexity = {
            'analysis_method': 'basic_heuristics',
            'notes': 'Full complexity analysis requires disassembly parsing'
        }
        
        # If we have function count from disassembly
        if 'disassembly' in self.results:
            func_count = self.results['disassembly'].get('function_count', 0)
            if func_count > 100:
                complexity['complexity_level'] = 'high'
            elif func_count > 20:
                complexity['complexity_level'] = 'medium'
            else:
                complexity['complexity_level'] = 'low'
            complexity['function_count'] = func_count
        
        return complexity
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on analysis results"""
        recommendations = []
        
        # Security recommendations
        if 'vulnerabilities' in self.results:
            vuln_count = self.results['vulnerabilities'].get('count', 0)
            if vuln_count > 0:
                recommendations.append(f"🚨 Found {vuln_count} potential vulnerabilities - consider running 'pf smart-exploit' for exploitation analysis")
        
        # Tool recommendations based on target type
        if self.target_info.get('format') == 'ELF':
            if not self.target_info.get('stripped', True):
                recommendations.append("💡 Binary has debug symbols - 'pf unified-debug' will be very effective")
            else:
                recommendations.append("🔍 Binary is stripped - consider 'pf smart-vulnerability-research' for advanced analysis")
        
        # Fuzzing recommendations
        if self.target_info.get('is_executable'):
            recommendations.append("🎯 Executable target detected - 'pf smart-fuzz' can test for input validation issues")
        
        # Complexity recommendations
        if 'complexity' in self.results:
            complexity_level = self.results['complexity'].get('complexity_level')
            if complexity_level == 'high':
                recommendations.append("🧠 High complexity binary - 'pf smart-vulnerability-research' recommended for thorough analysis")
        
        return recommendations
    
    def run_analysis(self, target: str, deep: bool = False, output_format: str = 'json') -> Dict[str, any]:
        """Run complete smart analysis"""
        print(f"🧠 Smart Analysis starting for: {target}")
        
        # Basic analysis
        print("📊 Running basic analysis...")
        self.results.update(self.run_basic_analysis(target))
        
        # Advanced analysis if requested
        if deep:
            print("🔬 Running deep analysis...")
            self.results.update(self.run_advanced_analysis(target))
        
        # Generate recommendations
        print("💡 Generating recommendations...")
        self.results['recommendations'] = self.generate_recommendations()
        
        # Add metadata
        self.results['metadata'] = {
            'analyzer_version': '1.0.0',
            'target': target,
            'analysis_type': 'deep' if deep else 'basic',
            'tools_used': [tool for tool, available in self.tools_available.items() if available],
        }
        
        print("✅ Smart analysis complete!")
        return self.results
    
    def format_output(self, results: Dict[str, any], format_type: str = 'json') -> str:
        """Format analysis results"""
        if format_type == 'json':
            return json.dumps(results, indent=2)
        elif format_type == 'text':
            return self._format_text_output(results)
        else:
            return json.dumps(results, indent=2)
    
    def _format_text_output(self, results: Dict[str, any]) -> str:
        """Format results as human-readable text"""
        output = []
        output.append("╔════════════════════════════════════════════════════════════╗")
        output.append("║                SMART ANALYSIS RESULTS                     ║")
        output.append("╚════════════════════════════════════════════════════════════╝")
        output.append("")
        
        # File info
        if 'file_info' in results:
            info = results['file_info']
            output.append("📁 FILE INFORMATION:")
            output.append(f"   Path: {info.get('path', 'N/A')}")
            output.append(f"   Size: {info.get('size', 0)} bytes")
            output.append(f"   Format: {info.get('format', 'Unknown')}")
            output.append(f"   Architecture: {info.get('architecture', 'Unknown')}")
            output.append(f"   Stripped: {info.get('stripped', 'Unknown')}")
            output.append("")
        
        # Security features
        if 'security_features' in results:
            output.append("🛡️ SECURITY FEATURES:")
            sec = results['security_features']
            for feature, enabled in sec.items():
                status = "✅" if enabled else "❌"
                output.append(f"   {feature}: {status}")
            output.append("")
        
        # Vulnerabilities
        if 'vulnerabilities' in results:
            vulns = results['vulnerabilities']
            count = vulns.get('count', 0)
            output.append(f"🚨 VULNERABILITIES FOUND: {count}")
            for vuln in vulns.get('vulnerabilities', [])[:5]:  # Show first 5
                output.append(f"   - {vuln.get('type', 'Unknown')}: {vuln.get('description', 'No description')}")
            if count > 5:
                output.append(f"   ... and {count - 5} more")
            output.append("")
        
        # Recommendations
        if 'recommendations' in results:
            output.append("💡 RECOMMENDATIONS:")
            for rec in results['recommendations']:
                output.append(f"   {rec}")
            output.append("")
        
        # Metadata
        if 'metadata' in results:
            meta = results['metadata']
            output.append("ℹ️ ANALYSIS METADATA:")
            output.append(f"   Analysis Type: {meta.get('analysis_type', 'Unknown')}")
            output.append(f"   Tools Used: {', '.join(meta.get('tools_used', []))}")
            output.append("")
        
        return '\n'.join(output)


def main():
    parser = argparse.ArgumentParser(description='Smart Binary Analyzer')
    parser.add_argument('target', help='Target binary to analyze')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--deep-analysis', action='store_true', help='Run deep analysis')
    parser.add_argument('--format', choices=['json', 'text'], default='text', help='Output format')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.target):
        print(f"Error: Target {args.target} does not exist", file=sys.stderr)
        sys.exit(1)
    
    analyzer = SmartAnalyzer()
    results = analyzer.run_analysis(args.target, deep=args.deep_analysis, output_format=args.format)
    
    formatted_output = analyzer.format_output(results, args.format)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(formatted_output)
        print(f"Results saved to: {args.output}")
    else:
        print(formatted_output)


if __name__ == '__main__':
    main()