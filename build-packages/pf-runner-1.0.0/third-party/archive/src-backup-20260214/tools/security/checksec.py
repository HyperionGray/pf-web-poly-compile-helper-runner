#!/usr/bin/env python3
"""
Binary Security Features Checker (checksec implementation)
Analyzes ELF binaries for security protections like ASLR, NX, PIE, Stack Canaries, etc.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union

class ChecksecAnalyzer:
    """Analyzes binary security features"""
    
    def __init__(self):
        self.results = {}
    
    def check_file_exists(self, binary_path: str) -> bool:
        """Check if binary file exists and is readable"""
        if not os.path.exists(binary_path):
            return False
        if not os.access(binary_path, os.R_OK):
            return False
        return True
    
    def run_command(self, cmd: List[str]) -> Optional[str]:
        """Run a command and return output, or None if failed"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return None
    
    def check_relro(self, binary_path: str) -> str:
        """Check RELRO (RELocation Read-Only) protection"""
        output = self.run_command(['readelf', '-l', binary_path])
        if not output:
            return "Unknown"
        
        has_gnu_relro = "GNU_RELRO" in output
        
        # Check for BIND_NOW in dynamic section
        dyn_output = self.run_command(['readelf', '-d', binary_path])
        has_bind_now = dyn_output and "BIND_NOW" in dyn_output
        
        if has_gnu_relro and has_bind_now:
            return "Full RELRO"
        elif has_gnu_relro:
            return "Partial RELRO"
        else:
            return "No RELRO"
    
    def check_stack_canary(self, binary_path: str) -> bool:
        """Check for stack canaries (stack smashing protection)"""
        # Check for __stack_chk_fail symbol
        output = self.run_command(['nm', '-D', binary_path])
        if output and "__stack_chk_fail" in output:
            return True
        
        # Alternative check with objdump
        output = self.run_command(['objdump', '-t', binary_path])
        if output and "__stack_chk_fail" in output:
            return True
        
        # Check with strings for stack_chk
        output = self.run_command(['strings', binary_path])
        if output and "stack_chk" in output:
            return True
        
        return False
    
    def check_nx(self, binary_path: str) -> bool:
        """Check NX bit (No eXecute) / DEP protection"""
        output = self.run_command(['readelf', '-l', binary_path])
        if not output:
            return False
        
        # Look for GNU_STACK with execute permissions
        lines = output.split('\n')
        for line in lines:
            if "GNU_STACK" in line:
                # If GNU_STACK has 'E' flag, NX is disabled
                if " RWE " in line:
                    return False
                else:
                    return True
        
        # If no GNU_STACK found, assume NX is enabled (default on modern systems)
        return True
    
    def check_pie(self, binary_path: str) -> str:
        """Check PIE (Position Independent Executable)"""
        output = self.run_command(['readelf', '-h', binary_path])
        if not output:
            return "Unknown"
        
        if "Type:" in output:
            if "DYN" in output:
                # Could be PIE or shared library, check for entry point
                if "Entry point address:" in output and "0x" in output:
                    entry_line = [line for line in output.split('\n') if "Entry point address:" in line][0]
                    if "0x0" in entry_line or entry_line.split()[-1] == "0x0":
                        return "DSO"  # Shared library
                    else:
                        return "PIE enabled"
                return "PIE enabled"
            elif "EXEC" in output:
                return "No PIE"
        
        return "Unknown"
    
    def check_rpath(self, binary_path: str) -> bool:
        """Check for RPATH/RUNPATH (potential security issue)"""
        output = self.run_command(['readelf', '-d', binary_path])
        if not output:
            return False
        
        return "RPATH" in output or "RUNPATH" in output
    
    def check_fortify(self, binary_path: str) -> bool:
        """Check for FORTIFY_SOURCE protections"""
        output = self.run_command(['nm', '-D', binary_path])
        if not output:
            return False
        
        # Look for fortified function symbols
        fortified_functions = [
            "__memcpy_chk", "__memmove_chk", "__memset_chk",
            "__strcpy_chk", "__strncpy_chk", "__strcat_chk",
            "__sprintf_chk", "__snprintf_chk", "__printf_chk",
            "__fprintf_chk", "__vprintf_chk", "__vfprintf_chk"
        ]
        
        for func in fortified_functions:
            if func in output:
                return True
        
        return False
    
    def analyze_binary(self, binary_path: str) -> Dict[str, Union[str, bool]]:
        """Perform complete security analysis of a binary"""
        if not self.check_file_exists(binary_path):
            return {"error": f"File not found or not readable: {binary_path}"}
        
        # Check if it's actually an ELF binary
        file_output = self.run_command(['file', binary_path])
        if not file_output or "ELF" not in file_output:
            return {"error": f"Not an ELF binary: {binary_path}"}
        
        results = {
            "file": binary_path,
            "relro": self.check_relro(binary_path),
            "stack_canary": self.check_stack_canary(binary_path),
            "nx": self.check_nx(binary_path),
            "pie": self.check_pie(binary_path),
            "rpath": self.check_rpath(binary_path),
            "fortify": self.check_fortify(binary_path)
        }
        
        return results
    
    def format_results(self, results: Dict, output_format: str = "table") -> str:
        """Format analysis results for display"""
        if "error" in results:
            return f"Error: {results['error']}"
        
        if output_format == "json":
            return json.dumps(results, indent=2)
        
        # Table format
        file_name = os.path.basename(results["file"])
        
        # Color coding for terminal output
        def colorize(value, good_values=None, bad_values=None):
            if not sys.stdout.isatty():
                return str(value)
            
            good_values = good_values or []
            bad_values = bad_values or []
            
            if value in good_values or (isinstance(value, bool) and value):
                return f"\033[92m{value}\033[0m"  # Green
            elif value in bad_values or (isinstance(value, bool) and not value):
                return f"\033[91m{value}\033[0m"  # Red
            else:
                return f"\033[93m{value}\033[0m"  # Yellow
        
        output = f"\nBinary Security Analysis: {file_name}\n"
        output += "=" * (len(output) - 1) + "\n"
        
        output += f"RELRO:           {colorize(results['relro'], ['Full RELRO'], ['No RELRO'])}\n"
        output += f"Stack Canary:    {colorize(results['stack_canary'])}\n"
        output += f"NX:              {colorize(results['nx'])}\n"
        output += f"PIE:             {colorize(results['pie'], ['PIE enabled'], ['No PIE'])}\n"
        output += f"RPATH:           {colorize(results['rpath'], [], [True])}\n"
        output += f"FORTIFY:         {colorize(results['fortify'])}\n"
        
        return output

