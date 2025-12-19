#!/usr/bin/env python3
"""
Unified Checksec - Smart binary security analysis
Consolidates multiple checksec implementations and chooses the best approach
Part of the pf unified tools system
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union

class UnifiedChecksec:
    """Unified interface for binary security analysis"""
    
    def __init__(self):
        self.available_tools = self._detect_available_tools()
        self.preferred_tool = self._select_preferred_tool()
    
    def _detect_available_tools(self) -> Dict[str, Dict[str, Union[bool, str]]]:
        """Detect available checksec implementations"""
        tools = {}
        
        # System checksec (checksec.sh)
        try:
            result = subprocess.run(['which', 'checksec'], capture_output=True, check=True)
            tools['system_checksec'] = {
                'available': True,
                'path': result.stdout.decode().strip(),
                'type': 'system',
                'priority': 3
            }
        except subprocess.CalledProcessError:
            tools['system_checksec'] = {'available': False}
        
        # pf checksec (Python implementation)
        pf_checksec_path = 'tools/security/checksec.py'
        if os.path.exists(pf_checksec_path):
            tools['pf_checksec'] = {
                'available': True,
                'path': pf_checksec_path,
                'type': 'python',
                'priority': 2
            }
        else:
            tools['pf_checksec'] = {'available': False}
        
        # pwntools checksec
        try:
            subprocess.run(['python3', '-c', 'import pwn; pwn.checksec'], 
                         capture_output=True, check=True)
            tools['pwntools_checksec'] = {
                'available': True,
                'path': 'python3',
                'type': 'pwntools',
                'priority': 1
            }
        except subprocess.CalledProcessError:
            tools['pwntools_checksec'] = {'available': False}
        
        # readelf/objdump fallback
        readelf_available = self._command_exists('readelf')
        objdump_available = self._command_exists('objdump')
        if readelf_available or objdump_available:
            tools['manual_analysis'] = {
                'available': True,
                'path': 'readelf' if readelf_available else 'objdump',
                'type': 'manual',
                'priority': 0
            }
        else:
            tools['manual_analysis'] = {'available': False}
        
        return tools
    
    def _command_exists(self, command: str) -> bool:
        """Check if a command exists"""
        try:
            subprocess.run(['which', command], capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _select_preferred_tool(self) -> Optional[str]:
        """Select the best available tool based on priority"""
        available = [(name, info) for name, info in self.available_tools.items() 
                    if info.get('available', False)]
        
        if not available:
            return None
        
        # Sort by priority (higher is better)
        available.sort(key=lambda x: x[1].get('priority', 0), reverse=True)
        return available[0][0]
    
    def analyze_binary(self, binary_path: str, output_format: str = 'json') -> Dict[str, any]:
        """Analyze binary security features using the best available tool"""
        if not os.path.exists(binary_path):
            return {'error': f'Binary {binary_path} does not exist'}
        
        if not self.preferred_tool:
            return {'error': 'No checksec tools available'}
        
        print(f"🛡️ Using {self.preferred_tool} for security analysis...")
        
        try:
            if self.preferred_tool == 'system_checksec':
                return self._run_system_checksec(binary_path, output_format)
            elif self.preferred_tool == 'pf_checksec':
                return self._run_pf_checksec(binary_path, output_format)
            elif self.preferred_tool == 'pwntools_checksec':
                return self._run_pwntools_checksec(binary_path, output_format)
            elif self.preferred_tool == 'manual_analysis':
                return self._run_manual_analysis(binary_path, output_format)
            else:
                return {'error': f'Unknown tool: {self.preferred_tool}'}
        except Exception as e:
            # Fallback to next available tool
            return self._fallback_analysis(binary_path, output_format, str(e))
    
    def _run_system_checksec(self, binary_path: str, output_format: str) -> Dict[str, any]:
        """Run system checksec tool"""
        if output_format == 'json':
            cmd = ['checksec', '--format=json', '--file', binary_path]
        else:
            cmd = ['checksec', '--file', binary_path]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        if output_format == 'json':
            return json.loads(result.stdout)
        else:
            return {'output': result.stdout, 'tool': 'system_checksec'}
    
    def _run_pf_checksec(self, binary_path: str, output_format: str) -> Dict[str, any]:
        """Run pf Python checksec implementation"""
        cmd = ['python3', 'tools/security/checksec.py']
        if output_format == 'json':
            cmd.append('--json')
        cmd.append(binary_path)
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        if output_format == 'json':
            return json.loads(result.stdout)
        else:
            return {'output': result.stdout, 'tool': 'pf_checksec'}
    
    def _run_pwntools_checksec(self, binary_path: str, output_format: str) -> Dict[str, any]:
        """Run pwntools checksec"""
        script = f"""
import pwn
import json
import sys

try:
    result = pwn.checksec('{binary_path}')
    if '{output_format}' == 'json':
        # Convert pwntools result to JSON
        output = {{
            'relro': 'Full' if result.relro else 'No',
            'canary': result.canary,
            'nx': result.nx,
            'pie': result.pie,
            'rpath': result.rpath,
            'runpath': result.runpath,
            'symbols': not result.stripped,
            'fortify': result.fortify,
            'tool': 'pwntools_checksec'
        }}
        print(json.dumps(output, indent=2))
    else:
        print(str(result))
except Exception as e:
    print(f"Error: {{e}}", file=sys.stderr)
    sys.exit(1)
