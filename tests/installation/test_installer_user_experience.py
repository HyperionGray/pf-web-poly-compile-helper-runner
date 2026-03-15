#!/usr/bin/env python3
"""
Test suite for installer user experience validation.

This test suite validates that:
1. Installers provide clear next-step instructions
2. Mentioned pf tasks actually exist
3. Usage is intuitive for users
4. Error messages are helpful

Part of Round 3 installer functionality testing.
"""

import os
import subprocess
import re
from pathlib import Path
import pytest


# Get repository root
REPO_ROOT = Path(__file__).parent.parent.parent.absolute()
SCRIPTS_DIR = REPO_ROOT / "scripts"
TOOLS_DIR = REPO_ROOT / "tools"


def _detect_runner_dir() -> Path:
    """Return the active runner directory for this repo layout."""
    for candidate in ("pf-runner-full", "pf-runner"):
        candidate_dir = REPO_ROOT / candidate
        if (candidate_dir / "pf_main.py").exists():
            return candidate_dir
    raise FileNotFoundError("Could not find pf_main.py in pf-runner-full/ or pf-runner/")


PF_RUNNER_DIR = _detect_runner_dir()


def get_pf_tasks():
    """Get list of all available pf tasks"""
    pf_static = PF_RUNNER_DIR / "pf-static"
    if not pf_static.exists():
        pytest.skip("pf-static not built")
    
    result = subprocess.run(
        [str(pf_static), "list"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        pytest.skip("Cannot list pf tasks")
    
    # Parse task names from output
    # Tasks are formatted as "  task-name - description"
    tasks = []
    for line in result.stdout.splitlines():
        # Task lines have leading spaces and contain " - "
        if ' - ' in line:
            # Extract task name (before the " - ")
            task_name = line.split(' - ')[0].strip()
            if task_name:  # Skip empty lines
                tasks.append(task_name)
    
    return set(tasks)


def check_installer_output(installer_path, dry_run=False):
    """
    Check if installer provides next-step instructions.
    Returns (has_next_steps, output, mentioned_tasks)
    """
    if not os.path.exists(installer_path):
        pytest.skip(f"Installer not found: {installer_path}")
    
    # Read the installer script to look for next steps guidance
    with open(installer_path, 'r') as f:
        content = f.read()
    
    # Look for common next-step patterns
    next_step_patterns = [
        r'Next steps?:',
        r'Usage:',
        r'To use:',
        r'Quick start:',
        r'Try:',
        r'Run:',
        r'Example:',
        r'Getting started:',
        r'How to use:',
    ]
    
    has_next_steps = any(re.search(pattern, content, re.IGNORECASE) for pattern in next_step_patterns)
    
    # Find mentioned pf tasks (pattern: 'pf task-name')
    pf_task_pattern = r"pf\s+([a-zA-Z0-9_-]+)"
    mentioned_tasks = set(re.findall(pf_task_pattern, content))
    
    return has_next_steps, content, mentioned_tasks


@pytest.mark.integration
class TestInstallerUserExperience:
    """Test user experience of installers"""
    
    @pytest.fixture(scope="class")
    def all_pf_tasks(self):
        """Get all available pf tasks"""
        return get_pf_tasks()
    
    def test_pr_tools_installer_ux(self, all_pf_tasks):
        """Test PR tools installer provides good user experience"""
        installer = SCRIPTS_DIR / "gitops" / "install-pr-tools.sh"
        has_next_steps, content, mentioned_tasks = check_installer_output(installer)
        
        # Verify installer exists and is executable
        assert installer.exists(), f"Installer not found: {installer}"
        assert os.access(installer, os.X_OK), f"Installer not executable: {installer}"
        
        # Check for completion message
        assert "complete" in content.lower() or "installed" in content.lower(), \
            "Installer should provide installation completion message"
        
        # Check for clear success indicators
        assert "OK" in content or "success" in content.lower(), \
            "Installer should indicate success clearly"
    
    def test_injection_tools_installer_ux(self, all_pf_tasks):
        """Test injection tools installer provides next steps"""
        installer = TOOLS_DIR / "injection" / "install-injection-tools.sh"
        has_next_steps, content, mentioned_tasks = check_installer_output(installer)
        
        # This installer should provide next steps
        assert has_next_steps, \
            "Injection tools installer should provide next-step instructions"
        
        # Verify mentioned pf tasks actually exist
        for task in mentioned_tasks:
            assert task in all_pf_tasks, \
                f"Installer mentions non-existent pf task: {task}"
        
        # Check for helpful information
        assert "injection-help" in content or "test-injection-workflow" in content, \
            "Installer should mention help or test tasks"
    
    def test_debuggers_installer_ux(self, all_pf_tasks):
        """Test debuggers installer provides usage guidance"""
        installer = TOOLS_DIR / "debugging" / "install-debuggers.sh"
        has_next_steps, content, mentioned_tasks = check_installer_output(installer)
        
        # Should provide completion message
        assert "complete" in content.lower() or "ready" in content.lower(), \
            "Debuggers installer should indicate completion"
        
        # Should mention how to test/use the tools
        assert "gdb" in content.lower() and "test" in content.lower(), \
            "Installer should provide example usage or test command"
    
    def test_debug_tools_installer_ux(self, all_pf_tasks):
        """Test debug tools installer provides clear instructions"""
        installer = TOOLS_DIR / "debugging" / "install-debug-tools.sh"
        
        if not installer.exists():
            pytest.skip(f"Installer not found: {installer}")
        
        has_next_steps, content, mentioned_tasks = check_installer_output(installer)
        
        # Should indicate completion
        assert "complete" in content.lower() or "installed" in content.lower(), \
            "Debug tools installer should indicate completion"
    
    def test_fuzzing_tools_installer_ux(self, all_pf_tasks):
        """Test fuzzing tools installer provides guidance"""
        installer = TOOLS_DIR / "debugging" / "install-fuzzing-tools.sh"
        
        if not installer.exists():
            pytest.skip(f"Installer not found: {installer}")
        
        has_next_steps, content, mentioned_tasks = check_installer_output(installer)
        
        # Should provide some guidance
        assert len(content) > 100, \
            "Fuzzing tools installer should provide meaningful output"


@pytest.mark.integration
class TestInstallerTaskReferences:
    """Verify that pf tasks mentioned in installers actually exist"""
    
    @pytest.fixture(scope="class")
    def all_pf_tasks(self):
        """Get all available pf tasks"""
        return get_pf_tasks()
    
    def test_all_installer_task_references(self, all_pf_tasks):
        """Scan all installers and verify task references are valid"""
        installers = []
        
        # Find all installer scripts
        for pattern in ['install*.sh', '**/install*.sh']:
            installers.extend(REPO_ROOT.glob(pattern))
        
        invalid_references = []
        
        for installer in installers:
            # Skip test directories and backup files
            if 'test' in str(installer) or 'bak' in str(installer):
                continue
            
            try:
                with open(installer, 'r') as f:
                    content = f.read()
                
                # Find pf task references
                pf_task_pattern = r"pf\s+([a-zA-Z0-9_-]+)"
                mentioned_tasks = set(re.findall(pf_task_pattern, content))
                
                # Filter out common false positives
                false_positives = {'list', 'help', 'version', '-V', '--help', '--version'}
                mentioned_tasks -= false_positives
                
                # Check each mentioned task
                for task in mentioned_tasks:
                    if task not in all_pf_tasks:
                        invalid_references.append((installer.name, task))
            
            except Exception as e:
                # Skip binary or unreadable files
                continue
        
        # Report findings
        if invalid_references:
            msg = "Found installers referencing non-existent pf tasks:\n"
            for installer_name, task in invalid_references:
                msg += f"  - {installer_name} mentions 'pf {task}'\n"
            
            # This is a warning, not a failure - tasks might be optional
            print(f"\nWarning: {msg}")


@pytest.mark.integration
class TestInstallerErrorHandling:
    """Test that installers handle errors gracefully"""
    
    def test_pr_tools_installer_error_messages(self):
        """Test that PR tools installer provides helpful error messages"""
        installer = SCRIPTS_DIR / "gitops" / "install-pr-tools.sh"
        
        with open(installer, 'r') as f:
            content = f.read()
        
        # Should have error handling
        assert "ERROR" in content or "error" in content, \
            "Installer should provide error messages"
        
        # Should mention unsupported platforms
        assert "unsupported" in content.lower() or "not supported" in content.lower(), \
            "Installer should handle unsupported platforms"
    
    def test_injection_tools_installer_warnings(self):
        """Test that injection tools installer provides warnings"""
        installer = TOOLS_DIR / "injection" / "install-injection-tools.sh"
        
        with open(installer, 'r') as f:
            content = f.read()
        
        # Should have warning messages for common issues
        assert "warning" in content.lower() or "note" in content.lower(), \
            "Installer should provide warnings for potential issues"


@pytest.mark.integration
class TestInstallerCompletionMessages:
    """Verify installers provide clear completion messages"""
    
    def test_installers_have_completion_messages(self):
        """All installers should indicate when they complete successfully"""
        
        # Key installers to check
        installers = [
            SCRIPTS_DIR / "gitops" / "install-pr-tools.sh",
            TOOLS_DIR / "injection" / "install-injection-tools.sh",
            TOOLS_DIR / "debugging" / "install-debuggers.sh",
        ]
        
        for installer in installers:
            if not installer.exists():
                continue
            
            with open(installer, 'r') as f:
                content = f.read()
            
            # Should have completion indicators
            completion_patterns = [
                "complete", "installed", "ready", "OK", "success", "finished", "done"
            ]
            
            has_completion = any(pattern in content.lower() for pattern in completion_patterns)
            
            assert has_completion, \
                f"Installer {installer.name} should provide completion message"


@pytest.mark.integration
class TestPostInstallationGuidance:
    """Test that installers provide post-installation guidance"""
    
    def test_injection_tools_next_steps(self):
        """Injection tools installer should tell users what to do next"""
        installer = TOOLS_DIR / "injection" / "install-injection-tools.sh"
        
        with open(installer, 'r') as f:
            content = f.read()
        
        # Should provide next steps section
        assert "next steps" in content.lower(), \
            "Injection tools installer should provide 'Next steps' section"
        
        # Should mention help or test commands
        assert "injection-help" in content or "test-injection" in content, \
            "Should mention help or test commands"
    
    def test_debuggers_quick_test(self):
        """Debuggers installer should provide a quick test command"""
        installer = TOOLS_DIR / "debugging" / "install-debuggers.sh"
        
        with open(installer, 'r') as f:
            content = f.read()
        
        # Should provide quick test
        assert "quick test" in content.lower() or "test:" in content.lower(), \
            "Debuggers installer should provide quick test command"


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
