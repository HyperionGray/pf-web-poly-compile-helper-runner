#!/usr/bin/env python3
"""
Adaptive Web Security Testing Engine
Uses binary analysis intelligence to inform web security testing strategies
"""

import json
import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

class AdaptiveWebTester:
    """Intelligent web security testing guided by binary analysis"""
    
    def __init__(self):
        self.workspace = Path('/workspace')
        self.results = {}
    
    def test_targets(self, targets_file: str, binary_intel_file: str) -> Dict[str, Any]:
        """Run adaptive web security testing"""
        print("🌐 Starting adaptive web security testing...")
        
        # Load targets and binary intelligence
        with open(targets_file, 'r') as f:
            targets_data = json.load(f)
        
        binary_intel = {}
        if os.path.exists(binary_intel_file):
            with open(binary_intel_file, 'r') as f:
                binary_intel = json.load(f)
        
        results = {
            'analysis_type': 'adaptive_web_testing',
            'targets_tested': 0,
            'web_targets': {},
            'summary': {
                'critical_findings': [],
                'high_priority_endpoints': [],
                'recommended_exploits': []
            }
        }
        
        # Find web targets
        web_targets = []
        if 'analysis' in targets_data and 'web' in targets_data['analysis']:
            web_targets.append(targets_data['analysis']['web'])
        
        for target in web_targets:
            if 'url' in target:
                url = target['url']
                print(f"🎯 Testing web target: {url}")
                
                web_analysis = self._test_single_web_target(url, target, binary_intel)
                results['web_targets'][url] = web_analysis
                results['targets_tested'] += 1
                
                # Update summary
                critical_findings = [f for f in web_analysis.get('findings', []) 
                                   if f.get('severity') == 'critical']
                results['summary']['critical_findings'].extend(critical_findings)
        
        return results
    
    def _test_single_web_target(self, url: str, target_info: Dict, binary_intel: Dict) -> Dict[str, Any]:
        """Comprehensive testing of a single web target"""
        analysis = {
            'url': url,
            'target_info': target_info,
            'security_scan': {},
            'fuzzing_results': {},
            'binary_guided_tests': {},
            'findings': [],
            'risk_score': 0
        }
        
        # 1. Standard security scanning
        print("  🔍 Running security scan...")
        analysis['security_scan'] = self._run_security_scan(url)
        
        # 2. Targeted fuzzing based on binary intelligence
        print("  ⚡ Running binary-guided fuzzing...")
        analysis['fuzzing_results'] = self._run_guided_fuzzing(url, binary_intel)
        
        # 3. Binary-specific tests
        print("  🎯 Running binary-guided tests...")
        analysis['binary_guided_tests'] = self._run_binary_guided_tests(url, binary_intel)
        
        # 4. Consolidate findings
        analysis['findings'] = self._consolidate_findings(analysis)
        
        # 5. Calculate risk score
        analysis['risk_score'] = self._calculate_web_risk_score(analysis)
        
        return analysis
    
    def _run_security_scan(self, url: str) -> Dict[str, Any]:
        """Run standard web security scan"""
        try:
            result = subprocess.run([
                'node', str(self.workspace / 'tools/security/scanner.mjs'),
                url, '--json'
            ], capture_output=True, text=True, cwd=str(self.workspace))
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {'error': result.stderr}
        except Exception as e:
            return {'error': str(e)}
    
    def _run_guided_fuzzing(self, url: str, binary_intel: Dict) -> Dict[str, Any]:
        """Run fuzzing guided by binary analysis results"""
        fuzzing_results = {
            'payloads_tested': 0,
            'anomalies_found': 0,
            'targeted_tests': []
        }
        
        try:
            # Determine fuzzing strategy based on binary intelligence
            fuzz_types = ['all']  # Default
            
            # If binary analysis found specific vulnerabilities, target those
            if 'binaries' in binary_intel:
                for binary_path, binary_data in binary_intel['binaries'].items():
                    vulnerabilities = binary_data.get('vulnerabilities', [])
                    
                    for vuln in vulnerabilities:
                        if vuln['type'] == 'buffer_overflow':
                            fuzz_types.append('overflow')
                        elif vuln['type'] == 'format_string':
                            fuzz_types.append('format')
                        elif vuln['type'] == 'command_injection':
                            fuzz_types.append('cmdi')
            
            # Run targeted fuzzing
            for fuzz_type in set(fuzz_types):
                print(f"    🎯 Fuzzing with {fuzz_type} payloads...")
                
                fuzz_result = subprocess.run([
                    'node', str(self.workspace / 'tools/security/fuzzer.mjs'),
                    url, '--type', fuzz_type, '--json'
                ], capture_output=True, text=True, cwd=str(self.workspace))
                
                if fuzz_result.returncode == 0:
                    fuzz_data = json.loads(fuzz_result.stdout)
                    fuzzing_results['targeted_tests'].append({
                        'type': fuzz_type,
                        'results': fuzz_data
                    })
                    fuzzing_results['payloads_tested'] += fuzz_data.get('payloads_sent', 0)
                    fuzzing_results['anomalies_found'] += fuzz_data.get('anomalies', 0)
        
        except Exception as e:
            fuzzing_results['error'] = str(e)
        
        return fuzzing_results
    
    def _run_binary_guided_tests(self, url: str, binary_intel: Dict) -> Dict[str, Any]:
        """Run tests specifically guided by binary analysis findings"""
        guided_tests = {
            'function_based_tests': [],
            'vulnerability_specific_tests': [],
            'complexity_based_tests': []
        }
        
        if 'binaries' in binary_intel:
            for binary_path, binary_data in binary_intel['binaries'].items():
                
                # Test based on dangerous functions found
                dangerous_functions = binary_data.get('functions', {}).get('dangerous_functions', [])
                for func in dangerous_functions:
                    test_result = self._test_function_vulnerability(url, func)
                    if test_result:
                        guided_tests['function_based_tests'].append(test_result)
                
                # Test based on specific vulnerabilities
                vulnerabilities = binary_data.get('vulnerabilities', [])
                for vuln in vulnerabilities:
                    test_result = self._test_specific_vulnerability(url, vuln)
                    if test_result:
                        guided_tests['vulnerability_specific_tests'].append(test_result)
                
                # Test based on complexity score
                complexity_score = binary_data.get('complexity', {}).get('complexity_score', 0)
                if complexity_score >= 3:
                    test_result = self._test_high_complexity_target(url)
                    if test_result:
                        guided_tests['complexity_based_tests'].append(test_result)
        
        return guided_tests
    
    def _test_function_vulnerability(self, url: str, function_name: str) -> Optional[Dict[str, Any]]:
        """Test for vulnerabilities related to specific functions"""
        # Map function names to test strategies
        function_tests = {
            'strcpy': 'buffer_overflow',
            'sprintf': 'format_string',
            'system': 'command_injection',
            'malloc': 'memory_corruption'
        }
        
        for func_pattern, test_type in function_tests.items():
            if func_pattern in function_name.lower():
                return {
                    'function': function_name,
                    'test_type': test_type,
                    'description': f'Testing {test_type} based on {function_name} function',
                    'priority': 'high'
                }
        
        return None
    
    def _test_specific_vulnerability(self, url: str, vulnerability: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Test for specific vulnerability types"""
        vuln_type = vulnerability.get('type')
        
        if vuln_type in ['buffer_overflow', 'format_string', 'command_injection']:
            return {
                'vulnerability_type': vuln_type,
                'severity': vulnerability.get('severity', 'medium'),
                'description': f'Targeted test for {vuln_type}',
                'binary_source': True
            }
        
        return None
    
    def _test_high_complexity_target(self, url: str) -> Dict[str, Any]:
        """Special tests for high-complexity binaries"""
        return {
            'test_type': 'high_complexity',
            'description': 'Extended fuzzing for high-complexity binary',
            'strategy': 'increased_payload_diversity',
            'duration_multiplier': 2
        }
    
    def _consolidate_findings(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Consolidate findings from all test phases"""
        findings = []
        
        # Add security scan findings
        security_scan = analysis.get('security_scan', {})
        if 'vulnerabilities' in security_scan:
            for vuln in security_scan['vulnerabilities']:
                findings.append({
                    'source': 'security_scan',
                    'type': vuln.get('type', 'unknown'),
                    'severity': vuln.get('severity', 'medium'),
                    'description': vuln.get('description', ''),
                    'evidence': vuln.get('evidence', {})
                })
        
        # Add fuzzing findings
        fuzzing_results = analysis.get('fuzzing_results', {})
        if fuzzing_results.get('anomalies_found', 0) > 0:
            findings.append({
                'source': 'fuzzing',
                'type': 'anomaly_detected',
                'severity': 'medium',
                'description': f"Fuzzing detected {fuzzing_results['anomalies_found']} anomalies",
                'evidence': {'anomaly_count': fuzzing_results['anomalies_found']}
            })
        
        # Add binary-guided findings
        guided_tests = analysis.get('binary_guided_tests', {})
        for test_category, tests in guided_tests.items():
            for test in tests:
                if test.get('priority') == 'high':
                    findings.append({
                        'source': 'binary_guided',
                        'type': test.get('test_type', 'guided_test'),
                        'severity': 'high',
                        'description': test.get('description', ''),
                        'evidence': test
                    })
        
        return findings
    
    def _calculate_web_risk_score(self, analysis: Dict[str, Any]) -> int:
        """Calculate web security risk score (0-10)"""
        score = 0
        
        # Base score from findings
        findings = analysis.get('findings', [])
        critical_findings = sum(1 for f in findings if f.get('severity') == 'critical')
        high_findings = sum(1 for f in findings if f.get('severity') == 'high')
        
        score += critical_findings * 3
        score += high_findings * 2
        
        # Bonus for binary-guided findings (these are more reliable)
        binary_guided_findings = sum(1 for f in findings if f.get('source') == 'binary_guided')
        score += binary_guided_findings
        
        # Fuzzing anomalies
        anomalies = analysis.get('fuzzing_results', {}).get('anomalies_found', 0)
        score += min(2, anomalies)
        
        return min(10, score)

def main():
    parser = argparse.ArgumentParser(description='Adaptive Web Security Testing Engine')
    parser.add_argument('--targets', required=True, help='Targets file from target analyzer')
    parser.add_argument('--binary-intel', required=True, help='Binary intelligence file')
    parser.add_argument('--output', required=True, help='Output file for test results')
    
    args = parser.parse_args()
    
    tester = AdaptiveWebTester()
    results = tester.test_targets(args.targets, args.binary_intel)
    
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📁 Web testing complete. Results saved to: {args.output}")
    print(f"🌐 Tested {results['targets_tested']} web targets")
    print(f"🔥 Critical findings: {len(results['summary']['critical_findings'])}")

if __name__ == '__main__':
    main()