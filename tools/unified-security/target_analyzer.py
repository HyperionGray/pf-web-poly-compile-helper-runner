#!/usr/bin/env python3
"""
Unified Security Target Analyzer
Intelligently discovers and analyzes targets for comprehensive security assessment
"""

import json
import os
import sys
import argparse
import subprocess
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional

class TargetAnalyzer:
    """Smart target discovery and analysis for unified security assessment"""
    
    def __init__(self):
        self.targets = {
            'web': [],
            'binary': [],
            'kernel': [],
            'network': []
        }
        self.analysis_results = {}
    
    def analyze_target(self, target: str, mode: str = 'full') -> Dict[str, Any]:
        """Main analysis entry point"""
        print(f"🔍 Analyzing target: {target}")
        
        # Auto-detect target type
        target_types = self._detect_target_type(target)
        print(f"📋 Detected target types: {', '.join(target_types)}")
        
        results = {
            'target': target,
            'mode': mode,
            'detected_types': target_types,
            'analysis': {}
        }
        
        # Analyze each detected type
        for target_type in target_types:
            if mode == 'full' or mode == target_type:
                print(f"🔬 Analyzing as {target_type} target...")
                results['analysis'][target_type] = self._analyze_by_type(target, target_type)
        
        return results
    
    def _detect_target_type(self, target: str) -> List[str]:
        """Intelligently detect what type of target we're dealing with"""
        types = []
        
        # Check if it's a URL (web target)
        if target.startswith(('http://', 'https://')):
            types.append('web')
        
        # Check if it's a file path
        if os.path.exists(target):
            if os.path.isfile(target):
                # Check if it's an executable binary
                if self._is_executable_binary(target):
                    types.append('binary')
                # Check if it's a kernel module
                if target.endswith(('.ko', '.o')) or 'kernel' in target.lower():
                    types.append('kernel')
            elif os.path.isdir(target):
                # Directory - scan for interesting files
                types.extend(self._scan_directory(target))
        
        # Check if it's a network target (IP:port)
        if self._is_network_target(target):
            types.append('network')
        
        # If no specific type detected, try to infer from context
        if not types:
            types = self._infer_target_type(target)
        
        return list(set(types))  # Remove duplicates
    
    def _is_executable_binary(self, filepath: str) -> bool:
        """Check if file is an executable binary"""
        try:
            result = subprocess.run(['file', filepath], capture_output=True, text=True)
            output = result.stdout.lower()
            return any(keyword in output for keyword in [
                'executable', 'elf', 'pe32', 'mach-o', 'shared object'
            ])
        except:
            return False
    
    def _is_network_target(self, target: str) -> bool:
        """Check if target is a network address"""
        import re
        # Simple regex for IP:port or hostname:port
        pattern = r'^[\w\.-]+:\d+$'
        return bool(re.match(pattern, target))
    
    def _scan_directory(self, directory: str) -> List[str]:
        """Scan directory for interesting files"""
        types = []
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    filepath = os.path.join(root, file)
                    if self._is_executable_binary(filepath):
                        types.append('binary')
                    if file.endswith('.ko'):
                        types.append('kernel')
                # Don't recurse too deep
                if len(root.split(os.sep)) - len(directory.split(os.sep)) > 2:
                    break
        except:
            pass
        return types
    
    def _infer_target_type(self, target: str) -> List[str]:
        """Infer target type from context clues"""
        target_lower = target.lower()
        
        if any(keyword in target_lower for keyword in ['localhost', '127.0.0.1', 'http']):
            return ['web']
        elif any(keyword in target_lower for keyword in ['/bin/', '/usr/bin/', '.exe']):
            return ['binary']
        elif any(keyword in target_lower for keyword in ['kernel', '/dev/', '.ko']):
            return ['kernel']
        else:
            # Default to trying multiple approaches
            return ['web', 'binary']
    
    def _analyze_by_type(self, target: str, target_type: str) -> Dict[str, Any]:
        """Perform type-specific analysis"""
        if target_type == 'web':
            return self._analyze_web_target(target)
        elif target_type == 'binary':
            return self._analyze_binary_target(target)
        elif target_type == 'kernel':
            return self._analyze_kernel_target(target)
        elif target_type == 'network':
            return self._analyze_network_target(target)
        else:
            return {'error': f'Unknown target type: {target_type}'}
    
    def _analyze_web_target(self, target: str) -> Dict[str, Any]:
        """Analyze web application target"""
        analysis = {
            'type': 'web',
            'url': target,
            'endpoints': [],
            'technologies': [],
            'security_headers': {},
            'priority': 'medium'
        }
        
        try:
            # Basic web reconnaissance
            import urllib.request
            import urllib.error
            
            # Test basic connectivity
            try:
                response = urllib.request.urlopen(target, timeout=10)
                analysis['status_code'] = response.getcode()
                analysis['headers'] = dict(response.headers)
                
                # Check for common security headers
                security_headers = [
                    'X-Frame-Options', 'X-XSS-Protection', 'X-Content-Type-Options',
                    'Strict-Transport-Security', 'Content-Security-Policy'
                ]
                
                for header in security_headers:
                    analysis['security_headers'][header] = header in analysis['headers']
                
                # Increase priority if security headers are missing
                missing_headers = sum(1 for h in security_headers if not analysis['security_headers'][h])
                if missing_headers > 2:
                    analysis['priority'] = 'high'
                
            except urllib.error.URLError as e:
                analysis['error'] = str(e)
                analysis['priority'] = 'low'
            
            # Discover common endpoints
            common_endpoints = [
                '/admin', '/api', '/login', '/upload', '/search',
                '/robots.txt', '/.git', '/config', '/debug'
            ]
            
            for endpoint in common_endpoints:
                try:
                    test_url = target.rstrip('/') + endpoint
                    response = urllib.request.urlopen(test_url, timeout=5)
                    if response.getcode() == 200:
                        analysis['endpoints'].append({
                            'path': endpoint,
                            'status': response.getcode(),
                            'priority': 'high' if endpoint in ['/admin', '/api', '/upload'] else 'medium'
                        })
                except:
                    pass
            
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
    
    def _analyze_binary_target(self, target: str) -> Dict[str, Any]:
        """Analyze binary executable target"""
        analysis = {
            'type': 'binary',
            'path': target,
            'security_features': {},
            'functions': [],
            'complexity_score': 0,
            'priority': 'medium'
        }
        
        try:
            # Use existing checksec functionality
            checksec_result = subprocess.run([
                'python3', 'tools/security/checksec.py', '--json', target
            ], capture_output=True, text=True, cwd='/workspace')
            
            if checksec_result.returncode == 0:
                checksec_data = json.loads(checksec_result.stdout)
                analysis['security_features'] = checksec_data
                
                # Calculate priority based on security features
                vulnerable_features = 0
                for feature, enabled in checksec_data.items():
                    if feature in ['NX', 'PIE', 'Canary', 'RELRO'] and not enabled:
                        vulnerable_features += 1
                
                if vulnerable_features >= 3:
                    analysis['priority'] = 'high'
                elif vulnerable_features >= 1:
                    analysis['priority'] = 'medium'
                else:
                    analysis['priority'] = 'low'
            
            # Try to get function information
            try:
                nm_result = subprocess.run(['nm', target], capture_output=True, text=True)
                if nm_result.returncode == 0:
                    functions = []
                    for line in nm_result.stdout.split('\n'):
                        if ' T ' in line or ' t ' in line:  # Text (code) symbols
                            parts = line.split()
                            if len(parts) >= 3:
                                functions.append(parts[-1])
                    
                    analysis['functions'] = functions[:20]  # Limit to first 20
                    analysis['function_count'] = len(functions)
                    
                    # Higher function count might indicate more complexity
                    if len(functions) > 100:
                        analysis['complexity_score'] = min(10, len(functions) // 10)
            except:
                pass
            
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
    
    def _analyze_kernel_target(self, target: str) -> Dict[str, Any]:
        """Analyze kernel module or device target"""
        analysis = {
            'type': 'kernel',
            'path': target,
            'ioctls': [],
            'dangerous_functions': [],
            'priority': 'high'  # Kernel targets are always high priority
        }
        
        try:
            # Check if it's a device file
            if target.startswith('/dev/'):
                analysis['device_file'] = True
                # Try to detect IOCTL interfaces
                # This would require more sophisticated analysis
                analysis['note'] = 'Device file detected - IOCTL analysis recommended'
            else:
                # Binary kernel module analysis
                analysis['device_file'] = False
                
                # Look for dangerous kernel functions
                dangerous_patterns = [
                    'copy_from_user', 'copy_to_user', 'get_user', 'put_user',
                    'kmalloc', 'kfree', 'ioctl', 'unlocked_ioctl'
                ]
                
                try:
                    strings_result = subprocess.run(['strings', target], capture_output=True, text=True)
                    if strings_result.returncode == 0:
                        for pattern in dangerous_patterns:
                            if pattern in strings_result.stdout:
                                analysis['dangerous_functions'].append(pattern)
                except:
                    pass
        
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
    
    def _analyze_network_target(self, target: str) -> Dict[str, Any]:
        """Analyze network service target"""
        analysis = {
            'type': 'network',
            'target': target,
            'services': [],
            'priority': 'medium'
        }
        
        try:
            # Basic port scanning would go here
            # For now, just parse the target
            if ':' in target:
                host, port = target.split(':', 1)
                analysis['host'] = host
                analysis['port'] = int(port)
                
                # Common vulnerable ports
                high_risk_ports = [21, 22, 23, 25, 53, 80, 135, 139, 443, 445, 993, 995, 1433, 3389]
                if analysis['port'] in high_risk_ports:
                    analysis['priority'] = 'high'
        
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis

def main():
    parser = argparse.ArgumentParser(description='Unified Security Target Analyzer')
    parser.add_argument('target', help='Target to analyze (URL, file path, IP:port, etc.)')
    parser.add_argument('--mode', choices=['full', 'web', 'binary', 'kernel', 'network'], 
                       default='full', help='Analysis mode')
    parser.add_argument('--output', help='Output file for results (JSON format)')
    
    args = parser.parse_args()
    
    analyzer = TargetAnalyzer()
    results = analyzer.analyze_target(args.target, args.mode)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"📁 Results saved to: {args.output}")
    else:
        print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()