"""
        
        result = subprocess.run(['python3', '-c', script], 
                              capture_output=True, text=True, check=True)
        
        if output_format == 'json':
            return json.loads(result.stdout)
        else:
            return {'output': result.stdout, 'tool': 'pwntools_checksec'}
    
    def _run_manual_analysis(self, binary_path: str, output_format: str) -> Dict[str, any]:
        """Run manual analysis using readelf/objdump"""
        analysis = {
            'tool': 'manual_analysis',
            'relro': 'Unknown',
            'canary': False,
            'nx': False,
            'pie': False,
            'stripped': True,
            'fortify': False
        }
        
        try:
            # Check for stack canary
            result = subprocess.run(['readelf', '-s', binary_path], 
                                  capture_output=True, text=True)
            if '__stack_chk_fail' in result.stdout:
                analysis['canary'] = True
            
            # Check for NX bit
            result = subprocess.run(['readelf', '-W', '-l', binary_path], 
                                  capture_output=True, text=True)
            if 'GNU_STACK' in result.stdout and 'RWE' not in result.stdout:
                analysis['nx'] = True
            
            # Check for PIE
            result = subprocess.run(['readelf', '-h', binary_path], 
                                  capture_output=True, text=True)
            if 'DYN' in result.stdout:
                analysis['pie'] = True
            
            # Check if stripped
            result = subprocess.run(['readelf', '--symbols', binary_path], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                analysis['stripped'] = False
            
        except subprocess.CalledProcessError:
            pass
        
        if output_format == 'json':
            return analysis
        else:
            output = f"Manual Analysis Results for {binary_path}:\n"
            output += f"RELRO: {analysis['relro']}\n"
            output += f"Stack Canary: {'Yes' if analysis['canary'] else 'No'}\n"
            output += f"NX: {'Yes' if analysis['nx'] else 'No'}\n"
            output += f"PIE: {'Yes' if analysis['pie'] else 'No'}\n"
            output += f"Stripped: {'Yes' if analysis['stripped'] else 'No'}\n"
            return {'output': output, 'tool': 'manual_analysis'}
    
    def _fallback_analysis(self, binary_path: str, output_format: str, error: str) -> Dict[str, any]:
        """Fallback to next available tool if primary fails"""
        print(f"⚠️ Primary tool failed ({error}), trying fallback...")
        
        # Remove failed tool and try next
        available_tools = [(name, info) for name, info in self.available_tools.items() 
                          if info.get('available', False) and name != self.preferred_tool]
        
        if not available_tools:
            return {'error': f'All tools failed. Last error: {error}'}
        
        # Try next best tool
        available_tools.sort(key=lambda x: x[1].get('priority', 0), reverse=True)
        fallback_tool = available_tools[0][0]
        
        print(f"🔄 Falling back to {fallback_tool}...")
        
        try:
            if fallback_tool == 'manual_analysis':
                return self._run_manual_analysis(binary_path, output_format)
            # Add other fallback cases as needed
        except Exception as fallback_error:
            return {'error': f'Fallback also failed: {fallback_error}'}
        
        return {'error': 'No working tools available'}
    
    def analyze_batch(self, directory: str, output_format: str = 'json') -> Dict[str, any]:
        """Analyze all binaries in a directory"""
        if not os.path.isdir(directory):
            return {'error': f'Directory {directory} does not exist'}
        
        results = {}
        binary_files = []
        
        # Find binary files
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if os.access(file_path, os.X_OK) and not os.path.isdir(file_path):
                    binary_files.append(file_path)
        
        print(f"🔍 Found {len(binary_files)} potential binaries to analyze...")
        
        for binary_path in binary_files:
            print(f"📊 Analyzing {binary_path}...")
            try:
                result = self.analyze_binary(binary_path, output_format)
                results[binary_path] = result
            except Exception as e:
                results[binary_path] = {'error': str(e)}
        
        return {
            'batch_results': results,
            'total_analyzed': len(binary_files),
            'tool_used': self.preferred_tool
        }
    
    def get_tool_info(self) -> Dict[str, any]:
        """Get information about available tools"""
        return {
            'available_tools': self.available_tools,
            'preferred_tool': self.preferred_tool,
            'tool_priorities': {
                'pwntools_checksec': 'Highest - Most comprehensive',
                'pf_checksec': 'High - Custom implementation',
                'system_checksec': 'Medium - Standard tool',
                'manual_analysis': 'Lowest - Basic fallback'
            }
        }


def main():
    parser = argparse.ArgumentParser(description='Unified Checksec - Smart binary security analysis')
    parser.add_argument('binary', nargs='?', help='Binary file to analyze')
    parser.add_argument('--batch', action='store_true', help='Analyze all binaries in directory')
    parser.add_argument('--format', choices=['json', 'text'], default='text', help='Output format')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    parser.add_argument('--tool-info', action='store_true', help='Show available tools information')
    
    args = parser.parse_args()
    
    checksec = UnifiedChecksec()
    
    if args.tool_info:
        info = checksec.get_tool_info()
        print(json.dumps(info, indent=2))
        return
    
    if not args.binary:
        parser.print_help()
        return
    
    if args.batch:
        results = checksec.analyze_batch(args.binary, args.format)
    else:
        results = checksec.analyze_binary(args.binary, args.format)
    
    # Format output
    if args.format == 'json':
        output = json.dumps(results, indent=2)
    else:
        if 'output' in results:
            output = results['output']
        else:
            output = json.dumps(results, indent=2)
    
    # Write output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Results saved to: {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()