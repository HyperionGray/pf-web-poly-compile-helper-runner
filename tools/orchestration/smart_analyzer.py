#!/usr/bin/env python3
"""
Smart Binary Analyzer
Intelligently analyzes binaries using multiple tools and techniques
"""
import sys
import os
import json
import argparse
import subprocess
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'security'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'unified'))

def run_command(cmd, timeout=30):
    """Run a command and return output. cmd should be a list of arguments."""
    try:
        # Ensure cmd is always a list to avoid shell injection
        if isinstance(cmd, str):
            # If a string is passed, split it safely
            cmd = cmd.split()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=False)
        return result.stdout if result.returncode == 0 else None
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return None

def analyze_basic(target):
    """Perform basic analysis"""
    results = {
        'target': target,
        'analysis_type': 'basic',
        'checks': []
    }
    
    # 1. File type detection
    file_output = run_command(['file', target])
    if file_output:
        results['file_type'] = file_output.strip()
        results['checks'].append({
            'name': 'File Type',
            'status': 'success',
            'result': file_output.strip()
        })
    else:
        results['checks'].append({
            'name': 'File Type',
            'status': 'failed',
            'result': 'Could not determine file type'
        })
        return results
    
    # 2. Security features analysis (using unified_checksec)
    try:
        from checksec import ChecksecAnalyzer
        analyzer = ChecksecAnalyzer()
        checksec_result = analyzer.analyze_binary(target)
        
        if 'error' not in checksec_result:
            results['security_features'] = checksec_result
            results['checks'].append({
                'name': 'Security Features',
                'status': 'success',
                'result': checksec_result
            })
        else:
            results['checks'].append({
                'name': 'Security Features',
                'status': 'failed',
                'result': checksec_result.get('error')
            })
    except Exception as e:
        results['checks'].append({
            'name': 'Security Features',
            'status': 'error',
            'result': str(e)
        })
    
    # 3. String analysis - look for interesting patterns
    strings_output = run_command(['strings', target])
    if strings_output:
        interesting_patterns = ['password', 'admin', 'flag', 'key', 'secret', 'token', 'api', 'credentials']
        interesting_strings = []
        
        for line in strings_output.split('\n'):
            line_lower = line.lower()
            if any(pattern in line_lower for pattern in interesting_patterns):
                interesting_strings.append(line.strip())
                if len(interesting_strings) >= 10:  # Limit to first 10
                    break
        
        if interesting_strings:
            results['interesting_strings'] = interesting_strings
            results['checks'].append({
                'name': 'Interesting Strings',
                'status': 'success',
                'result': f"Found {len(interesting_strings)} interesting strings"
            })
    
    # 4. Dependencies analysis (for ELF files)
    if 'ELF' in results.get('file_type', ''):
        ldd_output = run_command(['ldd', target])
        if ldd_output:
            dependencies = [line.strip() for line in ldd_output.split('\n') if '=>' in line]
            results['dependencies'] = dependencies
            results['checks'].append({
                'name': 'Dependencies',
                'status': 'success',
                'result': f"Found {len(dependencies)} dependencies"
            })
    
    return results

def analyze_deep(target):
    """Perform deep analysis with additional checks"""
    results = analyze_basic(target)
    results['analysis_type'] = 'deep'
    
    file_type = results.get('file_type', '')
    
    # Additional checks for ELF binaries
    if 'ELF' in file_type:
        # 5. Symbol table analysis
        nm_output = run_command(['nm', '-D', target])
        if nm_output:
            symbols = nm_output.split('\n')
            results['symbol_count'] = len([s for s in symbols if s.strip()])
            results['checks'].append({
                'name': 'Symbol Analysis',
                'status': 'success',
                'result': f"Found {results['symbol_count']} symbols"
            })
        
        # 6. Section analysis
        readelf_output = run_command(['readelf', '-S', target])
        if readelf_output:
            sections = [line.strip() for line in readelf_output.split('\n') if line.strip().startswith('[')]
            results['section_count'] = len(sections)
            results['checks'].append({
                'name': 'Section Analysis',
                'status': 'success',
                'result': f"Found {len(sections)} sections"
            })
        
        # 7. Function detection
        objdump_output = run_command(['objdump', '-t', target])
        if objdump_output:
            functions = [line for line in objdump_output.split('\n') if '.text' in line and ' F ' in line]
            results['function_count'] = len(functions)
            results['checks'].append({
                'name': 'Function Analysis',
                'status': 'success',
                'result': f"Detected {len(functions)} functions"
            })
    
    return results

