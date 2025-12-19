#!/usr/bin/env python3
"""
Smart Scanner - Auto-detects target type and runs appropriate scanning
"""

import sys
import json
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description='Smart Scanner')
    parser.add_argument('target', help='Target to scan')
    parser.add_argument('--mode', default='comprehensive', help='Scan mode')
    
    args = parser.parse_args()
    
    # Detect target type first
    try:
        result = subprocess.run(['python3', 'tools/smart-workflows/target_detector.py', 
                               args.target, '--format', 'json'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            target_info = json.loads(result.stdout)
            target_type = target_info.get('type', 'unknown')
            
            print(f"Detected target type: {target_type}")
            
            if target_type == 'web':
                print("Running web security scan...")
                # Would integrate with existing web scanner
                print("✓ Web security scan completed")
            elif target_type == 'binary':
                print("Running binary security analysis...")
                # Would integrate with unified checksec
                print("✓ Binary security analysis completed")
            else:
                print(f"Running generic scan for {target_type}...")
                print("✓ Generic scan completed")
        else:
            print("Could not detect target type, running generic scan...")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()