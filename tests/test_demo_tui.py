#!/usr/bin/env python3
"""Tests for non-interactive demo_tui script and root shim."""

from __future__ import annotations

import json
import os
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _fake_tui(load_ok: bool = True) -> Mock:
    tui = Mock()
    tui.tasks = {"build": object(), "test": object(), "deploy": object()}
    tui.categories = [
        SimpleNamespace(name="Build", tasks=[("build", "Build task")]),
        SimpleNamespace(name="Test", tasks=[("test", "Test task"), ("deploy", "")]),
    ]
    tui.load_tasks.return_value = load_ok
    tui.categorize_tasks.return_value = None
    return tui


def test_demo_tui_root_shim_exports_entrypoints():
    import demo_tui

    assert hasattr(demo_tui, "main")
    assert callable(demo_tui.main)
    assert hasattr(demo_tui, "demo_tui")
    assert callable(demo_tui.demo_tui)


def test_demo_tui_writes_json_summary(tmp_path):
    import demos.demo_tui as demo_script

    console_instance = Mock()
    fake_console_class = Mock(return_value=console_instance)
    fake_tui_instance = _fake_tui(load_ok=True)
    fake_tui_class = Mock(return_value=fake_tui_instance)
    out_path = tmp_path / "summary.json"

    with (
        patch.object(demo_script, "load_console_class", return_value=fake_console_class),
        patch.object(demo_script, "load_tui_class", return_value=fake_tui_class),
    ):
        rc = demo_script.main(["--json-out", str(out_path), "--max-categories", "1"])

    assert rc == 0
    assert out_path.exists()
    payload = json.loads(out_path.read_text())
    assert payload["task_count"] == 3
    assert payload["category_count"] == 2
    assert len(payload["categories"]) == 2


def test_demo_tui_strict_mode_fails_when_load_fails():
    import demos.demo_tui as demo_script

    fake_console_class = Mock(return_value=Mock())
    fake_tui_instance = _fake_tui(load_ok=False)
    fake_tui_class = Mock(return_value=fake_tui_instance)

    with (
        patch.object(demo_script, "load_console_class", return_value=fake_console_class),
        patch.object(demo_script, "load_tui_class", return_value=fake_tui_class),
    ):
        rc = demo_script.main(["--strict"])

    assert rc == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
