#!/usr/bin/env python3
"""
Unified Security Status Checker
Shows status of all security assessment components and tools
"""

import os
import sys
import subprocess
import json
from pathlib import Path

class SecurityStatusChecker:
    """Check status of all security tools and components"""
    
    def __init__(self):
        self.workspace = Path('/workspace')
        self.status = {}
    
    def check_all_status(self):
        """Check status of all security components"""
        print("🔍 Checking unified security framework status...")
        print()
        
        # Check core tools
        self._check_core_tools()
        
        # Check unified security components
        self._check_unified_components()
        
        # Check existing tool integrations
        self._check_tool_integrations()
        
        # Show summary
        self._show_summary()
    
    def _check_core_tools(self):
        """Check core security tools"""
        print("🛠️  Core Security Tools:")
        
        tools = {
            'checksec': ['python3', str(self.workspace / 'tools/security/checksec.py'), '--help'],
            'web_scanner': ['node', str(self.workspace / 'tools/security/scanner.mjs'), '--help'],
            'web_fuzzer': ['node', str(self.workspace / 'tools/security/fuzzer.mjs'), '--help'],
            'pwntools': ['python3', '-c', 'import pwn; print("OK")'],
            'radare2': ['r2', '-v'],
            'gdb': ['gdb', '--version'],
            'lldb': ['lldb', '--version']
        }
        
        for tool_name, command in tools.items():
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print(f"  ✅ {tool_name}: Available")
                    self.status[tool_name] = 'available'
                else:
                    print(f"  ❌ {tool_name}: Error")
                    self.status[tool_name] = 'error'
            except (subprocess.TimeoutExpired, FileNotFoundError):
                print(f"  ❌ {tool_name}: Not found")
                self.status[tool_name] = 'missing'
        
        print()
    
    def _check_unified_components(self):
        """Check unified security framework components"""
        print("🎯 Unified Security Framework:")
        
        components = {
            'target_analyzer': 'tools/unified-security/target_analyzer.py',
            'smart_binary_analysis': 'tools/unified-security/smart_binary_analysis.py',
            'adaptive_web_testing': 'tools/unified-security/adaptive_web_testing.py',
            'smart_fuzzer': 'tools/unified-security/smart_fuzzer.py',
            'report_generator': 'tools/unified-security/report_generator.py'
        }
        
        for comp_name, comp_path in components.items():
            full_path = self.workspace / comp_path
            if full_path.exists():
                print(f"  ✅ {comp_name}: Ready")
                self.status[f"unified_{comp_name}"] = 'ready'
            else:
                print(f"  ❌ {comp_name}: Missing")
                self.status[f"unified_{comp_name}"] = 'missing'
        
        print()
    
    def _check_tool_integrations(self):
        """Check existing tool integrations"""
        print("🔗 Tool Integrations:")
        
        integrations = {
            'exploit_tools': 'tools/exploit/',
            'kernel_debug': 'tools/kernel-debug/',
            'binary_injection': 'tools/injection/',
            'llvm_lifting': 'tools/lifting/'
        }
        
        for int_name, int_path in integrations.items():
            full_path = self.workspace / int_path
            if full_path.exists():
                tool_count = len(list(full_path.glob('*.py'))) + len(list(full_path.glob('*.sh')))
                print(f"  ✅ {int_name}: {tool_count} tools available")
                self.status[f"integration_{int_name}"] = f'{tool_count}_tools'
            else:
                print(f"  ❌ {int_name}: Missing")
                self.status[f"integration_{int_name}"] = 'missing'
        
        print()
    
    def _show_summary(self):
        """Show overall status summary"""
        print("📊 Status Summary:")
        
        available_tools = sum(1 for status in self.status.values() if status == 'available')
        ready_components = sum(1 for status in self.status.values() if status == 'ready')
        missing_items = sum(1 for status in self.status.values() if status in ['missing', 'error'])
        
        print(f"  ✅ Available tools: {available_tools}")
        print(f"  🎯 Ready components: {ready_components}")
        print(f"  ❌ Missing/Error items: {missing_items}")
        
        if missing_items == 0:
            print("  🎉 All systems ready for unified security assessment!")
        elif missing_items <= 2:
            print("  ⚠️  Minor issues detected - most functionality available")
        else:
            print("  🚨 Multiple issues detected - run installation tasks")
        
        print()
        print("💡 Quick fixes:")
        if self.status.get('pwntools') == 'missing':
            print("  - Install pwntools: pf install-pwntools")
        if self.status.get('radare2') == 'missing':
            print("  - Install radare2: sudo apt install radare2")
        if self.status.get('gdb') == 'missing':
            print("  - Install GDB: sudo apt install gdb")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Security Framework Status Checker')
    parser.add_argument('--show-all', action='store_true', help='Show detailed status')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    
    args = parser.parse_args()
    
    checker = SecurityStatusChecker()
    
    if args.show_all or not args.json:
        checker.check_all_status()
    
    if args.json:
        print(json.dumps(checker.status, indent=2))

if __name__ == '__main__':
    main()