#!/usr/bin/env python3
"""
Smart Target Detection System
Intelligently detects target types and recommends appropriate workflows
Combined from PRs #194, #195
"""

import os
import sys
import json
import argparse
import urllib.parse

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
        
        return self.target_info
    
    def _is_url(self, target):
        """Check if target is a URL"""
        parsed = urllib.parse.urlparse(target)
        return parsed.scheme in ['http', 'https', 'ftp', 'ftps']
    
    def _analyze_web_target(self, target):
        """Analyze web application target"""
        self.target_info.update({
            'type': 'web',
            'subtype': 'application',
            'confidence': 0.9,
            'properties': {'url': target},
            'recommended_workflows': ['autoweb', 'smart-web-security', 'security-scan'],
            'tools': ['web_scanner', 'web_fuzzer']
        })
        return self.target_info
    
    def _analyze_file_target(self, target):
        """Analyze file target"""
        try:
            import subprocess
            result = subprocess.run(['file', target], capture_output=True, text=True, timeout=5)
            file_info = result.stdout.strip()
            
            if 'ELF' in file_info:
                return self._analyze_elf_binary(target, file_info)
        except Exception:
            pass
        
        return self.target_info
    
    def _analyze_elf_binary(self, target, file_info):
        """Analyze ELF binary"""
        self.target_info.update({
            'type': 'binary',
            'subtype': 'elf',
            'confidence': 0.95,
            'recommended_workflows': ['autopwn', 'smart-binary-analysis', 'checksec'],
            'tools': ['checksec', 'pwntools', 'ropgadget']
        })
        
        if 'x86-64' in file_info or 'x86_64' in file_info:
            self.target_info['properties']['arch'] = 'x86_64'
        
        return self.target_info
    
    def _analyze_directory_target(self, target):
        """Analyze directory target"""
        self.target_info.update({
            'type': 'directory',
            'confidence': 0.6,
            'properties': {'path': target},
            'recommended_workflows': ['directory-scan'],
            'tools': ['find', 'grep']
        })
        return self.target_info

def main():
    parser = argparse.ArgumentParser(description='Smart Target Detection System')
    parser.add_argument('target', help='Target to analyze')
    parser.add_argument('--format', choices=['json', 'text'], default='text')
    
    args = parser.parse_args()
    
    detector = TargetDetector()
    result = detector.detect_target_type(args.target)
    
    if args.format == 'json':
        print(json.dumps(result, indent=2))
    else:
        print(f"""Target Analysis Results:
========================
Target: {args.target}
Type: {result['type']}
Confidence: {result['confidence']:.1%}

Recommended Workflows:
{chr(10).join(f"  - {wf}" for wf in result['recommended_workflows'])}
""")

if __name__ == '__main__':
    main()
