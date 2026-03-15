#!/usr/bin/env python3
"""Tests for installer entrypoint scripts."""

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER = REPO_ROOT / "install.sh"
QUICK_INSTALLER = REPO_ROOT / "quick-install.sh"


def run_installer(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(INSTALLER), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_install_help_mentions_check_mode() -> None:
    result = run_installer("--help")
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0
    assert "--check" in output


def test_install_check_mode_reports_ready(tmp_path: Path) -> None:
    prefix = tmp_path / "pf-prefix"
    result = run_installer("--check", "--skip-deps", "--prefix", str(prefix))
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, output
    assert "Preflight checks passed" in output


def test_top_level_wrappers_exist_and_are_executable() -> None:
    assert INSTALLER.exists()
    assert QUICK_INSTALLER.exists()
    assert os.access(INSTALLER, os.X_OK)
    assert os.access(QUICK_INSTALLER, os.X_OK)
