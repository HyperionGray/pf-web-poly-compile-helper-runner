
#!/usr/bin/env python3
"""
Validation script for the Copilot Issue Reconciler workflow.
Checks syntax, structure, and compliance with repository patterns.
"""

import yaml
import os
import sys
from pathlib import Path

def validate_workflow():
    """Validate the copilot-issue-reconciler.yml workflow file."""
    
    workflow_path = Path(".github/workflows/copilot-issue-reconciler.yml")
    
    if not workflow_path.exists():
        print("❌ Workflow file not found at .github/workflows/copilot-issue-reconciler.yml")
        return False
    
    print("✅ Workflow file exists")
    
    try:
        with open(workflow_path, 'r') as f:
            workflow = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"❌ YAML syntax error: {e}")
        return False
    
    print("✅ YAML syntax is valid")
    
    # Check required top-level keys
    required_keys = ['name', 'on', 'jobs']
    for key in required_keys:
        if key not in workflow:
            print(f"❌ Missing required key: {key}")
            return False
    
    print("✅ Required top-level keys present")
    
    # Check triggers
    triggers = workflow['on']
    if 'schedule' not in triggers:
        print("❌ Missing schedule trigger")
        return False
    
    if 'workflow_dispatch' not in triggers:
        print("❌ Missing workflow_dispatch trigger")
        return False
    
    print("✅ Required triggers present")
    
    # Check cron schedule
    schedule = triggers['schedule']
    if not isinstance(schedule, list) or len(schedule) == 0:
        print("❌ Schedule must be a non-empty list")
        return False
    
    cron_expr = schedule[0].get('cron')
    if not cron_expr:
        print("❌ Missing cron expression")
        return False
    
    if cron_expr != '*/5 * * * *':
        print(f"⚠️  Cron expression is '{cron_expr}', expected '*/5 * * * *' for 5-minute intervals")
    else:
        print("✅ Cron schedule is correct (every 5 minutes)")
    
    # Check workflow_dispatch inputs
    dispatch_inputs = triggers['workflow_dispatch'].get('inputs', {})
    expected_inputs = ['dry_run', 'max_issues']
    for input_name in expected_inputs:
        if input_name not in dispatch_inputs:
            print(f"⚠️  Missing workflow_dispatch input: {input_name}")
        else:
            print(f"✅ Workflow input '{input_name}' present")
    
    # Check permissions
    permissions = workflow.get('permissions', {})
    required_permissions = {'issues': 'write', 'contents': 'read'}
    for perm, level in required_permissions.items():
        if permissions.get(perm) != level:
            print(f"❌ Missing or incorrect permission: {perm} should be '{level}'")
            return False
    
    print("✅ Permissions are correct")
    
    # Check jobs
    jobs = workflow['jobs']
    if 'reconcile-copilot-issues' not in jobs:
        print("❌ Missing expected job: reconcile-copilot-issues")
        return False
    
    job = jobs['reconcile-copilot-issues']
    
    # Check job structure
    if job.get('runs-on') != 'ubuntu-latest':
        print("❌ Job should run on ubuntu-latest")
        return False
    
    print("✅ Job configuration is correct")
    
    # Check steps
    steps = job.get('steps', [])
    if len(steps) == 0:
        print("❌ Job has no steps")
        return False
    
    main_step = steps[0]
    if main_step.get('uses') != 'actions/github-script@main':
        print("❌ Main step should use actions/github-script@main")
        return False
    
    print("✅ Main step uses correct action")
    
    # Check script content
    script_content = main_step.get('with', {}).get('script', '')
    
    # Check for required variables and patterns
    required_patterns = [
        'copilotUsername',
        'allowedModels',
        'defaultModel',
        'copilot-gpt-5.1-codex',
        'copilot-gpt-5.1',
        'copilot-claude-4.5-opus',
        'github.paginate',
        'addAssignees',
        'addLabels',
        'dryRun'
    ]
    
    for pattern in required_patterns:
        if pattern not in script_content:
            print(f"⚠️  Script may be missing required pattern: {pattern}")
        else:
            print(f"✅ Script contains required pattern: {pattern}")
    
    print("\n🎉 Workflow validation completed!")
    return True

def check_repository_structure():
    """Check if the repository structure is as expected."""
    
    print("\n📁 Checking repository structure...")
    
    # Check for .github/workflows directory
    workflows_dir = Path(".github/workflows")
    if not workflows_dir.exists():
        print("❌ .github/workflows directory not found")
        return False
    
    print("✅ .github/workflows directory exists")
    
    # Check for existing workflow files
    existing_workflows = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
    print(f"📋 Found {len(existing_workflows)} existing workflow files:")
    for workflow in existing_workflows:
        print(f"   - {workflow.name}")
    
    # Check for workflow templates
    templates_dir = Path("workflow-templates")
    if templates_dir.exists():
        template_files = list(templates_dir.glob("*.yml")) + list(templates_dir.glob("*.yaml"))
        print(f"📋 Found {len(template_files)} workflow template files:")
        for template in template_files:
            print(f"   - {template.name}")
    
    return True

def main():
    """Main validation function."""
    
    print("🔍 Validating Copilot Issue Reconciler Workflow")
    print("=" * 50)
    
    # Change to the workspace directory if we're not already there
    if os.path.exists("/workspace"):
        os.chdir("/workspace")
    
    # Check repository structure
    if not check_repository_structure():
        sys.exit(1)
    
    # Validate the workflow
    if not validate_workflow():
        print("\n❌ Workflow validation failed!")
        sys.exit(1)
    
    print("\n✅ All validations passed!")
    print("\n📝 Next steps:")
    print("1. Commit the workflow file to enable it")
    print("2. Test with a manual workflow_dispatch run in dry-run mode")
    print("3. Monitor the scheduled runs every 5 minutes")
    print("4. Check logs for any issues or errors")

if __name__ == "__main__":
    main()
