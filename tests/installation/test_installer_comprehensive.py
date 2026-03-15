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
        result = self.run_command(
            [str(self.pf_executable), str(PF_RUNNER_DIR / "test.pf"), "list"],
            cwd=PF_RUNNER_DIR
        )
        assert result.returncode == 0, f"pf list failed: {result.stderr}"
        # test.pf should have 'hello' and 'vars' tasks
        assert "hello" in result.stdout.lower(), "hello task not found in list"
        return True
    
    def test_run_simple_task(self):
        """Test that pf can run a simple task"""
        result = self.run_command(
            [str(self.pf_executable), str(PF_RUNNER_DIR / "test.pf"), "hello"],
            cwd=PF_RUNNER_DIR
        )
        assert result.returncode == 0, f"pf hello task failed: {result.stderr}"
        assert "hello" in result.stdout.lower(), "Task output doesn't contain 'hello'"
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
            ["python3", str(PF_RUNNER_DIR / "pf_main.py"), "test.pf", "list"],
            cwd=PF_RUNNER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"List command failed: {result.stderr}"
        assert "hello" in result.stdout.lower(), "hello task not found"
    
    def test_direct_run_task(self):
        """Test that pf_main.py can run tasks"""
        result = subprocess.run(
            ["python3", str(PF_RUNNER_DIR / "pf_main.py"), "test.pf", "hello"],
            cwd=PF_RUNNER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Task execution failed: {result.stderr}"
    
    def test_direct_parameter_passing(self):
        """Test parameter passing in direct execution"""
        result = subprocess.run(
            ["python3", str(PF_RUNNER_DIR / "pf_main.py"), "test.pf", "vars", "name=DirectTest"],
            cwd=PF_RUNNER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Parameter passing failed: {result.stderr}"
        assert "DirectTest" in result.stdout, "Parameter not passed correctly"


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
            [str(static_exe), "test.pf", "list"],
            cwd=PF_RUNNER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"List command failed: {result.stderr}"
        assert "hello" in result.stdout.lower(), "hello task not found"
    
    def test_static_exe_run_task(self, static_exe):
        """Test that pf-static can run tasks"""
        result = subprocess.run(
            [str(static_exe), "test.pf", "hello"],
            cwd=PF_RUNNER_DIR,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Task execution failed: {result.stderr}"


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
