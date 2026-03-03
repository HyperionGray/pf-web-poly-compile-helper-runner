#!/usr/bin/env python3

"""
Test script to verify smart workflow integration
Checks that new tasks are properly defined and accessible
"""

import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return success status and output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def test_pf_available():
    """Test if pf command is available"""
    print("🔍 Testing pf availability...")
    success, stdout, stderr = run_command("pf --version")
    if success:
        print("✅ pf command is available")
        return True
    else:
        print("❌ pf command not found")
        print(f"Error: {stderr}")
        return False

def test_smart_tasks_defined():
    """Test if smart workflow tasks are properly defined"""
    print("\n🔍 Testing smart workflow task definitions...")
    
    smart_tasks = [
        'smart-detect-tools',
        'smart-binary-analysis', 
        'smart-web-security',
        'autopwn',
        'autoweb',
        'autokernel',
        'smart-full-stack'
    ]
    
    success, stdout, stderr = run_command("pf list")
    if not success:
        print("❌ Failed to list pf tasks")
        return False
    
    found_tasks = []
    missing_tasks = []
    
    for task in smart_tasks:
        if task in stdout:
            found_tasks.append(task)
            print(f"✅ Found task: {task}")
        else:
            missing_tasks.append(task)
            print(f"❌ Missing task: {task}")
    
    print(f"\n📊 Task Summary: {len(found_tasks)}/{len(smart_tasks)} enhanced tasks found")
    
    return len(missing_tasks) == 0

def test_orchestration_tools():
    """Test if orchestration tools exist"""
    print("\n🔍 Testing orchestration tools...")
    
    tools = [
        'tools/orchestration/tool-detector.mjs',
        'tools/orchestration/workflow-engine.mjs', 
        'tools/orchestration/output-normalizer.py'
    ]
    
    all_exist = True
    for tool in tools:
        if os.path.exists(tool):
            print(f"✅ Found: {tool}")
        else:
            print(f"❌ Missing: {tool}")
            all_exist = False
    
    return all_exist

def test_pfyfiles_included():
    """Test if new Pfyfiles are properly included"""
    print("\n🔍 Testing Pfyfile inclusions...")
    
    main_pfyfile = "Pfyfile.pf"
    if not os.path.exists(main_pfyfile):
        print(f"❌ Main Pfyfile not found: {main_pfyfile}")
        return False
    
    with open(main_pfyfile, 'r') as f:
        content = f.read()
    
    required_includes = [
        'Pfyfile.smart-workflows.pf',
        'Pfyfile.enhanced-integration.pf'
    ]
    
    all_included = True
    for include in required_includes:
        if include in content:
            print(f"✅ Found include: {include}")
        else:
            print(f"❌ Missing include: {include}")
            all_included = False
    
    return all_included

def test_aliases_work():
    """Test if quick aliases are working"""
    print("\n🔍 Testing quick aliases...")
    
    aliases = ['apwn', 'aweb', 'akernel', 'stools']
    
    success, stdout, stderr = run_command("pf list")
    if not success:
        print("❌ Failed to list tasks for alias testing")
        return False
    
    found_aliases = []
    for alias in aliases:
        if f"[alias {alias}]" in stdout or alias in stdout:
            found_aliases.append(alias)
            print(f"✅ Found alias: {alias}")
        else:
            print(f"❌ Missing alias: {alias}")
    
    print(f"📊 Alias Summary: {len(found_aliases)}/{len(aliases)} aliases found")
    return len(found_aliases) > 0  # At least some aliases should work

def main():
    """Run all integration tests"""
    print("🚀 Enhanced Workflow Integration Test")
    print("=" * 50)
    
    tests = [
        ("pf Command Available", test_pf_available),
        ("Enhanced Tasks Defined", test_smart_tasks_defined), 
        ("Orchestration Tools", test_orchestration_tools),
        ("Pfyfile Inclusions", test_pfyfiles_included),
        ("Quick Aliases", test_aliases_work)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 INTEGRATION TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Smart workflow integration is working correctly.")
        print("\n🚀 Try these commands to see the integration in action:")
        print("   pf stools                    # Detect available tools")
        print("   pf autopwn binary=./test     # Complete binary exploitation")
        print("   pf autoweb url=http://...    # Complete web security assessment")
        print("   pf smart-full-stack target=. # Auto-detecting analysis")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        print("\n🔧 Common fixes:")
        print("   - Run: ./install.sh --runtime podman")
        print("   - Or native install: sudo ./install.sh --mode native")
        print("   - Check that all Pfyfiles are in the correct location")
        print("   - Verify Node.js is installed for orchestration tools")
        return 1

if __name__ == "__main__":
    sys.exit(main())
