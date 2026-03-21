#!/usr/bin/env python3
"""Tests for screenshot TUI wrappers and CLI behavior."""

from __future__ import annotations

import importlib
import os
import sys
from unittest.mock import Mock, patch

# Add parent directory to import root wrappers and demos package.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_root_wrapper_exports_snapshot_function():
    """Root wrapper should expose show_menu_screenshot."""
    module = importlib.import_module("screenshot_tui")
    assert hasattr(module, "show_menu_screenshot")
    assert callable(module.show_menu_screenshot)


@patch("demos.screenshot_tui.load_tui_with_summary")
@patch("demos.screenshot_tui.load_console_class")
def test_show_menu_screenshot_uses_loaded_tui(
    mock_load_console_class, mock_load_tui_with_summary
):
    """Snapshot mode should call show_header on loaded TUI instance."""
    from demos import screenshot_tui as screenshot_module

    mock_console = Mock()
    mock_console_class = Mock(return_value=mock_console)
    mock_load_console_class.return_value = mock_console_class

    mock_tui = Mock()
    summary = {
        "total_tasks": 9,
        "category_count": 2,
        "categories": [{"name": "Core Tasks", "task_count": 3}],
    }
    mock_load_tui_with_summary.return_value = (mock_tui, summary)

    rc = screenshot_module.show_menu_screenshot(summary_json=False)
    assert rc == 0
    mock_load_tui_with_summary.assert_called_once_with(pfyfile=None, max_categories=8)
    mock_tui.show_header.assert_called_once()


@patch("demos.screenshot_tui.show_menu_screenshot")
def test_screenshot_main_parses_options(mock_show_menu_screenshot):
    """CLI options should flow into show_menu_screenshot."""
    from demos import screenshot_tui as screenshot_module

    mock_show_menu_screenshot.return_value = 0
    rc = screenshot_module.main(
        [
            "--pfyfile",
            "custom.pf",
            "--max-categories",
            "6",
            "--summary-json",
        ]
    )
    assert rc == 0
    mock_show_menu_screenshot.assert_called_once_with(
        pfyfile="custom.pf",
        max_categories=6,
        summary_json=True,
    )
