#!/usr/bin/env python3
"""
Enhanced Target Detection System
Intelligently detects target types and recommends appropriate workflows
"""

import os
import sys
import json
import argparse
import urllib.parse
from pathlib import Path

class EnhancedTargetDetector:
    def __init__(self):
        self.target_info = {
            'type': 'unknown',
            'subtype': None,
            'confidence': 0.0,
            'properties': {},
            'recommended_workflows': [],
            'tools': []
        }
    
    def detect_target_type(self, target):
        """Main detection logic"""
        # URL detection
        if self._is_url(target):
            return self._analyze_web_target(target)
        
        # File/device detection
        if os.path.exists(target):
            if os.path.isfile(target):
                return self._analyze_file_target(target)
            elif os.path.isdir(target):
                return self._analyze_directory_target(target)
            elif self._is_device(target):
                return self._analyze_device_target(target)
        
        # Network target detection
        if self._is_network_target(target):
            return self._analyze_network_target(target)
        
        return self.target_info
    
    def _is_url(self, target):
        """Check if target is a URL"""
        parsed = urllib.parse.urlparse(target)
        return parsed.scheme in ['http', 'https', 'ftp', 'ftps']
    
    def _is_device(self, target):
        """Check if target is a device"""
        return target.startswith('/dev/') or target in ['/proc/cpuinfo', '/sys/']
    
    def _is_network_target(self, target):
        """Check if target is a network address"""
        # Simple IP address or hostname detection
        import re
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}(:\d+)?$'
        hostname_pattern = r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(:\d+)?$'
        return re.match(ip_pattern, target) or re.match(hostname_pattern, target)
    
    def _analyze_web_target(self, target):
        """Analyze web target"""
        self.target_info.update({
            'type': 'web',
            'confidence': 0.9,
            'properties': {
                'url': target,
                'scheme': urllib.parse.urlparse(target).scheme,
                'hostname': urllib.parse.urlparse(target).hostname,
                'port': urllib.parse.urlparse(target).port
            },
            'recommended_workflows': [
                'enhanced-web-test',
                'scan',
                'enhanced-recon'
            ],
            'tools': [
                'nikto',
                'dirb',
                'sqlmap',
                'burpsuite',
                'nmap'
            ]
        })
        return self.target_info
    
    def _analyze_file_target(self, target):
        """Analyze file target"""
        file_path = Path(target)
        file_size = file_path.stat().st_size
        
        # Detect file type
        try:
            import subprocess
            file_result = subprocess.run(['file', target], capture_output=True, text=True)
            file_type = file_result.stdout.strip()
        except:
            file_type = "unknown"
        
        # Binary detection
        if any(keyword in file_type.lower() for keyword in ['elf', 'executable', 'pe32', 'mach-o']):
            self.target_info.update({
                'type': 'binary',
                'subtype': self._detect_binary_subtype(file_type),
                'confidence': 0.95,
                'properties': {
                    'path': target,
                    'size': file_size,
                    'file_type': file_type,
                    'architecture': self._detect_architecture(file_type)
                },
                'recommended_workflows': [
                    'enhanced-binary-analysis',
                    'pwn',
                    'enhanced-reverse'
                ],
                'tools': [
                    'checksec',
                    'gdb',
                    'radare2',
                    'ghidra',
                    'objdump',
                    'strings'
                ]
            })
        # Firmware detection
        elif any(keyword in file_type.lower() for keyword in ['firmware', 'rom', 'flash']):
            self.target_info.update({
                'type': 'firmware',
                'confidence': 0.8,
                'properties': {
                    'path': target,
                    'size': file_size,
                    'file_type': file_type
                },
                'recommended_workflows': [
                    'enhanced-binary-analysis',
                    'enhanced-reverse'
                ],
                'tools': [
                    'binwalk',
                    'firmware-mod-kit',
                    'radare2'
                ]
            })
        # Source code detection
        elif file_path.suffix in ['.c', '.cpp', '.py', '.js', '.php', '.java']:
            self.target_info.update({
                'type': 'source',
                'subtype': file_path.suffix[1:],
                'confidence': 0.9,
                'properties': {
                    'path': target,
                    'language': file_path.suffix[1:],
                    'size': file_size
                },
                'recommended_workflows': [
                    'enhanced-analyze',
                    'scan'
                ],
                'tools': [
                    'bandit',
                    'semgrep',
                    'cppcheck',
                    'eslint'
                ]
            })
        else:
            # Generic file
            self.target_info.update({
                'type': 'file',
                'confidence': 0.5,
                'properties': {
                    'path': target,
                    'size': file_size,
                    'file_type': file_type
                },
                'recommended_workflows': [
                    'enhanced-analyze'
                ],
                'tools': [
                    'file',
                    'strings',
                    'hexdump'
                ]
            })
        
        return self.target_info
    
    def _analyze_directory_target(self, target):
        """Analyze directory target"""
        dir_path = Path(target)
        
        # Check for common project types
        if (dir_path / 'Makefile').exists():
            project_type = 'c/c++'
        elif (dir_path / 'package.json').exists():
            project_type = 'nodejs'
        elif (dir_path / 'requirements.txt').exists() or (dir_path / 'setup.py').exists():
            project_type = 'python'
        elif (dir_path / 'Cargo.toml').exists():
            project_type = 'rust'
        elif (dir_path / 'pom.xml').exists():
            project_type = 'java'
        else:
            project_type = 'unknown'
        
        self.target_info.update({
            'type': 'project',
            'subtype': project_type,
            'confidence': 0.8,
            'properties': {
                'path': target,
                'project_type': project_type,
                'files_count': len(list(dir_path.rglob('*')))
            },
            'recommended_workflows': [
                'enhanced-analyze',
                'scan'
            ],
            'tools': [
                'find',
                'grep',
                'semgrep',
                'bandit'
            ]
        })
        
        return self.target_info
    
    def _analyze_device_target(self, target):
        """Analyze device target"""
        self.target_info.update({
            'type': 'device',
            'confidence': 0.7,
            'properties': {
                'path': target,
                'device_type': 'hardware'
            },
            'recommended_workflows': [
                'enhanced-analyze',
                'scan'
            ],
            'tools': [
                'lsusb',
                'lspci',
                'dmesg'
            ]
        })
        
        return self.target_info
    
    def _analyze_network_target(self, target):
        """Analyze network target"""
        # Parse host and port
        if ':' in target:
            host, port = target.rsplit(':', 1)
            try:
                port = int(port)
            except ValueError:
                port = None
        else:
            host = target
            port = None
        
        self.target_info.update({
            'type': 'network',
            'confidence': 0.8,
            'properties': {
                'host': host,
                'port': port,
                'target': target
            },
            'recommended_workflows': [
                'enhanced-network-test',
                'scan',
                'enhanced-recon'
            ],
            'tools': [
                'nmap',
                'masscan',
                'netcat',
                'telnet'
            ]
        })
        
        return self.target_info
    
    def _detect_binary_subtype(self, file_type):
        """Detect binary subtype"""
        if 'elf' in file_type.lower():
            return 'elf'
        elif 'pe32' in file_type.lower():
            return 'pe'
        elif 'mach-o' in file_type.lower():
            return 'macho'
        else:
            return 'unknown'
    
    def _detect_architecture(self, file_type):
        """Detect architecture from file type"""
        if 'x86-64' in file_type or 'x86_64' in file_type:
            return 'x86_64'
        elif 'i386' in file_type or 'x86' in file_type:
            return 'x86'
        elif 'arm' in file_type.lower():
            return 'arm'
        elif 'aarch64' in file_type.lower():
            return 'aarch64'
        else:
            return 'unknown'
    
    def suggest_workflows(self, target):
        """Suggest appropriate workflows for target"""
        target_info = self.detect_target_type(target)
        
        print(f"🎯 Enhanced Target Analysis for: {target}")
        print(f"Type: {target_info['type']}")
        if target_info['subtype']:
            print(f"Subtype: {target_info['subtype']}")
        print(f"Confidence: {target_info['confidence']:.1%}")
        
        if target_info['properties']:
            print("\nProperties:")
            for key, value in target_info['properties'].items():
                print(f"  {key}: {value}")
        
        if target_info['recommended_workflows']:
            print("\nRecommended Enhanced Workflows:")
            for workflow in target_info['recommended_workflows']:
                print(f"  pf {workflow} target={target}")
        
        if target_info['tools']:
            print("\nRecommended Tools:")
            for tool in target_info['tools']:
                print(f"  {tool}")
        
        return target_info

def main():
    parser = argparse.ArgumentParser(description='Enhanced Target Detection System')
    parser.add_argument('target', help='Target to analyze')
    parser.add_argument('--format', choices=['json', 'text'], default='text', help='Output format')
    parser.add_argument('--suggest-workflows', action='store_true', help='Suggest workflows')
    
    args = parser.parse_args()
    
    detector = EnhancedTargetDetector()
    
    if args.suggest_workflows:
        target_info = detector.suggest_workflows(args.target)
    else:
        target_info = detector.detect_target_type(args.target)
    
    if args.format == 'json':
        print(json.dumps(target_info, indent=2))
    elif args.format == 'text' and not args.suggest_workflows:
        print(f"Target: {args.target}")
        print(f"Type: {target_info['type']}")
        print(f"Confidence: {target_info['confidence']:.1%}")

if __name__ == '__main__':
    main()