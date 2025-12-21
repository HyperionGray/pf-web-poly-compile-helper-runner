#!/usr/bin/env python3
"""
Smart ROP Analysis Tool
Intelligently selects between ROPgadget and ropper based on binary characteristics
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

class SmartROP:
    def __init__(self):
        self.results = {
            'binary': '',
            'tool_used': '',
            'gadgets': [],
            'chains': [],
            'analysis': {},
            'recommendations': []
        }
    
    def analyze_rop_potential(self, binary_path, binary_analysis=None):
        """Main ROP analysis function"""
        self.results['binary'] = binary_path
        
        # Load binary analysis if provided
        if binary_analysis and os.path.exists(binary_analysis):
            with open(binary_analysis, 'r') as f:
                bin_info = json.load(f)
        else:
            bin_info = {}
        
        # Select optimal ROP tool
        tool = self._select_rop_tool(binary_path, bin_info)
        self.results['tool_used'] = tool
        
        # Run ROP analysis
        if tool == 'ropgadget':
            self._analyze_with_ropgadget(binary_path)
        elif tool == 'ropper':
            self._analyze_with_ropper(binary_path)
        else:
            # Fallback: try both
            self._analyze_with_both(binary_path)
        
        # Analyze results
        self._analyze_rop_quality()
        self._generate_recommendations(bin_info)
        
        return self.results
    
    def _select_rop_tool(self, binary_path, bin_info):
        """Intelligently select ROP tool based on binary characteristics"""
        
        # Check tool availability
        ropgadget_available = self._check_tool_available('ROPgadget')
        ropper_available = self._check_tool_available('ropper')
        
        if not ropgadget_available and not ropper_available:
            return 'none'
        elif not ropgadget_available:
            return 'ropper'
        elif not ropper_available:
            return 'ropgadget'
        
        # Decision logic based on binary characteristics
        arch = bin_info.get('arch', '')
        file_size = bin_info.get('properties', {}).get('size', 0)
        
        # ROPgadget is generally faster and more reliable for x86/x64
        if arch in ['x86_64', 'i386']:
            # For large binaries, ropper might be more efficient
            if file_size > 10 * 1024 * 1024:  # 10MB
                return 'ropper'
            else:
                return 'ropgadget'
        
        # For ARM and other architectures, ropper often has better support
        elif arch in ['arm', 'aarch64']:
            return 'ropper'
        
        # Default to ROPgadget
        return 'ropgadget'
    
    def _check_tool_available(self, tool):
        """Check if a tool is available"""
        try:
            result = subprocess.run([tool, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _analyze_with_ropgadget(self, binary_path):
        """Analyze with ROPgadget"""
        try:
            # Find gadgets
            result = subprocess.run(['ROPgadget', '--binary', binary_path], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                gadgets = self._parse_ropgadget_output(result.stdout)
                self.results['gadgets'] = gadgets
                
                # Try to build ROP chain
                chain_result = subprocess.run(['ROPgadget', '--binary', binary_path, '--ropchain'], 
                                            capture_output=True, text=True, timeout=60)
                
                if chain_result.returncode == 0:
                    chains = self._parse_ropgadget_chain(chain_result.stdout)
                    self.results['chains'] = chains
                    
        except Exception as e:
            self.results['analysis']['ropgadget_error'] = str(e)
    
    def _analyze_with_ropper(self, binary_path):
        """Analyze with ropper"""
        try:
            # Find gadgets
            result = subprocess.run(['ropper', '--file', binary_path, '--nocolor'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                gadgets = self._parse_ropper_output(result.stdout)
                self.results['gadgets'] = gadgets
                
                # Try to build chain for execve
                chain_result = subprocess.run(['ropper', '--file', binary_path, 
                                             '--chain', 'execve'], 
                                            capture_output=True, text=True, timeout=60)
                
                if chain_result.returncode == 0:
                    chains = self._parse_ropper_chain(chain_result.stdout)
                    self.results['chains'] = chains
                    
        except Exception as e:
            self.results['analysis']['ropper_error'] = str(e)
    
    def _analyze_with_both(self, binary_path):
        """Try both tools and combine results"""
        self._analyze_with_ropgadget(binary_path)
        
        # Store ROPgadget results
        ropgadget_results = {
            'gadgets': self.results['gadgets'].copy(),
            'chains': self.results['chains'].copy()
        }
        
        # Clear and try ropper
        self.results['gadgets'] = []
        self.results['chains'] = []
        self._analyze_with_ropper(binary_path)
        
        # Combine results
        self.results['analysis']['ropgadget_results'] = ropgadget_results
        self.results['analysis']['ropper_results'] = {
            'gadgets': self.results['gadgets'].copy(),
            'chains': self.results['chains'].copy()
        }
        
        # Use the tool that found more gadgets
        if len(ropgadget_results['gadgets']) >= len(self.results['gadgets']):
            self.results['gadgets'] = ropgadget_results['gadgets']
            self.results['chains'] = ropgadget_results['chains']
            self.results['tool_used'] = 'ropgadget'
        else:
            self.results['tool_used'] = 'ropper'
    
    def _parse_ropgadget_output(self, output):
        """Parse ROPgadget output"""
        gadgets = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line and 'ret' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    address = parts[0].strip()
                    instruction = parts[1].strip()
                    gadgets.append({
                        'address': address,
                        'instruction': instruction,
                        'tool': 'ropgadget'
                    })
        
        return gadgets
    
    def _parse_ropper_output(self, output):
        """Parse ropper output"""
        gadgets = []
        lines = output.split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line and ('ret' in line or 'pop' in line):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    address = parts[0].strip()
                    instruction = parts[1].strip()
                    gadgets.append({
                        'address': address,
                        'instruction': instruction,
                        'tool': 'ropper'
                    })
        
        return gadgets
    
    def _parse_ropgadget_chain(self, output):
        """Parse ROPgadget chain output"""
        chains = []
        if 'ROP chain generation' in output:
            # Extract the generated chain
            lines = output.split('\n')
            chain_lines = []
            in_chain = False
            
            for line in lines:
                if 'ROP chain generation' in line:
                    in_chain = True
                elif in_chain and line.strip():
                    chain_lines.append(line.strip())
            
            if chain_lines:
                chains.append({
                    'type': 'execve',
                    'chain': chain_lines,
                    'tool': 'ropgadget'
                })
        
        return chains
    
    def _parse_ropper_chain(self, output):
        """Parse ropper chain output"""
        chains = []
        if 'Chain' in output:
            lines = output.split('\n')
            chain_lines = []
            
            for line in lines:
                if line.strip() and ('0x' in line or 'p +=' in line):
                    chain_lines.append(line.strip())
            
            if chain_lines:
                chains.append({
                    'type': 'execve',
                    'chain': chain_lines,
                    'tool': 'ropper'
                })
        
        return chains
    
    def _analyze_rop_quality(self):
        """Analyze the quality of found ROP gadgets"""
        analysis = {}
        
        # Count gadget types
        gadget_types = {}
        useful_gadgets = []
        
        for gadget in self.results['gadgets']:
            instruction = gadget['instruction'].lower()
            
            # Categorize gadgets
            if 'pop' in instruction and 'ret' in instruction:
                gadget_type = 'pop_ret'
            elif 'mov' in instruction and 'ret' in instruction:
                gadget_type = 'mov_ret'
            elif 'add' in instruction and 'ret' in instruction:
                gadget_type = 'add_ret'
            elif 'sub' in instruction and 'ret' in instruction:
                gadget_type = 'sub_ret'
            elif 'xor' in instruction and 'ret' in instruction:
                gadget_type = 'xor_ret'
            elif 'syscall' in instruction or 'int 0x80' in instruction:
                gadget_type = 'syscall'
            else:
                gadget_type = 'other'
            
            gadget_types[gadget_type] = gadget_types.get(gadget_type, 0) + 1
            
            # Mark useful gadgets
            if gadget_type in ['pop_ret', 'syscall', 'mov_ret']:
                useful_gadgets.append(gadget)
        
        analysis['gadget_count'] = len(self.results['gadgets'])
        analysis['gadget_types'] = gadget_types
        analysis['useful_gadgets'] = len(useful_gadgets)
        analysis['chain_count'] = len(self.results['chains'])
        
        # Calculate ROP potential score
        score = 0
        if analysis['gadget_count'] > 100:
            score += 30
        elif analysis['gadget_count'] > 50:
            score += 20
        elif analysis['gadget_count'] > 10:
            score += 10
        
        if gadget_types.get('pop_ret', 0) > 5:
            score += 25
        if gadget_types.get('syscall', 0) > 0:
            score += 20
        if analysis['chain_count'] > 0:
            score += 25
        
        analysis['rop_potential_score'] = min(score, 100)
        
        self.results['analysis'] = analysis
    
    def _generate_recommendations(self, bin_info):
        """Generate ROP exploitation recommendations"""
        recommendations = []
        analysis = self.results['analysis']
        
        if analysis['rop_potential_score'] > 70:
            recommendations.append("HIGH ROP potential - binary is highly exploitable via ROP")
        elif analysis['rop_potential_score'] > 40:
            recommendations.append("MEDIUM ROP potential - ROP exploitation possible with effort")
        else:
            recommendations.append("LOW ROP potential - consider other exploitation techniques")
        
        # Specific recommendations based on gadgets found
        gadget_types = analysis.get('gadget_types', {})
        
        if gadget_types.get('pop_ret', 0) > 5:
            recommendations.append("Good pop/ret gadgets available - can control registers")
        
        if gadget_types.get('syscall', 0) > 0:
            recommendations.append("Syscall gadgets found - direct system call exploitation possible")
        
        if analysis['chain_count'] > 0:
            recommendations.append("Automatic ROP chain generated - ready for exploitation")
        
        # Recommendations based on binary security features
        if bin_info:
            security_features = bin_info.get('security_features', {})
            
            if security_features.get('nx') == 'Yes':
                recommendations.append("NX bit enabled - ROP is necessary to execute shellcode")
            
            if security_features.get('pie') == 'No':
                recommendations.append("No PIE - gadget addresses are fixed, simplifying exploitation")
            
            if security_features.get('canary') == 'No':
                recommendations.append("No stack canary - stack overflow + ROP is straightforward")
        
        self.results['recommendations'] = recommendations

def main():
    parser = argparse.ArgumentParser(description='Smart ROP Analysis Tool')
    parser.add_argument('binary', help='Binary file to analyze')
    parser.add_argument('--input', help='Binary analysis JSON file')
    parser.add_argument('--output', help='Output file (default: stdout)')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    args = parser.parse_args()
    
    try:
        rop_analyzer = SmartROP()
        results = rop_analyzer.analyze_rop_potential(args.binary, args.input)
        
        if args.json:
            output = json.dumps(results, indent=2)
        else:
            # Format for human reading
            analysis = results['analysis']
            output = f"""Smart ROP Analysis: {args.binary}
{'='*50}
Tool Used: {results['tool_used']}
Gadgets Found: {analysis['gadget_count']}
Useful Gadgets: {analysis['useful_gadgets']}
ROP Chains: {analysis['chain_count']}
ROP Potential Score: {analysis['rop_potential_score']}/100

Gadget Types:
"""
            
            for gadget_type, count in analysis.get('gadget_types', {}).items():
                output += f"  {gadget_type}: {count}\n"
            
            output += "\nRecommendations:\n"
            for rec in results['recommendations']:
                output += f"  • {rec}\n"
            
            if results['chains']:
                output += f"\nGenerated ROP Chains ({len(results['chains'])}):\n"
                for i, chain in enumerate(results['chains']):
                    output += f"  Chain {i+1} ({chain['type']}):\n"
                    for line in chain['chain'][:5]:  # Show first 5 lines
                        output += f"    {line}\n"
                    if len(chain['chain']) > 5:
                        output += f"    ... ({len(chain['chain']) - 5} more lines)\n"
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
        else:
            print(output)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()