def main():
    parser = argparse.ArgumentParser(
        description="Analyze binary security features (checksec implementation)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /bin/ls
  %(prog)s --json /usr/bin/gcc
  %(prog)s --batch /usr/bin/
  %(prog)s --report binaries/ --output report.json
        """
    )
    
    parser.add_argument("binary", nargs="?", help="Binary file to analyze")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--batch", metavar="DIR", help="Analyze all binaries in directory")
    parser.add_argument("--report", metavar="DIR", help="Generate comprehensive report for directory")
    parser.add_argument("--output", metavar="FILE", help="Output file for report (default: stdout)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    analyzer = ChecksecAnalyzer()
    
    if args.batch or args.report:
        # Batch analysis
        directory = args.batch or args.report
        if not os.path.isdir(directory):
            print(f"Error: {directory} is not a directory", file=sys.stderr)
            sys.exit(1)
        
        results = []
        for file_path in Path(directory).rglob("*"):
            if file_path.is_file() and os.access(file_path, os.X_OK):
                if args.verbose:
                    print(f"Analyzing: {file_path}", file=sys.stderr)
                
                result = analyzer.analyze_binary(str(file_path))
                if "error" not in result:
                    results.append(result)
        
        if args.report:
            # Generate comprehensive report
            report = {
                "summary": {
                    "total_binaries": len(results),
                    "with_relro": len([r for r in results if "Full RELRO" in r.get("relro", "")]),
                    "with_canary": len([r for r in results if r.get("stack_canary", False)]),
                    "with_nx": len([r for r in results if r.get("nx", False)]),
                    "with_pie": len([r for r in results if "PIE enabled" in r.get("pie", "")]),
                    "with_fortify": len([r for r in results if r.get("fortify", False)])
                },
                "binaries": results
            }
            
            output_text = json.dumps(report, indent=2)
        else:
            # Simple batch output
            if args.json:
                output_text = json.dumps(results, indent=2)
            else:
                output_text = ""
                for result in results:
                    output_text += analyzer.format_results(result, "table") + "\n"
        
        # Write output
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output_text)
            print(f"Report saved to: {args.output}")
        else:
            print(output_text)
    
    elif args.binary:
        # Single binary analysis
        result = analyzer.analyze_binary(args.binary)
        output_format = "json" if args.json else "table"
        print(analyzer.format_results(result, output_format))
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()