#!/usr/bin/env python3
"""
Unified Binary Security Analysis (Consolidated checksec)
Combines and enhances all checksec implementations into a single authoritative tool
"""

import os
import sys
import json
import argparse
import subprocess
import struct
from pathlib import Path

class UnifiedChecksec:
    def __init__(self):
        self.results = {
            'file': '',
            'arch': '',
            'endian': '',
            'class': '',
            'security_features': {},
            'vulnerabilities': [],
            'recommendations': [],
            'risk_score': 0
        }
    
    def analyze_binary(self, binary_path):
        """Main analysis function"""
        if not os.path.exists(binary_path):
            raise FileNotFoundError(f"Binary not found: {binary_path}")
        
        self.results['file'] = binary_path
        
        # Basic file analysis
        self._analyze_file_type(binary_path)
        
        # Security feature analysis
        self._check_relro(binary_path)
        self._check_stack_canary(binary_path)
        self._check_nx_bit(binary_path)
        self._check_pie(binary_path)
        self._check_rpath(binary_path)
        self._check_runpath(binary_path)
        self._check_symbols(binary_path)
        self._check_fortify(binary_path)
        
        # Advanced analysis
        self._analyze_sections(binary_path)
        self._check_dangerous_functions(binary_path)
        self._calculate_risk_score()
        self._generate_recommendations()
        
        return self.results
    
    def _analyze_file_type(self, binary_path):
        """Analyze basic file properties"""
        try:
            result = subprocess.run(['file', binary_path], 
                                  capture_output=True, text=True)
            file_info = result.stdout.strip()
            
            # Extract architecture
            if 'x86-64' in file_info or 'x86_64' in file_info:
                self.results['arch'] = 'x86_64'
            elif 'i386' in file_info or '80386' in file_info:
                self.results['arch'] = 'i386'
            elif 'ARM' in file_info:
                self.results['arch'] = 'arm'
            elif 'MIPS' in file_info:
                self.results['arch'] = 'mips'
            
            # Extract endianness
            if 'LSB' in file_info:
                self.results['endian'] = 'little'
            elif 'MSB' in file_info:
                self.results['endian'] = 'big'
            
            # Extract class
            if '64-bit' in file_info:
                self.results['class'] = '64-bit'
            elif '32-bit' in file_info:
                self.results['class'] = '32-bit'
                
        except Exception as e:
            self.results['analysis_errors'] = self.results.get('analysis_errors', [])
            self.results['analysis_errors'].append(f"File analysis error: {e}")
    
    def _check_relro(self, binary_path):
        """Check RELRO (RELocation Read-Only) protection"""
        try:
            result = subprocess.run(['readelf', '-l', binary_path], 
                                  capture_output=True, text=True)
            
            if 'GNU_RELRO' in result.stdout:
                # Check if it's full or partial RELRO
                result2 = subprocess.run(['readelf', '-d', binary_path], 
                                       capture_output=True, text=True)
                if 'BIND_NOW' in result2.stdout:
                    self.results['security_features']['relro'] = 'Full'
                else:
                    self.results['security_features']['relro'] = 'Partial'
            else:
                self.results['security_features']['relro'] = 'No'
                self.results['vulnerabilities'].append({
                    'type': 'missing_relro',
                    'severity': 'medium',
                    'description': 'No RELRO protection - GOT can be overwritten'
                })
        except Exception as e:
            self.results['security_features']['relro'] = 'Unknown'
    
    def _check_stack_canary(self, binary_path):
        """Check stack canary protection"""
        try:
            result = subprocess.run(['readelf', '-s', binary_path], 
                                  capture_output=True, text=True)
            
            if '__stack_chk_fail' in result.stdout:
                self.results['security_features']['canary'] = 'Yes'
            else:
                self.results['security_features']['canary'] = 'No'
                self.results['vulnerabilities'].append({
                    'type': 'no_stack_canary',
                    'severity': 'high',
                    'description': 'No stack canary - vulnerable to stack buffer overflows'
                })
        except Exception as e:
            self.results['security_features']['canary'] = 'Unknown'
    
    def _check_nx_bit(self, binary_path):
        """Check NX bit (No eXecute) protection"""
        try:
            result = subprocess.run(['readelf', '-l', binary_path], 
                                  capture_output=True, text=True)
            
            # Look for GNU_STACK with execute permissions
            lines = result.stdout.split('\n')
            for line in lines:
                if 'GNU_STACK' in line:
                    if 'RWE' in line:
                        self.results['security_features']['nx'] = 'No'
                        self.results['vulnerabilities'].append({
                            'type': 'executable_stack',
                            'severity': 'high',
                            'description': 'Stack is executable - shellcode execution possible'
                        })
                    else:
                        self.results['security_features']['nx'] = 'Yes'
                    break
            else:
                self.results['security_features']['nx'] = 'Unknown'
        except Exception as e:
            self.results['security_features']['nx'] = 'Unknown'
    
    def _check_pie(self, binary_path):
        """Check PIE (Position Independent Executable) protection"""
        try:
            result = subprocess.run(['readelf', '-h', binary_path], 
                                  capture_output=True, text=True)
            
            if 'Type:' in result.stdout:
                if 'DYN' in result.stdout:
                    # Check if it's PIE or just a shared library
                    result2 = subprocess.run(['readelf', '-d', binary_path], 
                                           capture_output=True, text=True)
                    if 'DEBUG' in result2.stdout:
                        self.results['security_features']['pie'] = 'Yes'
                    else:
                        self.results['security_features']['pie'] = 'DSO'
                elif 'EXEC' in result.stdout:
                    self.results['security_features']['pie'] = 'No'
                    self.results['vulnerabilities'].append({
                        'type': 'no_pie',
                        'severity': 'medium',
                        'description': 'No PIE - fixed memory layout aids exploitation'
                    })
        except Exception as e:
            self.results['security_features']['pie'] = 'Unknown'
    
    def _check_rpath(self, binary_path):
        """Check for dangerous RPATH"""
        try:
            result = subprocess.run(['readelf', '-d', binary_path], 
                                  capture_output=True, text=True)
            
            rpath_found = False
            for line in result.stdout.split('\n'):
                if 'RPATH' in line:
                    rpath_found = True
                    rpath_value = line.split('[')[1].split(']')[0] if '[' in line else ''
                    self.results['security_features']['rpath'] = rpath_value
                    
                    # Check for dangerous RPATH values
                    dangerous_paths = ['.', '..', '/tmp', '$ORIGIN']
                    if any(path in rpath_value for path in dangerous_paths):
                        self.results['vulnerabilities'].append({
                            'type': 'dangerous_rpath',
                            'severity': 'medium',
                            'description': f'Dangerous RPATH: {rpath_value}'
                        })
                    break
            
            if not rpath_found:
                self.results['security_features']['rpath'] = 'None'
        except Exception as e:
            self.results['security_features']['rpath'] = 'Unknown'
    
    def _check_runpath(self, binary_path):
        """Check for dangerous RUNPATH"""
        try:
            result = subprocess.run(['readelf', '-d', binary_path], 
                                  capture_output=True, text=True)
            
            runpath_found = False
            for line in result.stdout.split('\n'):
                if 'RUNPATH' in line:
                    runpath_found = True
                    runpath_value = line.split('[')[1].split(']')[0] if '[' in line else ''
                    self.results['security_features']['runpath'] = runpath_value
                    
                    # Check for dangerous RUNPATH values
                    dangerous_paths = ['.', '..', '/tmp', '$ORIGIN']
                    if any(path in runpath_value for path in dangerous_paths):
                        self.results['vulnerabilities'].append({
                            'type': 'dangerous_runpath',
                            'severity': 'medium',
                            'description': f'Dangerous RUNPATH: {runpath_value}'
                        })
                    break
            
            if not runpath_found:
                self.results['security_features']['runpath'] = 'None'
        except Exception as e:
            self.results['security_features']['runpath'] = 'Unknown'
    
    def _check_symbols(self, binary_path):
        """Check symbol table information"""
        try:
            result = subprocess.run(['readelf', '-s', binary_path], 
                                  capture_output=True, text=True)
            
            if 'Symbol table' in result.stdout:
                self.results['security_features']['symbols'] = 'Yes'
                # Count symbols for analysis
                symbol_count = result.stdout.count('\n') - 5  # Approximate
                self.results['security_features']['symbol_count'] = symbol_count
            else:
                self.results['security_features']['symbols'] = 'Stripped'
        except Exception as e:
            self.results['security_features']['symbols'] = 'Unknown'
    
    def _check_fortify(self, binary_path):
        """Check for FORTIFY_SOURCE protection"""
        try:
            result = subprocess.run(['readelf', '-s', binary_path], 
                                  capture_output=True, text=True)
            
            fortified_functions = [
                '__memcpy_chk', '__memmove_chk', '__memset_chk',
                '__strcpy_chk', '__strncpy_chk', '__strcat_chk',
                '__sprintf_chk', '__snprintf_chk', '__printf_chk'
            ]
            
            found_fortified = []
            for func in fortified_functions:
                if func in result.stdout:
                    found_fortified.append(func)
            
            if found_fortified:
                self.results['security_features']['fortify'] = 'Yes'
                self.results['security_features']['fortified_functions'] = found_fortified
            else:
                self.results['security_features']['fortify'] = 'No'
        except Exception as e:
            self.results['security_features']['fortify'] = 'Unknown'
    
    def _analyze_sections(self, binary_path):
        """Analyze ELF sections for security implications"""
        try:
            result = subprocess.run(['readelf', '-S', binary_path], 
                                  capture_output=True, text=True)
            
            sections = []
            for line in result.stdout.split('\n'):
                if line.strip().startswith('[') and ']' in line:
                    parts = line.split()
                    if len(parts) >= 7:
                        section_name = parts[1]
                        section_flags = parts[7] if len(parts) > 7 else ''
                        sections.append({
                            'name': section_name,
                            'flags': section_flags
                        })
            
            self.results['sections'] = sections
            
            # Check for suspicious sections
            suspicious_sections = ['.init_array', '.fini_array', '.ctors', '.dtors']
            for section in sections:
                if section['name'] in suspicious_sections:
                    self.results['vulnerabilities'].append({
                        'type': 'suspicious_section',
                        'severity': 'low',
                        'description': f'Suspicious section found: {section["name"]}'
                    })
        except Exception as e:
            pass
    
    def _check_dangerous_functions(self, binary_path):
        """Check for dangerous function usage"""
        try:
            result = subprocess.run(['strings', binary_path], 
                                  capture_output=True, text=True)
            
            dangerous_functions = [
                'strcpy', 'strcat', 'sprintf', 'vsprintf',
                'gets', 'scanf', 'system', 'exec',
                'memcpy', 'memmove', 'strncpy'
            ]
            
            found_dangerous = []
            for func in dangerous_functions:
                if func in result.stdout:
                    found_dangerous.append(func)
            
            if found_dangerous:
                self.results['dangerous_functions'] = found_dangerous
                self.results['vulnerabilities'].append({
                    'type': 'dangerous_functions',
                    'severity': 'medium',
                    'description': f'Dangerous functions found: {", ".join(found_dangerous)}'
                })
        except Exception as e:
            pass
    
    def _calculate_risk_score(self):
        """Calculate overall risk score"""
        score = 0
        
        # Security features scoring (lower is worse)
        if self.results['security_features'].get('relro') == 'No':
            score += 20
        elif self.results['security_features'].get('relro') == 'Partial':
            score += 10
        
        if self.results['security_features'].get('canary') == 'No':
            score += 30
        
        if self.results['security_features'].get('nx') == 'No':
            score += 25
        
        if self.results['security_features'].get('pie') == 'No':
            score += 15
        
        # Vulnerability scoring
        for vuln in self.results['vulnerabilities']:
            if vuln['severity'] == 'high':
                score += 25
            elif vuln['severity'] == 'medium':
                score += 15
            elif vuln['severity'] == 'low':
                score += 5
        
        self.results['risk_score'] = min(score, 100)
    
    def _generate_recommendations(self):
        """Generate security recommendations"""
        recommendations = []
        
        if self.results['security_features'].get('relro') == 'No':
            recommendations.append("Enable RELRO protection (-Wl,-z,relro)")
        elif self.results['security_features'].get('relro') == 'Partial':
            recommendations.append("Enable full RELRO protection (-Wl,-z,relro,-z,now)")
        
        if self.results['security_features'].get('canary') == 'No':
            recommendations.append("Enable stack canaries (-fstack-protector-strong)")
        
        if self.results['security_features'].get('nx') == 'No':
            recommendations.append("Enable NX bit protection (-z noexecstack)")
        
        if self.results['security_features'].get('pie') == 'No':
            recommendations.append("Enable PIE (-fPIE -pie)")
        
        if self.results['security_features'].get('fortify') == 'No':
            recommendations.append("Enable FORTIFY_SOURCE (-D_FORTIFY_SOURCE=2)")
        
        if 'dangerous_functions' in self.results:
            recommendations.append("Replace dangerous functions with safer alternatives")
        
        self.results['recommendations'] = recommendations

