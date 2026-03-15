#!/usr/bin/env python3
"""Regression coverage for installer task workflow wiring."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MAIN_PFYFILE = REPO_ROOT / "pf-files" / "Pfyfile.pf"
ALWAYS_AVAILABLE_PFYFILE = REPO_ROOT / "pf-files" / "always-available" / "Pfyfile.always-available.pf"


def _section(text: str, start_marker: str, end_marker: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[start:end]


def test_install_task_is_defined_and_discoverable():
    content = MAIN_PFYFILE.read_text(encoding="utf-8")
    assert 'task install prefix="/usr/local"' in content
    assert "pf install-prereqs" in content
    assert "pf install-post-check" in content


def test_web_toolchain_check_no_longer_contains_install_logic():
    content = MAIN_PFYFILE.read_text(encoding="utf-8")
    toolchain_section = _section(content, "task web-toolchain-check", 'task install prefix="/usr/local"')
    assert "Installing to prefix=$prefix" not in toolchain_section
    assert "dpkg -i" not in toolchain_section


def test_install_smoke_test_uses_root_discovery_helper():
    content = MAIN_PFYFILE.read_text(encoding="utf-8")
    smoke_section = _section(content, "task install-smoke-test", "task debug-check-podman")
    assert "find_root()" in smoke_section
    assert 'ROOT="${PF_ROOT:-$(find_root)}"' in smoke_section


def test_category_installation_help_lists_system_setup_entries():
    content = ALWAYS_AVAILABLE_PFYFILE.read_text(encoding="utf-8")
    section = _section(content, "task category-installation-help", "task module-install-help")
    assert "pf install-prereqs" in section
    assert "pf install-post-check" in section
    assert "pf install-smoke-test" in section
