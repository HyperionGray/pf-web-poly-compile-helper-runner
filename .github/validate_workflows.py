#!/usr/bin/env python3
"""
Workflow validation script to check for common issues
"""
import os
import yaml
import json
from pathlib import Path

def validate_yaml_file(file_path):
    """Validate YAML syntax"""
    try:
        with open(file_path, 'r') as f:
            yaml.safe_load(f)
        return True, "Valid YAML"
    except yaml.YAMLError as e:
        return False, f"YAML Error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def check_for_nonexistent_actions(file_path):
    """Check for known-bad patterns in workflow templates."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        issues = []
        if 'github/copilot-cli-actions' in content:
            issues.append("Found non-existent action: github/copilot-cli-actions")
        if 'github/copilot-agent/' in content:
            issues.append("Found non-existent action: github/copilot-agent/*")

        # Unresolved merge conflicts break workflows and templates.
        if '<<<<<<<' in content or '>>>>>>>' in content or '=======' in content:
            issues.append("Found unresolved merge conflict markers")
            
        return len(issues) == 0, issues
    except Exception as e:
        return False, [f"Error reading file: {e}"]


def check_workflow_has_required_keys(file_path):
    """Ensure a workflow file is not an empty placeholder."""
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            return False, ["Workflow YAML root is not a mapping (empty placeholder?)"]

        # PyYAML treats `on` as boolean True in YAML 1.1, so handle both.
        has_on = ('on' in data) or (True in data)
        has_jobs = 'jobs' in data

        missing = []
        if not has_on:
            missing.append('on')
        if not has_jobs:
            missing.append('jobs')

        if missing:
            return False, [f"Missing required top-level keys: {', '.join(missing)}"]

        return True, []
    except Exception as e:
        return False, [f"Error: {e}"]

def validate_json_file(file_path):
    """Validate JSON syntax"""
    try:
        with open(file_path, 'r') as f:
            json.load(f)
        return True, "Valid JSON"
    except json.JSONDecodeError as e:
        return False, f"JSON Error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    """Main validation function"""
    print("🔍 Validating workflow files...")
    print("=" * 50)
    
    workflow_dir = Path("workflow-templates")
    issues_found = 0
    
    # Check YAML workflow files
    yaml_files = sorted(list(workflow_dir.glob("*.yml")) + list(workflow_dir.glob("*.yaml")))
    for yaml_file in yaml_files:
        print(f"\n📄 Checking {yaml_file.name}:")
        
        # Validate YAML syntax
        is_valid, message = validate_yaml_file(yaml_file)
        if is_valid:
            print(f"  ✅ YAML syntax: {message}")
        else:
            print(f"  ❌ YAML syntax: {message}")
            issues_found += 1

        # Ensure required workflow keys exist (catches empty placeholders)
        is_workflow, workflow_issues = check_workflow_has_required_keys(yaml_file)
        if is_workflow:
            print(f"  ✅ Workflow structure: OK")
        else:
            print(f"  ❌ Workflow structure issues:")
            for problem in workflow_issues:
                print(f"    - {problem}")
            issues_found += len(workflow_issues)
        
        # Check for problematic actions
        is_clean, problems = check_for_nonexistent_actions(yaml_file)
        if is_clean:
            print(f"  ✅ No problematic actions found")
        else:
            print(f"  ❌ Issues found:")
            for problem in problems:
                print(f"    - {problem}")
            issues_found += len(problems)
    
    # Check JSON property files
    for json_file in workflow_dir.glob("*.json"):
        print(f"\n📄 Checking {json_file.name}:")
        
        is_valid, message = validate_json_file(json_file)
        if is_valid:
            print(f"  ✅ JSON syntax: {message}")
        else:
            print(f"  ❌ JSON syntax: {message}")
            issues_found += 1
    
    # Check copilot instructions
    copilot_file = Path(".github/copilot-instructions.yml")
    if copilot_file.exists():
        print(f"\n📄 Checking {copilot_file}:")
        is_valid, message = validate_yaml_file(copilot_file)
        if is_valid:
            print(f"  ✅ YAML syntax: {message}")
        else:
            print(f"  ❌ YAML syntax: {message}")
            issues_found += 1
    
    print("\n" + "=" * 50)
    if issues_found == 0:
        print("🎉 All validations passed! No issues found.")
        return 0
    else:
        print(f"⚠️  Found {issues_found} issues that need attention.")
        return 1

if __name__ == "__main__":
    exit(main())
