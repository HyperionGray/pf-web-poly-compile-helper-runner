#!/usr/bin/env python3
"""
Unified Binary Security Analysis (Consolidated checksec)
Combines the best features from multiple checksec implementations
From PRs #194, #195, #196
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path

# Import the actual checksec implementation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'security'))
from checksec import ChecksecAnalyzer

def calculate_risk_score(results):
    """Calculate a risk score (0-100) based on security features"""
    if 'error' in results:
        return 100  # Maximum risk if we can't analyze
    
    risk = 0
    
    # RELRO (0-25 points of risk)
    relro = results.get('relro', 'No RELRO')
    if relro == 'No RELRO':
        risk += 25
    elif relro == 'Partial RELRO':
        risk += 10
    # Full RELRO = 0 risk
    
    # Stack Canary (0-25 points of risk)
    if not results.get('stack_canary', False):
        risk += 25
    
    # NX (0-25 points of risk)
    if not results.get('nx', False):
        risk += 25
    
    # PIE (0-20 points of risk)
    pie = results.get('pie', 'No PIE')
    if pie == 'No PIE':
        risk += 20
    elif pie == 'DSO':
        risk += 5
    
    # FORTIFY (0-5 points of risk)
    if not results.get('fortify', False):
        risk += 5
    
    return min(risk, 100)  # Cap at 100

def get_security_status(results):
    """Get human-readable security status"""
    if 'error' in results:
        return 'Error'
    
    risk = calculate_risk_score(results)
    if risk <= 20:
        return 'Secure'
    elif risk <= 50:
        return 'Moderate'
    elif risk <= 80:
        return 'Vulnerable'
    else:
        return 'Critical'

def format_unified_output(results, output_format='text'):
    """Format results in unified format"""
    if 'error' in results:
        if output_format == 'json':
            return json.dumps({'error': results['error']}, indent=2)
        return f"❌ Error: {results['error']}"
    
    # Create unified result structure
    unified_result = {
        'file': results.get('file'),
        'security_features': {
            'relro': results.get('relro', 'Unknown'),
            'canary': 'Yes' if results.get('stack_canary') else 'No',
            'nx': 'Yes' if results.get('nx') else 'No',
            'pie': results.get('pie', 'Unknown'),
            'rpath': 'Yes' if results.get('rpath') else 'No',
            'fortify': 'Yes' if results.get('fortify') else 'No'
        },
        'tool': 'unified_checksec',
        'risk_score': calculate_risk_score(results),
        'security_status': get_security_status(results)
    }
    
    if output_format == 'json':
        return json.dumps(unified_result, indent=2)
    
    # Text format with emoji indicators
    file_name = os.path.basename(unified_result['file'])
    output = f"\n🔍 Unified Security Analysis: {file_name}\n"
    output += "=" * 60 + "\n\n"
    
    output += "Security Features:\n"
    features = unified_result['security_features']
    
    # Helper for status indicators
    def indicator(value, good_values):
        if value in good_values:
            return "✅"
        elif value in ['Partial RELRO', 'DSO']:
            return "⚠️"
        else:
            return "❌"
    
    output += f"  {indicator(features['relro'], ['Full RELRO'])} RELRO:          {features['relro']}\n"
    output += f"  {indicator(features['canary'], ['Yes'])} Stack Canary:   {features['canary']}\n"
    output += f"  {indicator(features['nx'], ['Yes'])} NX (DEP):       {features['nx']}\n"
    output += f"  {indicator(features['pie'], ['PIE enabled'])} PIE (ASLR):     {features['pie']}\n"
    output += f"  {indicator(features['rpath'], ['No'])} RPATH:          {features['rpath']}\n"
    output += f"  {indicator(features['fortify'], ['Yes'])} FORTIFY:        {features['fortify']}\n"
    
    output += f"\n📊 Risk Assessment:\n"
    output += f"  Risk Score:     {unified_result['risk_score']}/100\n"
    output += f"  Status:         {unified_result['security_status']}\n"
    
    if unified_result['risk_score'] > 50:
        output += f"\n⚠️  Warning: This binary has significant security vulnerabilities!\n"
    
    return output

def main():
    parser = argparse.ArgumentParser(
        description='Unified Binary Security Analysis - Combines multiple checksec implementations',
        epilog='Examples:\n'
               '  %(prog)s /bin/ls\n'
               '  %(prog)s --json /usr/bin/gcc\n'
               '  %(prog)s --format json /bin/cat',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('binary', help='Binary file to analyze')
    parser.add_argument('--json', action='store_true', help='Output in JSON format')
    parser.add_argument('--format', choices=['json', 'text'], default='text', 
                       help='Output format (default: text)')
    parser.add_argument('--batch', action='store_true', 
                       help='Analyze multiple binaries (binary should be a directory)')
    parser.add_argument('--output', metavar='FILE', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    # Determine output format
    output_format = 'json' if (args.json or args.format == 'json') else 'text'
    
    # Create analyzer
    analyzer = ChecksecAnalyzer()
    
    # Single binary analysis
    if not args.batch:
        results = analyzer.analyze_binary(args.binary)
        output = format_unified_output(results, output_format)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"✅ Results written to: {args.output}")
        else:
            print(output)
    else:
        # Batch analysis
        if not os.path.isdir(args.binary):
            print(f"❌ Error: {args.binary} is not a directory", file=sys.stderr)
            sys.exit(1)
        
        all_results = []
        # Limit depth and only check ELF files
        for file_path in Path(args.binary).glob("*"):
            if file_path.is_file() and os.access(file_path, os.X_OK):
                # Quick ELF check before full analysis
                try:
                    with open(file_path, 'rb') as f:
                        if f.read(4) == b'\x7fELF':
                            results = analyzer.analyze_binary(str(file_path))
                            if 'error' not in results:
                                all_results.append(results)
                except Exception:
                    continue
        
        if output_format == 'json':
            # Create unified results for batch JSON output
            batch_output = {
                'directory': args.binary,
                'total_binaries': len(all_results),
                'results': []
            }
            for r in all_results:
                unified_result = {
                    'file': r.get('file'),
                    'security_features': {
                        'relro': r.get('relro', 'Unknown'),
                        'canary': 'Yes' if r.get('stack_canary') else 'No',
                        'nx': 'Yes' if r.get('nx') else 'No',
                        'pie': r.get('pie', 'Unknown'),
                        'rpath': 'Yes' if r.get('rpath') else 'No',
                        'fortify': 'Yes' if r.get('fortify') else 'No'
                    },
                    'risk_score': calculate_risk_score(r),
                    'security_status': get_security_status(r)
                }
                batch_output['results'].append(unified_result)
            output = json.dumps(batch_output, indent=2)
        else:
            output = "\n".join([format_unified_output(r, 'text') for r in all_results])
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"✅ Analyzed {len(all_results)} binaries, results written to: {args.output}")
        else:
            print(output)

if __name__ == '__main__':
    main()
