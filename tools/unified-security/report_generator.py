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
    
    def _process_web_analysis(self, data: Dict, report: Dict):
        """Process web analysis results"""
        web_targets = data.get('web_targets', {})
        
        for url, web_info in web_targets.items():
            # Add detailed findings
            for finding in web_info.get('findings', []):
                detailed_finding = {
                    'id': f"web_{len(report['detailed_findings'])}",
                    'source': 'web_analysis',
                    'target': url,
                    'type': finding['type'],
                    'severity': finding['severity'],
                    'description': finding['description'],
                    'risk_score': web_info.get('risk_score', 0),
                    'evidence': finding.get('evidence', {}),
                    'binary_guided': finding.get('source') == 'binary_guided'
                }
                report['detailed_findings'].append(detailed_finding)
            
            # Check for exploit opportunities
            if web_info.get('risk_score', 0) >= 6:
                exploit_opp = {
                    'target': url,
                    'type': 'web_exploitation',
                    'priority': 'high' if web_info.get('risk_score', 0) >= 8 else 'medium',
                    'findings': len(web_info.get('findings', [])),
                    'risk_score': web_info.get('risk_score', 0)
                }
                report['exploit_opportunities'].append(exploit_opp)
    
    def _process_fuzzing_analysis(self, data: Dict, report: Dict):
        """Process fuzzing analysis results"""
        fuzzing_sessions = data.get('fuzzing_sessions', {})
        
        for session_id, session_info in fuzzing_sessions.items():
            if session_info.get('crashes', 0) > 0:
                finding = {
                    'id': f"fuzz_{len(report['detailed_findings'])}",
                    'source': 'fuzzing',
                    'target': session_info.get('target_id', 'unknown'),
                    'type': 'crash_discovered',
                    'severity': 'high',
                    'description': f"Fuzzing discovered {session_info['crashes']} crashes",
                    'evidence': {
                        'test_cases': session_info.get('test_cases', 0),
                        'crashes': session_info.get('crashes', 0),
                        'method': session_info.get('method', 'unknown')
                    }
                }
                report['detailed_findings'].append(finding)
    
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
    
    def _generate_executive_summary(self, report: Dict) -> Dict[str, Any]:
        """Generate executive summary"""
        findings = report['detailed_findings']
        
        summary = {
            'total_findings': len(findings),
            'critical_findings': len([f for f in findings if f['severity'] == 'critical']),
            'high_findings': len([f for f in findings if f['severity'] == 'high']),
            'medium_findings': len([f for f in findings if f['severity'] == 'medium']),
            'low_findings': len([f for f in findings if f['severity'] == 'low']),
            'exploit_opportunities': len(report['exploit_opportunities']),
            'overall_risk': 'low'
        }
        
        # Determine overall risk
        if summary['critical_findings'] > 0:
            summary['overall_risk'] = 'critical'
        elif summary['high_findings'] > 2:
            summary['overall_risk'] = 'high'
        elif summary['high_findings'] > 0 or summary['medium_findings'] > 3:
            summary['overall_risk'] = 'medium'
        
        return summary
    
    def _generate_risk_matrix(self, report: Dict) -> Dict[str, Any]:
        """Generate risk matrix for prioritization"""
        findings = report['detailed_findings']
        
        risk_matrix = {
            'by_severity': {},
            'by_source': {},
            'by_target': {},
            'prioritized_list': []
        }
        
        # Group by severity
        for severity in ['critical', 'high', 'medium', 'low']:
            risk_matrix['by_severity'][severity] = [
                f for f in findings if f['severity'] == severity
            ]
        
        # Group by source
        for source in ['binary_analysis', 'web_analysis', 'fuzzing']:
            risk_matrix['by_source'][source] = [
                f for f in findings if f['source'] == source
            ]
        
        # Create prioritized list
        priority_scores = []
        for finding in findings:
            score = self._calculate_priority_score(finding)
            priority_scores.append((score, finding))
        
        priority_scores.sort(key=lambda x: x[0], reverse=True)
        risk_matrix['prioritized_list'] = [item[1] for item in priority_scores[:10]]
        
        return risk_matrix
    
    def _calculate_priority_score(self, finding: Dict) -> int:
        """Calculate priority score for finding"""
        score = 0
        
        # Base score from severity
        severity_scores = {'critical': 10, 'high': 7, 'medium': 4, 'low': 1}
        score += severity_scores.get(finding['severity'], 0)
        
        # Bonus for binary-guided findings (more reliable)
        if finding.get('binary_guided', False):
            score += 3
        
        # Bonus for fuzzing crashes (concrete evidence)
        if finding['source'] == 'fuzzing' and 'crash' in finding['type']:
            score += 5
        
        # Bonus for exploit opportunities
        if finding.get('risk_score', 0) >= 8:
            score += 2
        
        return score
    
    def _generate_recommendations(self, report: Dict) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        findings = report['detailed_findings']
        
        # Immediate actions for critical/high findings
        critical_high = [f for f in findings if f['severity'] in ['critical', 'high']]
        if critical_high:
            recommendations.append({
                'priority': 'immediate',
                'category': 'vulnerability_remediation',
                'title': 'Address Critical and High Severity Vulnerabilities',
                'description': f'Immediately address {len(critical_high)} critical/high severity findings',
                'actions': [
                    'Review and patch buffer overflow vulnerabilities',
                    'Implement input validation and sanitization',
                    'Enable security features (NX, PIE, Stack Canaries)',
                    'Conduct security code review'
                ]
            })
        
        # Security hardening recommendations
        binary_findings = [f for f in findings if f['source'] == 'binary_analysis']
        if binary_findings:
            recommendations.append({
                'priority': 'high',
                'category': 'security_hardening',
                'title': 'Implement Binary Security Hardening',
                'description': 'Enable compiler security features and hardening measures',
                'actions': [
                    'Enable stack canaries (-fstack-protector-strong)',
                    'Enable Position Independent Executables (PIE)',
                    'Enable NX bit protection',
                    'Implement RELRO (Relocation Read-Only)'
                ]
            })
        
        # Web security recommendations
        web_findings = [f for f in findings if f['source'] == 'web_analysis']
        if web_findings:
            recommendations.append({
                'priority': 'medium',
                'category': 'web_security',
                'title': 'Enhance Web Application Security',
                'description': 'Implement web security best practices',
                'actions': [
                    'Implement security headers (CSP, HSTS, etc.)',
                    'Add input validation and output encoding',
                    'Implement proper authentication and authorization',
                    'Regular security testing and code review'
                ]
            })
        
        return recommendations
    
    def _generate_json_report(self, report: Dict, output_file: str):
        """Generate JSON format report"""
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"📄 JSON report saved: {output_file}")
    
    def _generate_html_report(self, report: Dict, output_file: str):
        """Generate HTML format report"""
        html_content = self._create_html_template(report)
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        print(f"🌐 HTML report saved: {output_file}")
    
    def _create_html_template(self, report: Dict) -> str:
        """Create HTML report template"""
        exec_summary = report['executive_summary']
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Unified Security Assessment Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; }}
        .summary {{ background: #ecf0f1; padding: 15px; margin: 20px 0; }}
        .finding {{ border-left: 4px solid #e74c3c; padding: 10px; margin: 10px 0; }}
        .critical {{ border-color: #c0392b; background: #fadbd8; }}
        .high {{ border-color: #e74c3c; background: #fadbd8; }}
        .medium {{ border-color: #f39c12; background: #fdeaa7; }}
        .low {{ border-color: #27ae60; background: #d5f4e6; }}
        .recommendations {{ background: #d5f4e6; padding: 15px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ Unified Security Assessment Report</h1>
        <p>Generated: {report['metadata']['generated_at']}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Executive Summary</h2>
        <p><strong>Overall Risk Level:</strong> {exec_summary['overall_risk'].upper()}</p>
        <p><strong>Total Findings:</strong> {exec_summary['total_findings']}</p>
        <ul>
            <li>Critical: {exec_summary['critical_findings']}</li>
            <li>High: {exec_summary['high_findings']}</li>
            <li>Medium: {exec_summary['medium_findings']}</li>
            <li>Low: {exec_summary['low_findings']}</li>
        </ul>
        <p><strong>Exploit Opportunities:</strong> {exec_summary['exploit_opportunities']}</p>
    </div>
    
    <h2>🎯 Priority Findings</h2>
"""
        
        # Add priority findings
        priority_findings = report['risk_matrix']['prioritized_list'][:5]
        for finding in priority_findings:
            severity_class = finding['severity']
            html += f"""
    <div class="finding {severity_class}">
        <h3>{finding['type'].replace('_', ' ').title()} ({finding['severity'].upper()})</h3>
        <p><strong>Target:</strong> {finding['target']}</p>
        <p><strong>Source:</strong> {finding['source']}</p>
        <p>{finding['description']}</p>
    </div>
"""
        
        # Add recommendations
        html += """
    <div class="recommendations">
        <h2>💡 Recommendations</h2>
"""
        
        for rec in report['recommendations']:
            html += f"""
        <h3>{rec['title']}</h3>
        <p><strong>Priority:</strong> {rec['priority']}</p>
        <p>{rec['description']}</p>
        <ul>
"""
            for action in rec['actions']:
                html += f"            <li>{action}</li>\n"
            
            html += "        </ul>\n"
        
        html += """
    </div>
</body>
</html>
"""
        
        return html
    
    def _generate_exploit_templates(self, report: Dict, output_dir: str):
        """Generate exploit templates for high-priority findings"""
        os.makedirs(output_dir, exist_ok=True)
        
        exploit_opportunities = report['exploit_opportunities']
        
        for i, opp in enumerate(exploit_opportunities):
            if opp['priority'] == 'high':
                template_file = os.path.join(output_dir, f"exploit_{i}.py")
                template_content = self._create_exploit_template(opp)
                
                with open(template_file, 'w') as f:
                    f.write(template_content)
        
        print(f"🚀 Exploit templates saved to: {output_dir}/")
    
    def _create_exploit_template(self, opportunity: Dict) -> str:
        """Create exploit template for an opportunity"""
        template = f"""#!/usr/bin/env python3
\"\"\"
Exploit Template for {opportunity['target']}
Generated by Unified Security Assessment
Risk Score: {opportunity['risk_score']}/10
\"\"\"

import sys
import struct

# Target information
TARGET = "{opportunity['target']}"
EXPLOIT_TYPE = "{opportunity['type']}"

def main():
    print(f"🎯 Exploit template for {{TARGET}}")
    print(f"📋 Type: {{EXPLOIT_TYPE}}")
    print(f"⚠️  Risk Score: {opportunity['risk_score']}/10")
    print()
    
    # TODO: Implement specific exploit based on findings
    # Suggested techniques: {', '.join(opportunity.get('techniques', []))}
    
    print("⚠️  This is a template - implement specific exploit logic")
    print("📚 Refer to the security assessment report for details")

if __name__ == '__main__':
    main()
"""
        return template

def main():
    parser = argparse.ArgumentParser(description='Unified Security Report Generator')
    parser.add_argument('--inputs', required=True, help='Comma-separated input files')
    parser.add_argument('--output', required=True, help='Output file prefix')
    
    args = parser.parse_args()
    
    input_files = args.inputs.split(',')
    
    generator = UnifiedReportGenerator()
    report = generator.generate_report(input_files, args.output)
    
    print("📊 Report generation complete!")
    print(f"📄 Files generated:")
    print(f"  - {args.output}.json (machine readable)")
    print(f"  - {args.output}.html (human readable)")
    print(f"  - {args.output}_exploits/ (exploit templates)")

if __name__ == '__main__':
    main()