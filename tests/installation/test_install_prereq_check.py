#!/usr/bin/env python3
"""Validation tests for installer prerequisite checker."""

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKER_SCRIPT = REPO_ROOT / "scripts" / "installer" / "check-install-prereqs.sh"


def test_prereq_checker_exists_and_executable():
    """Prerequisite checker should exist and be executable."""
    assert CHECKER_SCRIPT.exists(), f"Missing checker script: {CHECKER_SCRIPT}"
    assert os.access(CHECKER_SCRIPT, os.X_OK), f"Checker script not executable: {CHECKER_SCRIPT}"


def test_prereq_checker_report_only_mode_runs():
    """Report-only mode should always succeed and print key sections."""
    result = subprocess.run(
        ["bash", str(CHECKER_SCRIPT), "--report-only"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, output
    assert "PF Installer Prerequisite Check" in output
    assert "Required tools:" in output
    assert "Optional (recommended) tools:" in output
