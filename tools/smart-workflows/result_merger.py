#!/usr/bin/env python3
"""
Result Merger Utility
Combines results from multiple security tools into unified reports
"""

import json
import sys
import argparse
from datetime import datetime

def merge_results(*input_files, output_file=None):
    """Merge multiple JSON result files into a unified report"""
    
    merged_results = {
        'timestamp': datetime.now().isoformat(),
        'merged_from': list(input_files),
        'summary': {},
        'detailed_results': {}
    }
    
    all_vulnerabilities = []
    all_recommendations = []
    risk_scores = []
    
    for i, input_file in enumerate(input_files):
        try:
            with open(input_file, 'r') as f:
                data = json.load(f)
            
            # Store detailed results
            merged_results['detailed_results'][f'source_{i+1}'] = {
                'file': input_file,
                'data': data
            }
            
            # Extract common fields
            if 'vulnerabilities' in data:
                all_vulnerabilities.extend(data['vulnerabilities'])
            
            if 'recommendations' in data:
                all_recommendations.extend(data['recommendations'])
            
            if 'risk_score' in data:
                risk_scores.append(data['risk_score'])
            
            # Extract analysis-specific data
            if 'security_features' in data:
                merged_results['summary']['security_features'] = data['security_features']
            
            if 'gadgets' in data:
                merged_results['summary']['rop_gadgets'] = len(data['gadgets'])
            
            if 'analysis' in data and 'rop_potential_score' in data['analysis']:
                merged_results['summary']['rop_potential'] = data['analysis']['rop_potential_score']
                
        except Exception as e:
            print(f"Warning: Could not process {input_file}: {e}")
    
    # Create unified summary
    merged_results['summary']['total_vulnerabilities'] = len(all_vulnerabilities)
    merged_results['summary']['unique_recommendations'] = len(set(all_recommendations))
    
    if risk_scores:
        merged_results['summary']['average_risk_score'] = sum(risk_scores) / len(risk_scores)
        merged_results['summary']['max_risk_score'] = max(risk_scores)
    
    # Deduplicate and categorize vulnerabilities
    vuln_by_type = {}
    for vuln in all_vulnerabilities:
        vuln_type = vuln.get('type', 'unknown')
        if vuln_type not in vuln_by_type:
            vuln_by_type[vuln_type] = []
        vuln_by_type[vuln_type].append(vuln)
    
    merged_results['summary']['vulnerabilities_by_type'] = {
        vtype: len(vulns) for vtype, vulns in vuln_by_type.items()
    }
    
    # Create consolidated recommendations
    unique_recommendations = list(set(all_recommendations))
    merged_results['summary']['consolidated_recommendations'] = unique_recommendations
    
    # Calculate overall assessment
    overall_risk = 'low'
    if merged_results['summary'].get('max_risk_score', 0) > 70:
        overall_risk = 'high'
    elif merged_results['summary'].get('max_risk_score', 0) > 40:
        overall_risk = 'medium'
    
    merged_results['summary']['overall_assessment'] = {
        'risk_level': overall_risk,
        'exploitability': 'unknown',
        'priority': 'medium'
    }
    
    # Determine exploitability
    if merged_results['summary'].get('rop_potential', 0) > 70:
        merged_results['summary']['overall_assessment']['exploitability'] = 'high'
        merged_results['summary']['overall_assessment']['priority'] = 'high'
    elif len(all_vulnerabilities) > 3:
        merged_results['summary']['overall_assessment']['exploitability'] = 'medium'
    
    # Save results
    output_json = json.dumps(merged_results, indent=2)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(output_json)
    else:
        print(output_json)
    
    return merged_results

def main():
    parser = argparse.ArgumentParser(description='Merge security analysis results')
    parser.add_argument('input_files', nargs='+', help='Input JSON files to merge')
    parser.add_argument('--output', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    try:
        merge_results(*args.input_files, output_file=args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()