def main():
    parser = argparse.ArgumentParser(description='Unified Binary Security Analysis')
    parser.add_argument('binary', help='Binary file to analyze')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--output', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    try:
        checksec = UnifiedChecksec()
        results = checksec.analyze_binary(args.binary)
        
        if args.json:
            output = json.dumps(results, indent=2)
        else:
            # Format for human reading
            output = f"""Binary Security Analysis: {args.binary}
{'='*50}
Architecture: {results['arch']} ({results['class']})
Endianness: {results['endian']}

Security Features:
  RELRO:          {results['security_features'].get('relro', 'Unknown')}
  Stack Canary:   {results['security_features'].get('canary', 'Unknown')}
  NX Bit:         {results['security_features'].get('nx', 'Unknown')}
  PIE:            {results['security_features'].get('pie', 'Unknown')}
  RPATH:          {results['security_features'].get('rpath', 'Unknown')}
  RUNPATH:        {results['security_features'].get('runpath', 'Unknown')}
  Symbols:        {results['security_features'].get('symbols', 'Unknown')}
  FORTIFY:        {results['security_features'].get('fortify', 'Unknown')}

Risk Score: {results['risk_score']}/100 {'(HIGH RISK)' if results['risk_score'] > 70 else '(MEDIUM RISK)' if results['risk_score'] > 40 else '(LOW RISK)'}

"""
            
            if results['vulnerabilities']:
                output += "Vulnerabilities Found:\n"
                for vuln in results['vulnerabilities']:
                    output += f"  [{vuln['severity'].upper()}] {vuln['description']}\n"
                output += "\n"
            
            if results['recommendations']:
                output += "Recommendations:\n"
                for rec in results['recommendations']:
                    output += f"  • {rec}\n"
        
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