#!/usr/bin/env python3
"""
Unified Security Report Generator
Consolidates findings from all security assessment phases into comprehensive reports
"""

import json
import os
import sys
import argparse
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class UnifiedReportGenerator:
    """Generate comprehensive security assessment reports"""
    
    def __init__(self):
        self.workspace = Path('/workspace')
        self.report_data = {}
    
    def generate_report(self, input_files: List[str], output_prefix: str) -> Dict[str, Any]:
        """Generate unified security report from all analysis phases"""
        print("📊 Generating unified security report...")
        
        # Load all input data
        all_data = {}
        for input_file in input_files:
            if os.path.exists(input_file):
                with open(input_file, 'r') as f:
                    data = json.load(f)
                    all_data[input_file] = data
        
        # Consolidate findings
        consolidated_report = self._consolidate_findings(all_data)
        
        # Generate different report formats
        self._generate_json_report(consolidated_report, f"{output_prefix}.json")
        self._generate_html_report(consolidated_report, f"{output_prefix}.html")
        self._generate_exploit_templates(consolidated_report, f"{output_prefix}_exploits")
        
        return consolidated_report
    
    def _consolidate_findings(self, all_data: Dict) -> Dict[str, Any]:
        """Consolidate findings from all analysis phases"""
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'analysis_phases': list(all_data.keys()),
                'total_targets': 0,
                'assessment_duration': 0
            },
            'executive_summary': {},
            'detailed_findings': [],
            'risk_matrix': {},
            'recommendations': [],
            'exploit_opportunities': []
        }
        
        # Process each analysis phase
        for source_file, data in all_data.items():
            analysis_type = data.get('analysis_type', 'unknown')
            
            if analysis_type == 'smart_binary':
                self._process_binary_analysis(data, report)
            elif analysis_type == 'adaptive_web_testing':
                self._process_web_analysis(data, report)
            elif analysis_type == 'smart_fuzzing':
                self._process_fuzzing_analysis(data, report)
        
        # Generate executive summary
        report['executive_summary'] = self._generate_executive_summary(report)
        
        # Generate risk matrix
        report['risk_matrix'] = self._generate_risk_matrix(report)
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(report)
        
        return report
    
    def _process_binary_analysis(self, data: Dict, report: Dict):
        """Process binary analysis results"""
        binaries = data.get('binaries', {})
        
        for binary_path, binary_info in binaries.items():
            # Add detailed findings
            for vuln in binary_info.get('vulnerabilities', []):
                finding = {
                    'id': f"binary_{len(report['detailed_findings'])}",
                    'source': 'binary_analysis',
                    'target': binary_path,
                    'type': vuln['type'],
                    'severity': vuln['severity'],
                    'description': vuln['description'],
                    'risk_score': binary_info.get('risk_score', 0),
                    'evidence': {
                        'security_features': binary_info.get('security_features', {}),
                        'functions': binary_info.get('functions', {}),
                        'complexity': binary_info.get('complexity', {})
                    }
                }
                report['detailed_findings'].append(finding)
            
            # Check for exploit opportunities
            if binary_info.get('risk_score', 0) >= 7:
                exploit_opp = {
                    'target': binary_path,
                    'type': 'binary_exploitation',
                    'priority': 'high',
                    'techniques': self._suggest_exploit_techniques(binary_info),
                    'risk_score': binary_info.get('risk_score', 0)
                }
                report['exploit_opportunities'].append(exploit_opp)
    
    def _suggest_exploit_techniques(self, binary_info: Dict) -> List[str]:
        """Suggest exploit techniques based on binary analysis"""
        techniques = []
        
        security_features = binary_info.get('security_features', {})
        vulnerabilities = binary_info.get('vulnerabilities', [])
        
        # Suggest techniques based on missing protections
        if not security_features.get('NX', True):
            techniques.append('shellcode_injection')
        if not security_features.get('PIE', True):
            techniques.append('ret2libc')
        if not security_features.get('Canary', True):
            techniques.append('stack_overflow')
        
        # Suggest techniques based on vulnerabilities
        for vuln in vulnerabilities:
            if vuln['type'] == 'buffer_overflow':
                techniques.append('rop_chain')
            elif vuln['type'] == 'format_string':
                techniques.append('format_string_exploit')
            elif vuln['type'] == 'command_injection':
                techniques.append('command_injection_exploit')
        
        return list(set(techniques))  # Remove duplicates
    
    def _generate_json_report(self, report: Dict, output_file: str):
        """Generate JSON format report"""
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"📄 JSON report saved: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Unified Security Report Generator')
    parser.add_argument('--inputs', required=True, help='Comma-separated input files')
    parser.add_argument('--output', required=True, help='Output file prefix')
    
    args = parser.parse_args()
    
    input_files = args.inputs.split(',')
    
    generator = UnifiedReportGenerator()
    report = generator.generate_report(input_files, args.output)
    
    print("📊 Report generation complete!")

if __name__ == '__main__':
    main()