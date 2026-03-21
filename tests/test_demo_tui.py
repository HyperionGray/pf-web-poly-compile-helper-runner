#!/usr/bin/env python3
"""Tests for demo TUI wrappers and summary mode."""

from __future__ import annotations

import importlib
import json
import os
import sys
from unittest.mock import Mock, patch

# Add parent directory to import root wrappers and demos package.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_root_wrapper_exports_demo_function():
    """Root wrapper should expose demo_tui for compatibility."""
    module = importlib.import_module("demo_tui")
    assert hasattr(module, "demo_tui")
    assert callable(module.demo_tui)


@patch("demos.demo_tui.load_tui_with_summary")
@patch("demos.demo_tui.load_console_class")
def test_demo_tui_summary_json_mode(mock_load_console_class, mock_load_tui_with_summary):
    """JSON mode should print structured summary content."""
    from demos import demo_tui as demo_module

    mock_console = Mock()
    mock_console_class = Mock(return_value=mock_console)
    mock_load_console_class.return_value = mock_console_class

    mock_tui = Mock()
    summary = {
        "total_tasks": 11,
        "category_count": 3,
        "categories": [{"name": "Core Tasks", "task_count": 4}],
    }
    mock_load_tui_with_summary.return_value = (mock_tui, summary)

    rc = demo_module.demo_tui(summary_json=True)
    assert rc == 0
    mock_load_tui_with_summary.assert_called_once_with(pfyfile=None, max_categories=8)

    assert mock_console.print.called
    printed = mock_console.print.call_args_list[-1].args[0]
    parsed = json.loads(printed)
    assert parsed["total_tasks"] == 11
    assert parsed["category_count"] == 3


@patch("demos.demo_tui.demo_tui")
def test_demo_tui_main_parses_options(mock_demo_tui):
    """CLI options should flow into demo_tui entrypoint."""
    from demos import demo_tui as demo_module

    mock_demo_tui.return_value = 0
    rc = demo_module.main(
        [
            "--pfyfile",
            "custom.pf",
            "--max-categories",
            "5",
            "--summary-json",
        ]
    )
    assert rc == 0
    mock_demo_tui.assert_called_once_with(
        pfyfile="custom.pf",
        max_categories=5,
        summary_json=True,
    )
