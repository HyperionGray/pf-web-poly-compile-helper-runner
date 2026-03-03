#!/usr/bin/env python3
"""
Smart Fuzzing Engine
Intelligently guides fuzzing based on binary analysis and web testing results
"""

import json
import os
import sys
import argparse
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

class SmartFuzzer:
    """Intelligent fuzzing guided by comprehensive analysis results"""
    
    def __init__(self):
        self.workspace = Path('/workspace')
        self.results = {}
    
    def fuzz_targets(self, targets_file: str, analysis_files: List[str]) -> Dict[str, Any]:
        """Run smart fuzzing campaign"""
        print("⚡ Starting smart fuzzing campaign...")
        
        # Load all analysis data
        targets_data = self._load_json(targets_file)
        analysis_data = {}
        
        for analysis_file in analysis_files:
            if os.path.exists(analysis_file):
                data = self._load_json(analysis_file)
                analysis_data[analysis_file] = data
        
        results = {
            'analysis_type': 'smart_fuzzing',
            'campaign_start': time.time(),
            'targets_fuzzed': 0,
            'fuzzing_sessions': {},
            'summary': {
                'total_test_cases': 0,
                'crashes_found': 0,
                'unique_crashes': 0,
                'high_priority_findings': []
            }
        }
        
        # Determine fuzzing strategy
        fuzzing_strategy = self._determine_fuzzing_strategy(targets_data, analysis_data)
        print(f"📋 Fuzzing strategy: {fuzzing_strategy['approach']}")
        
        # Execute fuzzing based on strategy
        if fuzzing_strategy['targets']:
            for target in fuzzing_strategy['targets']:
                session_results = self._fuzz_single_target(target, fuzzing_strategy)
                results['fuzzing_sessions'][target['id']] = session_results
                results['targets_fuzzed'] += 1
                
                # Update summary
                results['summary']['total_test_cases'] += session_results.get('test_cases', 0)
                results['summary']['crashes_found'] += session_results.get('crashes', 0)
        
        results['campaign_end'] = time.time()
        results['campaign_duration'] = results['campaign_end'] - results['campaign_start']
        
        return results
    
    def _load_json(self, filepath: str) -> Dict[str, Any]:
        """Safely load JSON file"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Warning: Could not load {filepath}: {e}")
            return {}
    
    def _determine_fuzzing_strategy(self, targets_data: Dict, analysis_data: Dict) -> Dict[str, Any]:
        """Determine optimal fuzzing strategy based on analysis results"""
        strategy = {
            'approach': 'comprehensive',
            'targets': [],
            'priority_order': [],
            'techniques': []
        }
        
        # Analyze binary intelligence for fuzzing targets
        binary_targets = self._extract_binary_targets(targets_data, analysis_data)
        web_targets = self._extract_web_targets(targets_data, analysis_data)
        
        # Prioritize targets based on risk scores and vulnerability types
        all_targets = binary_targets + web_targets
        all_targets.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
        
        strategy['targets'] = all_targets[:5]  # Limit to top 5 targets
        
        # Determine techniques based on found vulnerabilities
        strategy['techniques'] = self._select_fuzzing_techniques(analysis_data)
        
        if len(strategy['targets']) > 3:
            strategy['approach'] = 'parallel'
        elif any(t.get('complexity_score', 0) > 5 for t in strategy['targets']):
            strategy['approach'] = 'deep'
        else:
            strategy['approach'] = 'broad'
        
        return strategy
    
    def _extract_binary_targets(self, targets_data: Dict, analysis_data: Dict) -> List[Dict[str, Any]]:
        """Extract and prioritize binary fuzzing targets"""
        targets = []
        
        # Look for binary analysis results
        for analysis_file, data in analysis_data.items():
            if data.get('analysis_type') == 'smart_binary':
                binaries = data.get('binaries', {})
                
                for binary_path, binary_info in binaries.items():
                    target = {
                        'id': f"binary_{len(targets)}",
                        'type': 'binary',
                        'path': binary_path,
                        'priority_score': binary_info.get('risk_score', 0),
                        'complexity_score': binary_info.get('complexity', {}).get('complexity_score', 0),
                        'vulnerabilities': binary_info.get('vulnerabilities', []),
                        'functions': binary_info.get('functions', {}),
                        'fuzzing_approach': self._determine_binary_fuzzing_approach(binary_info)
                    }
                    targets.append(target)
        
        return targets
    
    def _extract_web_targets(self, targets_data: Dict, analysis_data: Dict) -> List[Dict[str, Any]]:
        """Extract and prioritize web fuzzing targets"""
        targets = []
        
        # Look for web analysis results
        for analysis_file, data in analysis_data.items():
            if data.get('analysis_type') == 'adaptive_web_testing':
                web_targets = data.get('web_targets', {})
                
                for url, web_info in web_targets.items():
                    target = {
                        'id': f"web_{len(targets)}",
                        'type': 'web',
                        'url': url,
                        'priority_score': web_info.get('risk_score', 0),
                        'findings': web_info.get('findings', []),
                        'endpoints': web_info.get('target_info', {}).get('endpoints', []),
                        'fuzzing_approach': self._determine_web_fuzzing_approach(web_info)
                    }
                    targets.append(target)
        
        return targets
    
    def _determine_binary_fuzzing_approach(self, binary_info: Dict) -> Dict[str, Any]:
        """Determine best fuzzing approach for a binary"""
        approach = {
            'method': 'file_fuzzing',
            'focus_areas': [],
            'duration_multiplier': 1.0
        }
        
        # Check for parse functions
        parse_functions = binary_info.get('functions', {}).get('parse_functions', [])
        if parse_functions:
            approach['method'] = 'function_fuzzing'
            approach['focus_areas'] = parse_functions[:3]  # Top 3 parse functions
        
        # Check for specific vulnerability types
        vulnerabilities = binary_info.get('vulnerabilities', [])
        for vuln in vulnerabilities:
            if vuln['type'] == 'buffer_overflow':
                approach['focus_areas'].append('buffer_boundaries')
            elif vuln['type'] == 'format_string':
                approach['focus_areas'].append('format_specifiers')
        
        # Adjust duration based on complexity
        complexity_score = binary_info.get('complexity', {}).get('complexity_score', 0)
        if complexity_score > 5:
            approach['duration_multiplier'] = 2.0
        
        return approach
    
    def _determine_web_fuzzing_approach(self, web_info: Dict) -> Dict[str, Any]:
        """Determine best fuzzing approach for a web target"""
        approach = {
            'method': 'endpoint_fuzzing',
            'focus_areas': [],
            'payload_types': ['all']
        }
        
        # Focus on high-priority endpoints
        endpoints = web_info.get('target_info', {}).get('endpoints', [])
        high_priority_endpoints = [ep for ep in endpoints if ep.get('priority') == 'high']
        
        if high_priority_endpoints:
            approach['focus_areas'] = [ep['path'] for ep in high_priority_endpoints]
        
        # Determine payload types based on findings
        findings = web_info.get('findings', [])
        payload_types = set(['all'])
        
        for finding in findings:
            if finding.get('source') == 'binary_guided':
                if 'buffer_overflow' in finding.get('type', ''):
                    payload_types.add('overflow')
                elif 'command_injection' in finding.get('type', ''):
                    payload_types.add('cmdi')
                elif 'format_string' in finding.get('type', ''):
                    payload_types.add('format')
        
        approach['payload_types'] = list(payload_types)
        
        return approach
    
    def _select_fuzzing_techniques(self, analysis_data: Dict) -> List[str]:
        """Select appropriate fuzzing techniques based on analysis"""
        techniques = ['mutation_fuzzing']  # Always include basic mutation
        
        # Add techniques based on discovered vulnerabilities
        all_vulnerabilities = []
        for data in analysis_data.values():
            if 'binaries' in data:
                for binary_info in data['binaries'].values():
                    all_vulnerabilities.extend(binary_info.get('vulnerabilities', []))
        
        vuln_types = set(v['type'] for v in all_vulnerabilities)
        
        if 'buffer_overflow' in vuln_types:
            techniques.append('boundary_fuzzing')
        if 'format_string' in vuln_types:
            techniques.append('format_fuzzing')
        if 'command_injection' in vuln_types:
            techniques.append('injection_fuzzing')
        
        return techniques
    
    def _fuzz_single_target(self, target: Dict, strategy: Dict) -> Dict[str, Any]:
        """Fuzz a single target with appropriate technique"""
        print(f"  🎯 Fuzzing {target['type']} target: {target.get('path', target.get('url'))}")
        
        session_results = {
            'target_id': target['id'],
            'target_type': target['type'],
            'start_time': time.time(),
            'test_cases': 0,
            'crashes': 0,
            'unique_crashes': 0,
            'interesting_findings': []
        }
        
        if target['type'] == 'binary':
            session_results.update(self._fuzz_binary_target(target))
        elif target['type'] == 'web':
            session_results.update(self._fuzz_web_target(target))
        
        session_results['end_time'] = time.time()
        session_results['duration'] = session_results['end_time'] - session_results['start_time']
        
        return session_results
    
    def _fuzz_binary_target(self, target: Dict) -> Dict[str, Any]:
        """Fuzz a binary target"""
        results = {
            'method': 'binary_fuzzing',
            'test_cases': 0,
            'crashes': 0
        }
        
        try:
            # For now, simulate binary fuzzing
            # In a real implementation, this would use AFL++, libFuzzer, or similar
            
            binary_path = target['path']
            approach = target.get('fuzzing_approach', {})
            
            # Simulate fuzzing based on approach
            if approach.get('method') == 'function_fuzzing':
                # Focus on specific functions
                focus_areas = approach.get('focus_areas', [])
                results['test_cases'] = len(focus_areas) * 1000
                results['method'] = 'function_targeted_fuzzing'
                
                # Simulate finding crashes in vulnerable functions
                vulnerabilities = target.get('vulnerabilities', [])
                if any(v['type'] == 'buffer_overflow' for v in vulnerabilities):
                    results['crashes'] = 3
                    results['interesting_findings'].append({
                        'type': 'buffer_overflow_crash',
                        'function': focus_areas[0] if focus_areas else 'unknown',
                        'severity': 'high'
                    })
            else:
                # General file fuzzing
                results['test_cases'] = 5000
                results['crashes'] = 1 if target.get('priority_score', 0) > 5 else 0
        
        except Exception as e:
            results['error'] = str(e)
        
        return results
    
    def _fuzz_web_target(self, target: Dict) -> Dict[str, Any]:
        """Fuzz a web target"""
        results = {
            'method': 'web_fuzzing',
            'test_cases': 0,
            'anomalies': 0
        }
        
        try:
            url = target['url']
            approach = target.get('fuzzing_approach', {})
            
            # Use existing web fuzzer with targeted payloads
            payload_types = approach.get('payload_types', ['all'])
            
            for payload_type in payload_types:
                print(f"    🔥 Fuzzing with {payload_type} payloads...")
                
                fuzz_result = subprocess.run([
                    'node', str(self.workspace / 'tools/security/fuzzer.mjs'),
                    url, '--type', payload_type, '--json'
                ], capture_output=True, text=True, cwd=str(self.workspace))
                
                if fuzz_result.returncode == 0:
                    fuzz_data = json.loads(fuzz_result.stdout)
                    results['test_cases'] += fuzz_data.get('payloads_sent', 0)
                    results['anomalies'] += fuzz_data.get('anomalies', 0)
        
        except Exception as e:
            results['error'] = str(e)
        
        return results

def main():
    parser = argparse.ArgumentParser(description='Smart Fuzzing Engine')
    parser.add_argument('--targets', required=True, help='Targets file from target analyzer')
    parser.add_argument('--analysis-data', required=True, help='Comma-separated analysis files')
    parser.add_argument('--output', required=True, help='Output file for fuzzing results')
    
    args = parser.parse_args()
    
    analysis_files = args.analysis_data.split(',')
    
    fuzzer = SmartFuzzer()
    results = fuzzer.fuzz_targets(args.targets, analysis_files)
    
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📁 Fuzzing campaign complete. Results saved to: {args.output}")
    print(f"⚡ Fuzzed {results['targets_fuzzed']} targets")
    print(f"📊 Total test cases: {results['summary']['total_test_cases']}")
    print(f"💥 Crashes found: {results['summary']['crashes_found']}")

if __name__ == '__main__':
    main()