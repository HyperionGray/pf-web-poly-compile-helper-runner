#!/usr/bin/env python3
"""
Radare2 Automation
Automate radare2 analysis and reversing tasks with r2pipe.
"""

import sys
import json
from pathlib import Path

try:
    import r2pipe
    R2_AVAILABLE = True
except ImportError:
    R2_AVAILABLE = False
    print("[!] r2pipe not available. Install with: pip install r2pipe")

class Radare2Automation:
    """Automate radare2 analysis"""
    
    def __init__(self, binary_path, commands_path=None):
        self.binary_path = Path(binary_path)
        self.commands_path = Path(commands_path) if commands_path else None
        
        if not self.binary_path.exists():
            raise FileNotFoundError(f"Binary not found: {binary_path}")
        
        if not R2_AVAILABLE:
            raise ImportError("r2pipe library not available")
    
    def get_default_commands(self):
        """Get default analysis commands"""
        return [
            'aaa',              # Analyze all
            'afl',              # List functions
            'ii',               # List imports
            'ie',               # List exports
            'iz',               # List strings
            'pdf @ main',       # Disassemble main
            'agf',              # Print function graph
        ]
    
    def analyze_basic(self, r2):
        """Perform basic analysis"""
        print(f"[*] Running basic analysis...")
        
        # Auto-analyze
        r2.cmd('aaa')
        
        # Get binary info
        info = r2.cmdj('ij')  # JSON output
        print(f"\n=== Binary Information ===")
        print(f"Architecture: {info.get('bin', {}).get('arch', 'unknown')}")
        print(f"Bits: {info.get('bin', {}).get('bits', 'unknown')}")
        print(f"OS: {info.get('bin', {}).get('os', 'unknown')}")
        print(f"Language: {info.get('bin', {}).get('lang', 'unknown')}")
        
        return info
    
    def list_functions(self, r2):
        """List all functions"""
        print(f"\n[*] Listing functions...")
        
        functions = r2.cmdj('aflj')  # JSON format
        if functions:
            print(f"[+] Found {len(functions)} functions:")
            for func in functions[:20]:  # Show first 20
                name = func.get('name', 'unknown')
                offset = func.get('offset', 0)
                size = func.get('size', 0)
                print(f"    {name:40s} @ 0x{offset:08x} (size: {size})")
            
            if len(functions) > 20:
                print(f"    ... and {len(functions) - 20} more")
        
        return functions
    
    def find_vulnerabilities(self, r2):
        """Look for potential vulnerabilities"""
        print(f"\n[*] Searching for potential vulnerabilities...")
        
        vulns = []
        
        # Look for dangerous functions
        dangerous_funcs = [
            'strcpy', 'strcat', 'sprintf', 'gets',
            'scanf', 'vsprintf', 'strncpy'
        ]
        
        imports = r2.cmdj('iij')  # Import list in JSON
        if imports:
            for imp in imports:
                name = imp.get('name', '')
                if any(dangerous in name for dangerous in dangerous_funcs):
                    vulns.append({
                        'type': 'dangerous_function',
                        'name': name,
                        'address': hex(imp.get('plt', 0))
                    })
        
        if vulns:
            print(f"[!] Found {len(vulns)} potentially dangerous functions:")
            for vuln in vulns:
                print(f"    {vuln['name']} @ {vuln['address']}")
        else:
            print(f"[+] No obvious dangerous function imports found")
        
        return vulns
    
    def extract_strings(self, r2):
        """Extract interesting strings"""
        print(f"\n[*] Extracting interesting strings...")
        
        strings = r2.cmdj('izj')  # Strings in JSON
        
        if strings:
            # Filter interesting strings
            interesting_patterns = ['password', 'key', 'secret', 'admin', 'root', 'debug']
            interesting = []
            
            for s in strings:
                string_val = s.get('string', '').lower()
                if any(pattern in string_val for pattern in interesting_patterns):
                    interesting.append(s)
            
            print(f"[+] Found {len(strings)} total strings")
            print(f"[+] Found {len(interesting)} interesting strings:")
            
            for s in interesting[:10]:  # Show first 10
                addr = s.get('vaddr', 0)
                string_val = s.get('string', '')
                print(f"    0x{addr:08x}: {string_val}")
            
            if len(interesting) > 10:
                print(f"    ... and {len(interesting) - 10} more")
        
        return strings
    
    def control_flow_graph(self, r2, function='main'):
        """Generate control flow graph"""
        print(f"\n[*] Generating control flow graph for {function}...")
        
        try:
            # Try to export as dot format
            dot = r2.cmd(f'agfd @ {function}')
            
            if dot:
                output_file = f"{self.binary_path.stem}_{function}_cfg.dot"
                with open(output_file, 'w') as f:
                    f.write(dot)
                print(f"[+] CFG saved to: {output_file}")
                print(f"[*] Convert to image with: dot -Tpng {output_file} -o cfg.png")
                return output_file
        except Exception as e:
            print(f"[-] Could not generate CFG: {e}")
        
        return None
    
    def run_custom_commands(self, r2, commands):
        """Run custom radare2 commands"""
        print(f"\n[*] Running custom commands...")
        
        for cmd in commands:
            print(f"\n--- Command: {cmd} ---")
            output = r2.cmd(cmd)
            print(output)
    
    def run(self):
        """Run automated radare2 analysis"""
        print(f"\n=== Radare2 Automation ===")
        print(f"Analyzing: {self.binary_path}")
        
        try:
            # Open binary with r2pipe
            r2 = r2pipe.open(str(self.binary_path))
            
            # Run analyses
            self.analyze_basic(r2)
            functions = self.list_functions(r2)
            vulns = self.find_vulnerabilities(r2)
            strings = self.extract_strings(r2)
            
            # Generate CFG for main function
            if functions and any(f.get('name') == 'main' for f in functions):
                self.control_flow_graph(r2, 'main')
            
            # Run custom commands if provided
            if self.commands_path and self.commands_path.exists():
                with open(self.commands_path, 'r') as f:
                    custom_commands = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                self.run_custom_commands(r2, custom_commands)
            
            r2.quit()
            
            print(f"\n[+] Analysis complete!")
            
        except Exception as e:
            print(f"[-] Error during analysis: {e}")
            raise

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <binary_path> [commands_file]")
        print(f"\nExample:")
        print(f"  {sys.argv[0]} /path/to/binary")
        print(f"  {sys.argv[0]} /path/to/binary commands.txt")
        print(f"\ncommands_file should contain one r2 command per line")
        sys.exit(1)
    
    if not R2_AVAILABLE:
        print(f"Error: r2pipe not available")
        print(f"Install with: pip install r2pipe")
        sys.exit(1)
    
    binary_path = sys.argv[1]
    commands_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        automation = Radare2Automation(binary_path, commands_path)
        automation.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
