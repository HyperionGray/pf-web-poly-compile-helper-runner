#!/usr/bin/env python3
"""
Comprehensive installer test suite for pf-runner.

Tests all installation methods and verifies both installation success
and post-installation functionality.
"""

import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
import pytest


# Get repository root
REPO_ROOT = Path(__file__).parent.parent.parent.absolute()
PF_RUNNER_DIR = REPO_ROOT / "pf-runner-full"
SAFE_TASK_CANDIDATES = [
    "category-help",
    "install-help",
    "always-available-help",
    "smart-help",
    "debug-help",
    "pkg-help",
    "os-help",
    "git-help",
]


def extract_task_names(list_output):
    """Extract task names from `pf list` output."""
    tasks = []
    for line in list_output.splitlines():
        stripped = line.strip()
        if not stripped or stripped.endswith("tasks:"):
            continue
        if " - " not in stripped:
            continue
        task_name = stripped.split(" - ", 1)[0].strip()
        if task_name:
            tasks.append(task_name)
    return tasks


def select_safe_task(task_names):
    """Select a non-destructive task suitable for smoke execution."""
    for candidate in SAFE_TASK_CANDIDATES:
        if candidate in task_names:
            return candidate
    return None


class InstallerTest:
    """Base class for installer tests"""
    
    def __init__(self, test_dir):
        self.test_dir = Path(test_dir)
        self.pf_executable = None
    
    def run_command(self, cmd, cwd=None, capture_output=True, check=True):
        """Run a shell command and return result"""
        if isinstance(cmd, str):
            cmd = cmd.split()
        
        result = subprocess.run(
            cmd,
            cwd=cwd or REPO_ROOT,
            capture_output=capture_output,
            text=True,
            check=check
        )
        return result
    
    def test_version(self):
        """Test that pf --version works"""
        assert self.pf_executable is not None, "pf executable not set"
        assert os.path.exists(self.pf_executable), f"pf not found at {self.pf_executable}"
        
        result = self.run_command([str(self.pf_executable), "-V"])
        assert result.returncode == 0, f"pf -V failed: {result.stderr}"
        assert "pf" in result.stdout.lower(), "Version output doesn't contain 'pf'"
        return True
    
    def test_list_tasks(self):
        """Test that pf can list tasks"""
        result = self.run_command([str(self.pf_executable), "list"], cwd=PF_RUNNER_DIR)
        assert result.returncode == 0, f"pf list failed: {result.stderr}"
        assert "available tasks" in result.stdout.lower(), "Task list header not found"
        return True
    
    def test_run_simple_task(self):
        """Test that pf can run a simple built-in task"""
        list_result = self.run_command([str(self.pf_executable), "list"], cwd=PF_RUNNER_DIR)
        tasks = extract_task_names(list_result.stdout)
        task = select_safe_task(tasks)
        assert task is not None, "No safe smoke task found in `pf list` output"

        result = self.run_command([str(self.pf_executable), "run", task], cwd=PF_RUNNER_DIR)
        assert result.returncode == 0, f"pf run {task} failed: {result.stderr}"
        return True


