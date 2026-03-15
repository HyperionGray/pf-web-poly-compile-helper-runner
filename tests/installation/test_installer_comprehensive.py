#!/usr/bin/env python3
"""Installer test suite for current pf-runner layout."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent.parent.absolute()
PF_RUNNER_DIR = REPO_ROOT / "pf-runner-full"
INSTALLER = REPO_ROOT / "install-static.sh"


def run_command(cmd, cwd=None):
    """Run command with captured text output."""
    return subprocess.run(
        cmd,
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def assert_pf_basics(pf_executable: Path):
    """Validate version/list/task execution on test fixture."""
    assert pf_executable.exists(), f"Missing executable: {pf_executable}"
    assert os.access(pf_executable, os.X_OK), f"Not executable: {pf_executable}"

    version = run_command([str(pf_executable), "-V"])
    assert version.returncode == 0, f"pf -V failed: {version.stderr}"
    assert "pf" in version.stdout.lower(), "Version output missing 'pf'"

    list_result = run_command(
        [str(pf_executable), str(PF_RUNNER_DIR / "test.pf"), "list"],
        cwd=PF_RUNNER_DIR,
    )
    assert list_result.returncode == 0, f"pf list failed: {list_result.stderr}"
    assert "hello" in list_result.stdout.lower(), "hello task not found"

    hello_result = run_command(
        [str(pf_executable), str(PF_RUNNER_DIR / "test.pf"), "hello"],
        cwd=PF_RUNNER_DIR,
    )
    assert hello_result.returncode == 0, f"pf hello failed: {hello_result.stderr}"


@pytest.mark.integration
class TestDirectExecution:
    """Direct pf_main.py execution from source tree."""

    def test_direct_version(self):
        result = run_command(["python3", str(PF_RUNNER_DIR / "pf_main.py"), "-V"], cwd=PF_RUNNER_DIR)
        assert result.returncode == 0, f"Direct execution failed: {result.stderr}"
        assert "pf" in result.stdout.lower(), "Version output missing 'pf'"

    def test_direct_list(self):
        result = run_command(
            ["python3", str(PF_RUNNER_DIR / "pf_main.py"), "test.pf", "list"],
            cwd=PF_RUNNER_DIR,
        )
        assert result.returncode == 0, f"List failed: {result.stderr}"
        assert "hello" in result.stdout.lower(), "hello task not found"

    def test_direct_run_task(self):
        result = run_command(
            ["python3", str(PF_RUNNER_DIR / "pf_main.py"), "test.pf", "hello"],
            cwd=PF_RUNNER_DIR,
        )
        assert result.returncode == 0, f"Task execution failed: {result.stderr}"


@pytest.mark.integration
class TestPythonModeInstall:
    """Validate Python-mode installer output layout."""

    @pytest.fixture(scope="class")
    def install_prefix(self):
        test_dir = Path(tempfile.mkdtemp(prefix="pf-test-python-install-"))
        prefix = test_dir / "install"
        yield prefix
        shutil.rmtree(test_dir, ignore_errors=True)

    def test_install_python_mode(self, install_prefix):
        result = run_command(
            [str(INSTALLER), "--mode", "python", "--prefix", str(install_prefix)],
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"Python-mode install failed: {result.stderr}"

        pf_path = install_prefix / "bin" / "pf"
        lib_dir = install_prefix / "lib" / "pf-runner"
        assert pf_path.exists(), f"Missing installed executable: {pf_path}"
        assert os.access(pf_path, os.X_OK), "Installed pf wrapper is not executable"
        assert (lib_dir / "pf_main.py").exists(), "pf_main.py missing from installed runtime"
        assert (lib_dir / "pf.lark").exists(), "pf.lark missing from installed runtime"
        assert (lib_dir / "pf-files").exists(), "pf-files directory missing from installed runtime"


@pytest.mark.integration
class TestStaticModeInstall:
    """Validate static installer mode and resulting binary."""

    @pytest.fixture(scope="class")
    def static_binary(self):
        static_exe = PF_RUNNER_DIR / "pf-static"
        if not static_exe.exists():
            pytest.skip("Static executable not built (pf-runner-full/pf-static missing)")
        return static_exe

    @pytest.fixture(scope="class")
    def install_prefix(self, static_binary):
        test_dir = Path(tempfile.mkdtemp(prefix="pf-test-static-install-"))
        prefix = test_dir / "install"
        yield prefix
        shutil.rmtree(test_dir, ignore_errors=True)

    def test_install_static_mode(self, install_prefix):
        result = run_command(
            [str(INSTALLER), "--mode", "static", "--prefix", str(install_prefix), "--verify"],
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, f"Static install failed: {result.stderr}"

        pf_path = install_prefix / "bin" / "pf"
        assert_pf_basics(pf_path)


@pytest.mark.integration
class TestStaticExecutable:
    """Exercise static executable directly when present."""

    @pytest.fixture(scope="class")
    def static_exe(self):
        static_path = PF_RUNNER_DIR / "pf-static"
        if not static_path.exists():
            pytest.skip("Static executable not built")
        return static_path

    def test_static_exe_basics(self, static_exe):
        assert_pf_basics(static_exe)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
