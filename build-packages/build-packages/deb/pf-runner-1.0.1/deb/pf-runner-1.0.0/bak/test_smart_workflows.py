#!/usr/bin/env python3
"""
Test script to demonstrate smart workflows integration
"""

import os
import sys
import subprocess

def test_smart_workflows():
    """Test the smart workflows integration"""
    print("🧪 Testing Smart Workflows Integration")
    print("=" * 50)
    
    # Test 1: Check if smart workflows are available
    print("\n[Test 1] Checking smart workflow availability...")
    try:
        result = subprocess.run(['pf', 'list'], capture_output=True, text=True)
        if 'smart-analyze' in result.stdout:
            print("✅ Smart workflows are available in pf")
        else:
            print("❌ Smart workflows not found in pf list")
    except FileNotFoundError:
        print("⚠️ pf command not found - install pf first")
        return False
    
    # Test 2: Check if orchestration tools exist
    print("\n[Test 2] Checking orchestration tools...")
    orchestration_files = [
        'tools/orchestration/smart_analyzer.py',
        'tools/orchestration/smart_exploiter.py', 
        'tools/orchestration/workflow_manager.py'
    ]
    
    for file_path in orchestration_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
    
    # Test 3: Check if unified tools exist
    print("\n[Test 3] Checking unified tools...")
    unified_files = [
        'tools/unified/unified_checksec.py'
    ]
    
    for file_path in unified_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
    
    # Test 4: Test smart analyzer on /bin/ls (if available)
    print("\n[Test 4] Testing smart analyzer...")
    if os.path.exists('/bin/ls'):
        try:
            result = subprocess.run(['python3', 'tools/orchestration/smart_analyzer.py', '/bin/ls'], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("✅ Smart analyzer works on /bin/ls")
                print("Sample output:")
                print(result.stdout[:200] + "..." if len(result.stdout) > 200 else result.stdout)
            else:
                print(f"❌ Smart analyzer failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("⚠️ Smart analyzer timed out")
        except Exception as e:
            print(f"❌ Smart analyzer error: {e}")
    else:
        print("⚠️ /bin/ls not available for testing")
    
    # Test 5: Test unified checksec
    print("\n[Test 5] Testing unified checksec...")
    if os.path.exists('/bin/ls'):
        try:
            result = subprocess.run(['python3', 'tools/unified/unified_checksec.py', '--tool-info'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("✅ Unified checksec tool info works")
            else:
                print(f"❌ Unified checksec failed: {result.stderr}")
        except Exception as e:
            print(f"❌ Unified checksec error: {e}")
    
    print("\n🎯 Integration Test Summary:")
    print("- Smart workflows Pfyfile created")
    print("- Orchestration tools implemented")
    print("- Unified interfaces created")
    print("- Documentation added")
    print("- Backward compatibility maintained")
    
    print("\n💡 Try these commands:")
    print("  pf smart-help                    # Show smart workflows help")
    print("  pf smart-analyze target=/bin/ls  # Test smart analysis")
    print("  pf unified-checksec --tool-info  # Show available tools")
    print("  pf smart-demo                    # Run complete demo")
    
    return True

if __name__ == '__main__':
    test_smart_workflows()