@pytest.mark.integration
class TestNativeInstall:
    """Test native installation method (install.sh)."""
    
    @pytest.fixture(scope="class")
    def test_environment(self):
        """Set up test environment"""
        test_dir = tempfile.mkdtemp(prefix="pf-test-native-")
        install_prefix = Path(test_dir) / "install"
        
        yield {
            "test_dir": test_dir,
            "install_prefix": install_prefix,
        }
        
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)
    
    def test_install_native(self, test_environment):
        """Test that native installation succeeds"""
        install_prefix = test_environment["install_prefix"]
        
        # Run installer
        result = subprocess.run(
            [str(REPO_ROOT / "install.sh"), "--prefix", str(install_prefix), "--skip-deps"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Installation failed: {result.stderr}"
        
        # Check that pf executable exists
        pf_path = install_prefix / "bin" / "pf"
        assert pf_path.exists(), f"pf executable not found at {pf_path}"
        assert os.access(pf_path, os.X_OK), "pf is not executable"


@pytest.mark.integration
class TestStaticInstall:
    """Test static executable installation method (install-static.sh)"""
    
    @pytest.fixture(scope="class")
    def test_environment(self):
        """Set up test environment"""
        # First check if static executable exists
        static_exe = PF_RUNNER_DIR / "pf-static"
        if not static_exe.exists():
            pytest.skip("Static executable not built (pf-static not found)")
        
        test_dir = tempfile.mkdtemp(prefix="pf-test-static-")
        install_prefix = Path(test_dir) / "install"
        
        yield {
            "test_dir": test_dir,
            "install_prefix": install_prefix,
        }
        
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)
    
    def test_install_static(self, test_environment):
        """Test that static installation succeeds"""
        install_prefix = test_environment["install_prefix"]
        
        # Run installer
        result = subprocess.run(
            [str(REPO_ROOT / "install-static.sh"), "--prefix", str(install_prefix)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Installation failed: {result.stderr}"
        
        # Check that pf executable exists
        pf_path = install_prefix / "bin" / "pf"
        assert pf_path.exists(), f"pf executable not found at {pf_path}"
        assert os.access(pf_path, os.X_OK), "pf is not executable"
        
        # Store for other tests
        test_environment["pf_executable"] = pf_path
    
    def test_static_version(self, test_environment):
        """Test version command works"""
        pf_path = test_environment["pf_executable"]
        tester = InstallerTest(test_environment["test_dir"])
        tester.pf_executable = pf_path
        assert tester.test_version()
    
    def test_static_list(self, test_environment):
        """Test list command works"""
        pf_path = test_environment["pf_executable"]
        tester = InstallerTest(test_environment["test_dir"])
        tester.pf_executable = pf_path
        assert tester.test_list_tasks()
    
    def test_static_run_task(self, test_environment):
        """Test running a task works"""
        pf_path = test_environment["pf_executable"]
        tester = InstallerTest(test_environment["test_dir"])
        tester.pf_executable = pf_path
        assert tester.test_run_simple_task()


@pytest.mark.integration
class TestDirectExecution:
    """Test direct execution of pf_main.py"""
    
    def test_direct_version(self):
        """Test that pf_main.py -V works"""
        result = subprocess.run(
            ["python3", str(PF_RUNNER_DIR / "pf_main.py"), "-V"],
            cwd=PF_RUNNER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Direct execution failed: {result.stderr}"
        assert "pf" in result.stdout.lower(), "Version output doesn't contain 'pf'"
    
    def test_direct_list(self):
        """Test that pf_main.py can list tasks"""
        result = subprocess.run(
            ["python3", str(PF_RUNNER_DIR / "pf_main.py"), "list"],
            cwd=PF_RUNNER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"List command failed: {result.stderr}"
        assert "available tasks" in result.stdout.lower(), "Task list header not found"
    
    def test_direct_run_task(self):
        """Test that pf_main.py can run tasks"""
        list_result = subprocess.run(
            ["python3", str(PF_RUNNER_DIR / "pf_main.py"), "list"],
            cwd=PF_RUNNER_DIR,
            capture_output=True,
            text=True
        )
        assert list_result.returncode == 0, f"List command failed: {list_result.stderr}"
        task = select_safe_task(extract_task_names(list_result.stdout))
        assert task is not None, "No safe smoke task found in `pf list` output"

        result = subprocess.run(
            ["python3", str(PF_RUNNER_DIR / "pf_main.py"), "run", task],
            cwd=PF_RUNNER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Task execution failed: {result.stderr}"
    
    def test_direct_parameter_passing(self):
        """Test task help lookup in direct execution"""
        list_result = subprocess.run(
            ["python3", str(PF_RUNNER_DIR / "pf_main.py"), "list"],
            cwd=PF_RUNNER_DIR,
            capture_output=True,
            text=True
        )
        assert list_result.returncode == 0, f"List command failed: {list_result.stderr}"
        task = select_safe_task(extract_task_names(list_result.stdout))
        assert task is not None, "No safe smoke task found in `pf list` output"

        result = subprocess.run(
            ["python3", str(PF_RUNNER_DIR / "pf_main.py"), "help", task],
            cwd=PF_RUNNER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Task help lookup failed: {result.stderr}"
        assert task in result.stdout.lower(), "Task help output missing task name"


@pytest.mark.integration  
class TestStaticExecutable:
    """Test static executable directly (if it exists)"""
    
    @pytest.fixture(scope="class")
    def static_exe(self):
        """Get static executable path"""
        static_path = PF_RUNNER_DIR / "pf-static"
        if not static_path.exists():
            pytest.skip("Static executable not built")
        return static_path
    
    def test_static_exe_version(self, static_exe):
        """Test that pf-static -V works"""
        result = subprocess.run(
            [str(static_exe), "-V"],
            cwd=PF_RUNNER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Static executable failed: {result.stderr}"
        assert "pf" in result.stdout.lower(), "Version output doesn't contain 'pf'"
    
    def test_static_exe_list(self, static_exe):
        """Test that pf-static can list tasks"""
        result = subprocess.run(
            [str(static_exe), "list"],
            cwd=PF_RUNNER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"List command failed: {result.stderr}"
        assert "available tasks" in result.stdout.lower(), "Task list header not found"
    
    def test_static_exe_run_task(self, static_exe):
        """Test that pf-static can run tasks"""
        list_result = subprocess.run(
            [str(static_exe), "list"],
            cwd=PF_RUNNER_DIR,
            capture_output=True,
            text=True
        )
        assert list_result.returncode == 0, f"List command failed: {list_result.stderr}"
        task = select_safe_task(extract_task_names(list_result.stdout))
        assert task is not None, "No safe smoke task found in `pf list` output"

        result = subprocess.run(
            [str(static_exe), "run", task],
            cwd=PF_RUNNER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Task execution failed: {result.stderr}"


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
