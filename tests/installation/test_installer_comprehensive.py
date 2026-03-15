#!/usr/bin/env python3
"""
Comprehensive installer test suite for pf-runner.

Tests all installation methods and verifies both installation success
and post-installation functionality.

NOTE: As of the test creation date, install.sh has known syntax errors and
missing functions. Tests for native installation are marked as xfail until
the installer is fixed. This test suite will help validate once it's repaired.
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


def _resolve_pf_runner_dir():
    """Prefer canonical runner directory, with fallback for older layouts."""
    candidates = [
        REPO_ROOT / "pf-runner-full",
        REPO_ROOT / "pf-runner",
    ]
    for candidate in candidates:
        if (candidate / "pf_main.py").exists():
            return candidate
    raise FileNotFoundError("Could not locate pf_main.py in pf-runner directories")


PF_RUNNER_DIR = _resolve_pf_runner_dir()


def _runtime_dependencies_available():
    """Whether local Python can import modules required by install-static wrapper."""
    result = subprocess.run(
        ["python3", "-c", "import lark, fabric, typer"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


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
@pytest.mark.xfail(reason="install.sh currently has syntax errors and missing functions")
class TestNativeInstall:
    """Test native installation method (install.sh)
    
    NOTE: Currently marked as xfail because install.sh has known issues:
    - Missing EOF for heredoc at line 284  
    - Missing functions: check_prerequisites, install_pf_runner, validate_installation
    - Uninitialized variable: PREFIX_SET
    
    These tests will pass once install.sh is fixed."""
    
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
    """Test lightweight source installation method (install-static.sh)"""
    
    @pytest.fixture(scope="class")
    def test_environment(self):
        """Set up test environment"""
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
        test_environment["runtime_dependencies_available"] = _runtime_dependencies_available()

    def test_static_verify_only(self, test_environment):
        """Test installer verification-only mode"""
        install_prefix = test_environment["install_prefix"]
        result = subprocess.run(
            [str(REPO_ROOT / "install-static.sh"), "--prefix", str(install_prefix), "--verify-only"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True
        )
        combined_output = f"{result.stdout}\n{result.stderr}".lower()
        if result.returncode != 0:
            # Verification can fail on clean environments missing runtime deps.
            assert "dependency missing" in combined_output or "verification checks failed" in combined_output, (
                f"Unexpected verification failure output:\n{result.stdout}\n{result.stderr}"
            )
        else:
            assert "verification checks passed" in combined_output, (
                f"Expected success message missing:\n{result.stdout}\n{result.stderr}"
            )
    
    def test_static_version(self, test_environment):
        """Test version command works"""
        if not test_environment.get("runtime_dependencies_available", False):
            pytest.skip("Skipping runtime check: lark/fabric/typer not installed")
        pf_path = test_environment["pf_executable"]
        tester = InstallerTest(test_environment["test_dir"])
        tester.pf_executable = pf_path
        assert tester.test_version()
    
    def test_static_list(self, test_environment):
        """Test list command works"""
        if not test_environment.get("runtime_dependencies_available", False):
            pytest.skip("Skipping runtime check: lark/fabric/typer not installed")
        pf_path = test_environment["pf_executable"]
        tester = InstallerTest(test_environment["test_dir"])
        tester.pf_executable = pf_path
        assert tester.test_list_tasks()
    
    def test_static_run_task(self, test_environment):
        """Test running a task works"""
        if not test_environment.get("runtime_dependencies_available", False):
            pytest.skip("Skipping runtime check: lark/fabric/typer not installed")
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


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
