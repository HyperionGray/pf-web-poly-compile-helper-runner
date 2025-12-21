#!/usr/bin/env python3
"""
Smart Target Detection System
Intelligently detects target types and recommends appropriate workflows
"""

import os
import sys
import json
import argparse
import subprocess
import magic
import urllib.parse
from pathlib import Path

class TargetDetector:
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
        """Check if target is a device file"""
        return target.startswith('/dev/') or target.startswith('/proc/')
    
    def _is_network_target(self, target):
        """Check if target is a network address"""
        import re
        # Simple IP address or hostname pattern
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}(:\d+)?$'
        hostname_pattern = r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(:\d+)?$'
        return re.match(ip_pattern, target) or re.match(hostname_pattern, target)
    
    def _analyze_web_target(self, target):
        """Analyze web application target"""
        self.target_info.update({
            'type': 'web',
            'subtype': 'application',
            'confidence': 0.9,
            'properties': {
                'url': target,
                'parsed_url': urllib.parse.urlparse(target)._asdict()
            },
            'recommended_workflows': [
                'smart-web-security',
                'security-scan',
                'security-fuzz'
            ],
            'tools': [
                'web_scanner',
                'web_fuzzer',
                'burp_suite_like'
            ]
        })
        
        # Try to get more info about the web app
        try:
            import requests
            response = requests.head(target, timeout=5)
            self.target_info['properties']['status_code'] = response.status_code
            self.target_info['properties']['headers'] = dict(response.headers)
            
            # Detect web framework/technology
            server = response.headers.get('Server', '')
            if 'nginx' in server.lower():
                self.target_info['properties']['web_server'] = 'nginx'
            elif 'apache' in server.lower():
                self.target_info['properties']['web_server'] = 'apache'
            
        except Exception as e:
            self.target_info['properties']['connection_error'] = str(e)
        
        return self.target_info
    
    def _analyze_file_target(self, target):
        """Analyze file target"""
        try:
            # Get file info
            file_info = magic.from_file(target)
            file_type = magic.from_file(target, mime=True)
            
            self.target_info.update({
                'properties': {
                    'path': target,
                    'size': os.path.getsize(target),
                    'file_info': file_info,
                    'mime_type': file_type
                }
            })
            
            # Binary executable detection
            if 'ELF' in file_info:
                return self._analyze_elf_binary(target, file_info)
            elif 'PE32' in file_info or 'MS-DOS' in file_info:
                return self._analyze_pe_binary(target, file_info)
            elif 'Mach-O' in file_info:
                return self._analyze_macho_binary(target, file_info)
            
            # Source code detection
            elif target.endswith(('.c', '.cpp', '.cc', '.cxx')):
                return self._analyze_source_code(target, 'c/cpp')
            elif target.endswith(('.py', '.pyw')):
                return self._analyze_source_code(target, 'python')
            elif target.endswith(('.js', '.mjs')):
                return self._analyze_source_code(target, 'javascript')
            
            # Firmware/kernel module detection
            elif 'kernel' in file_info.lower() or target.endswith('.ko'):
                return self._analyze_kernel_module(target, file_info)
            
            # Archive/firmware detection
            elif any(fmt in file_info.lower() for fmt in ['zip', 'tar', 'gzip', 'firmware']):
                return self._analyze_archive_firmware(target, file_info)
            
        except Exception as e:
            self.target_info['properties']['analysis_error'] = str(e)
        
        return self.target_info
    
    def _analyze_elf_binary(self, target, file_info):
        """Analyze ELF binary"""
        self.target_info.update({
            'type': 'binary',
            'subtype': 'elf',
            'confidence': 0.95,
            'recommended_workflows': [
                'smart-binary-analysis',
                'smart-exploit',
                'checksec',
                'rop-find-gadgets'
            ],
            'tools': [
                'checksec',
                'pwntools',
                'ropgadget',
                'gdb',
                'radare2'
            ]
        })
        
        # Get more detailed binary info
        try:
            # Check if it's a shared library
            if 'shared object' in file_info:
                self.target_info['subtype'] = 'shared_library'
                self.target_info['recommended_workflows'].append('binary-injection')
            
            # Check architecture
            if 'x86-64' in file_info:
                self.target_info['properties']['arch'] = 'x86_64'
            elif 'i386' in file_info:
                self.target_info['properties']['arch'] = 'i386'
            elif 'ARM' in file_info:
                self.target_info['properties']['arch'] = 'arm'
            
            # Try to get security features
            result = subprocess.run(['file', target], capture_output=True, text=True)
            if 'dynamically linked' in result.stdout:
                self.target_info['properties']['linking'] = 'dynamic'
            elif 'statically linked' in result.stdout:
                self.target_info['properties']['linking'] = 'static'
                
        except Exception as e:
            self.target_info['properties']['detailed_analysis_error'] = str(e)
        
        return self.target_info
    
    def _analyze_pe_binary(self, target, file_info):
        """Analyze PE binary"""
        self.target_info.update({
            'type': 'binary',
            'subtype': 'pe',
            'confidence': 0.95,
            'recommended_workflows': [
                'smart-binary-analysis',
                'pe-analysis',
                'windows-exploit'
            ],
            'tools': [
                'pe_tools',
                'windows_debugger',
                'immunity_debugger'
            ]
        })
        return self.target_info
    
    def _analyze_macho_binary(self, target, file_info):
        """Analyze Mach-O binary"""
        self.target_info.update({
            'type': 'binary',
            'subtype': 'macho',
            'confidence': 0.95,
            'recommended_workflows': [
                'smart-binary-analysis',
                'macos-exploit'
            ],
            'tools': [
                'otool',
                'lldb',
                'class_dump'
            ]
        })
        return self.target_info
    
    def _analyze_kernel_module(self, target, file_info):
        """Analyze kernel module"""
        self.target_info.update({
            'type': 'kernel',
            'subtype': 'module',
            'confidence': 0.9,
            'recommended_workflows': [
                'smart-kernel-analysis',
                'kernel-ioctl-analyze',
                'kernel-fuzz-basic'
            ],
            'tools': [
                'kernel_analyzer',
                'ioctl_detector',
                'kernel_fuzzer'
            ]
        })
        return self.target_info
    
    def _analyze_source_code(self, target, language):
        """Analyze source code"""
        self.target_info.update({
            'type': 'source',
            'subtype': language,
            'confidence': 0.8,
            'recommended_workflows': [
                'source-analysis',
                'static-analysis',
                'compile-and-analyze'
            ],
            'tools': [
                'static_analyzer',
                'compiler',
                'linter'
            ]
        })
        return self.target_info
    
    def _analyze_archive_firmware(self, target, file_info):
        """Analyze archive or firmware"""
        self.target_info.update({
            'type': 'firmware',
            'subtype': 'archive',
            'confidence': 0.7,
            'recommended_workflows': [
                'firmware-extract',
                'firmware-analyze',
                'binwalk-analysis'
            ],
            'tools': [
                'binwalk',
                'firmware_extractor',
                'strings'
            ]
        })
        return self.target_info
    
    def _analyze_device_target(self, target):
        """Analyze device file"""
        self.target_info.update({
            'type': 'device',
            'confidence': 0.8,
            'properties': {
                'device_path': target
            }
        })
        
        if target.startswith('/dev/'):
            self.target_info.update({
                'subtype': 'device_file',
                'recommended_workflows': [
                    'kernel-fuzz-ioctl',
                    'device-analysis'
                ],
                'tools': [
                    'ioctl_fuzzer',
                    'device_analyzer'
                ]
            })
        
        return self.target_info
    
    def _analyze_directory_target(self, target):
        """Analyze directory target"""
        self.target_info.update({
            'type': 'directory',
            'confidence': 0.6,
            'properties': {
                'path': target,
                'file_count': len(list(Path(target).rglob('*')))
            },
            'recommended_workflows': [
                'directory-scan',
                'source-analysis'
            ],
            'tools': [
                'find',
                'grep',
                'static_analyzer'
            ]
        })
        return self.target_info
    
    def _analyze_network_target(self, target):
        """Analyze network target"""
        self.target_info.update({
            'type': 'network',
            'subtype': 'host',
            'confidence': 0.7,
            'properties': {
                'target': target
            },
            'recommended_workflows': [
                'network-scan',
                'port-scan',
                'service-enum'
            ],
            'tools': [
                'nmap',
                'masscan',
                'service_scanner'
            ]
        })
        return self.target_info

def main():
    parser = argparse.ArgumentParser(description='Smart Target Detection System')
    parser.add_argument('target', help='Target to analyze')
    parser.add_argument('--format', choices=['json', 'text'], default='text',
                       help='Output format')
    parser.add_argument('--output', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    detector = TargetDetector()
    result = detector.detect_target_type(args.target)
    
    if args.format == 'json':
        output = json.dumps(result, indent=2)
    else:
        output = f"""Target Analysis Results:
========================
Target: {args.target}
Type: {result['type']}
Subtype: {result.get('subtype', 'N/A')}
Confidence: {result['confidence']:.1%}

Properties:
{json.dumps(result['properties'], indent=2)}

Recommended Workflows:
{chr(10).join(f"  - {wf}" for wf in result['recommended_workflows'])}

Suggested Tools:
{chr(10).join(f"  - {tool}" for tool in result['tools'])}
"""
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
    else:
        print(output)

if __name__ == '__main__':
    main()