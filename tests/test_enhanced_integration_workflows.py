#!/usr/bin/env python3
"""Regression tests for enhanced smart integration task files."""

from pathlib import Path


TASK_FILES = [
    Path("pf-files/enhanced-tasks/Pfyfile.enhanced-integration.pf"),
    Path("pf/Pfyfile.enhanced-integration.pf"),
    Path("pf/enhanced-tasks/Pfyfile.enhanced-integration.pf"),
]


EXPECTED_ALIAS_TASKS = [
    "task autopwn [alias apwn]",
    "task autoweb [alias aweb]",
    "task autokernel [alias akernel]",
    "task smart-binary-complete [alias sbc]",
    "task smart-web-complete [alias swc]",
    "task smart-full-stack [alias sfs]",
    "task smart-exploit-chain [alias sec]",
]


def test_no_placeholder_stubs_in_enhanced_integration_files():
    for path in TASK_FILES:
        content = path.read_text(encoding="utf-8")
        assert "Not yet implemented" not in content, f"Placeholder stub remains in {path}"


def test_alias_tasks_are_defined_on_real_workflows():
    for path in TASK_FILES:
        content = path.read_text(encoding="utf-8")
        for task_def in EXPECTED_ALIAS_TASKS:
            assert task_def in content, f"Missing alias-enabled task '{task_def}' in {path}"


def test_smart_exploit_chain_uses_supported_shellcode_task():
    for path in TASK_FILES:
        content = path.read_text(encoding="utf-8")
        assert "pf pwn-shellcode" in content, f"smart-exploit-chain must call pwn-shellcode in {path}"
        assert "pf generate-shellcode" not in content, f"Deprecated shellcode task call still present in {path}"
