#!/usr/bin/env python3
"""Integrity checks for installer-related pf task definitions."""

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[2]
MAIN_PFYFILE = REPO_ROOT / "pf-files" / "Pfyfile.pf"


def _read_main_pfyfile() -> str:
    return MAIN_PFYFILE.read_text(encoding="utf-8")


def test_core_install_tasks_exist():
    """Main Pfyfile should expose core install entrypoints."""
    content = _read_main_pfyfile()
    task_names = set(re.findall(r"^task\s+([a-zA-Z0-9_-]+)", content, flags=re.MULTILINE))

    assert "install" in task_names, "Missing 'install' task in pf-files/Pfyfile.pf"
    assert (
        "install-prereq-check" in task_names
    ), "Missing 'install-prereq-check' task in pf-files/Pfyfile.pf"


def test_install_help_references_prereq_check():
    """Install help should advertise the prereq check workflow."""
    content = _read_main_pfyfile()
    assert "pf install-prereq-check" in content
    assert "pf install-smoke-test" in content


def test_web_toolchain_check_no_longer_contains_install_logic():
    """Install logic should not be embedded in web-toolchain-check task."""
    content = _read_main_pfyfile()
    match = re.search(
        r"task web-toolchain-check.*?\nend\n",
        content,
        flags=re.DOTALL,
    )
    assert match, "Could not locate web-toolchain-check task block"
    block = match.group(0)

    # These strings belong to the install task and must stay out of web toolchain checks.
    assert "Installing to prefix=" not in block
    assert "canonical installer not found" not in block