def format_output(results, output_format='text'):
    """Format results for display"""
    if output_format == 'json':
        return json.dumps(results, indent=2)
    
    # Text format with emojis and colors
    output = "\n🧠 Smart Binary Analysis Results\n"
    output += "=" * 60 + "\n\n"
    
    output += f"📁 Target: {results['target']}\n"
    output += f"🔍 Analysis Type: {results['analysis_type'].title()}\n\n"
    
    if 'file_type' in results:
        output += f"📋 File Type: {results['file_type']}\n\n"
    
    # Security features summary
    if 'security_features' in results:
        output += "🛡️  Security Features:\n"
        features = results['security_features']
        
        def indicator(value, good_values, bad_values):
            if value in good_values:
                return "✅"
            elif value in bad_values:
                return "❌"
            else:
                return "⚠️"
        
        output += f"  {indicator(features.get('relro'), ['Full RELRO'], ['No RELRO'])} RELRO:          {features.get('relro', 'Unknown')}\n"
        output += f"  {indicator('Yes' if features.get('stack_canary') else 'No', ['Yes'], ['No'])} Stack Canary:   {'Yes' if features.get('stack_canary') else 'No'}\n"
        output += f"  {indicator('Yes' if features.get('nx') else 'No', ['Yes'], ['No'])} NX:             {'Yes' if features.get('nx') else 'No'}\n"
        output += f"  {indicator(features.get('pie'), ['PIE enabled'], ['No PIE'])} PIE:            {features.get('pie', 'Unknown')}\n"
        output += "\n"
    
    # Analysis checks summary
    output += "📊 Analysis Checks:\n"
    for check in results.get('checks', []):
        status_icon = "✅" if check['status'] == 'success' else "❌"
        output += f"  {status_icon} {check['name']}: {check['result']}\n"
    
    # Interesting strings
    if 'interesting_strings' in results and results['interesting_strings']:
        output += f"\n🔍 Interesting Strings Found:\n"
        for s in results['interesting_strings'][:5]:  # Show first 5
            output += f"  • {s}\n"
        if len(results['interesting_strings']) > 5:
            output += f"  ... and {len(results['interesting_strings']) - 5} more\n"
    
    # Deep analysis additional info
    if results.get('analysis_type') == 'deep':
        if 'symbol_count' in results:
            output += f"\n📦 Additional Details:\n"
            output += f"  • Symbols: {results.get('symbol_count', 0)}\n"
        if 'section_count' in results:
            output += f"  • Sections: {results.get('section_count', 0)}\n"
        if 'function_count' in results:
            output += f"  • Functions: {results.get('function_count', 0)}\n"
    
    # Summary
    successful_checks = len([c for c in results.get('checks', []) if c['status'] == 'success'])
    total_checks = len(results.get('checks', []))
    output += f"\n✨ Summary: {successful_checks}/{total_checks} checks completed successfully\n"
    
    return output

def main():
    parser = argparse.ArgumentParser(
        description='Smart Binary Analyzer - Intelligent analysis using multiple tools',
        epilog='Examples:\n'
               '  %(prog)s /bin/ls\n'
               '  %(prog)s --deep-analysis /usr/bin/gcc\n'
               '  %(prog)s --format json /bin/cat',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('target', help='Target binary to analyze')
    parser.add_argument('--deep-analysis', action='store_true', 
                       help='Perform deep analysis with additional checks')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='Output format (default: text)')
    parser.add_argument('--output', metavar='FILE',
                       help='Write results to file instead of stdout')
    
    args = parser.parse_args()
    
    # Check if target exists
    if not os.path.exists(args.target):
        print(f"❌ Error: Target file not found: {args.target}", file=sys.stderr)
        sys.exit(1)
    
    # Perform analysis
    if args.deep_analysis:
        results = analyze_deep(args.target)
    else:
        results = analyze_basic(args.target)
    
    # Format output
    output = format_output(results, args.format)
    
    # Write output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"✅ Analysis complete! Results written to: {args.output}")
    else:
        print(output)

if __name__ == '__main__':
    main()
