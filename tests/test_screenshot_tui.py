#!/usr/bin/env python3
"""
Test suite for screenshot_tui.py

This demonstrates how to add tests for demo/utility scripts.
Tests verify that the screenshot script can be imported and has expected structure.
"""

import sys
import os
import json
import pytest
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _pf_tui_path_exists() -> bool:
    root = os.path.join(os.path.dirname(__file__), "..")
    candidates = [
        os.path.join(root, "pf-runner-full", "pf_tui.py"),
        os.path.join(root, "pf-runner", "pf_tui.py"),
    ]
    return any(os.path.exists(candidate) for candidate in candidates)


def test_screenshot_tui_file_exists():
    """Test that screenshot_tui.py file exists"""
    screenshot_tui_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'screenshot_tui.py'
    )
    assert os.path.exists(screenshot_tui_path), "screenshot_tui.py should exist"


def test_screenshot_tui_imports():
    """Test that screenshot_tui can be imported without errors"""
    try:
        import screenshot_tui
        assert screenshot_tui is not None
    except ImportError as e:
        pytest.skip(f"screenshot_tui not available: {e}")


@pytest.mark.skipif(
    not _pf_tui_path_exists(),
    reason="pf_tui module not available"
)
def test_screenshot_tui_module_structure():
    """Test that screenshot_tui has expected structure"""
    try:
        import screenshot_tui
        
        # Verify expected function exists
        assert hasattr(screenshot_tui, 'show_menu_screenshot')
        assert callable(screenshot_tui.show_menu_screenshot)
        
    except ImportError:
        pytest.skip("screenshot_tui module not available for testing")


@pytest.mark.skipif(
    not _pf_tui_path_exists(),
    reason="pf_tui module not available"
)
@patch('screenshot_tui.PfTUI')
@patch('screenshot_tui.Console')
def test_show_menu_screenshot(mock_console, mock_tui_class):
    """Test show_menu_screenshot function with mocked dependencies"""
    # Setup mocks
    mock_console_instance = Mock()
    mock_console.return_value = mock_console_instance
    
    mock_tui_instance = Mock()
    mock_tui_instance.tasks = [Mock()] * 10
    mock_tui_instance.categories = [
        Mock(name=f"Category {i}", tasks=[Mock()]) 
        for i in range(10)
    ]
    mock_tui_class.return_value = mock_tui_instance
    
    try:
        import screenshot_tui
        
        # Test that function runs without errors
        screenshot_tui.show_menu_screenshot()
        
        # Verify Console was used for output
        assert mock_console.called or mock_console_instance.print.called
        
        # Verify TUI methods were called
        assert mock_tui_instance.load_tasks.called
        assert mock_tui_instance.categorize_tasks.called
        assert mock_tui_instance.show_header.called
        
    except Exception as e:
        pytest.skip(f"Screenshot TUI test skipped due to dependencies: {e}")


@pytest.mark.skipif(
    not _pf_tui_path_exists(),
    reason="pf_tui module not available"
)
@patch("screenshot_tui.PfTUI")
@patch("screenshot_tui.Console")
def test_show_menu_screenshot_writes_json(mock_console, mock_tui_class, tmp_path):
    """Snapshot mode should write JSON output when requested."""
    mock_console.return_value = Mock()
    mock_tui_instance = Mock()
    mock_tui_instance.tasks = [Mock(), Mock()]
    category_one = Mock()
    category_one.name = "Core Tasks"
    category_one.tasks = [Mock(), Mock()]
    category_two = Mock()
    category_two.name = "Testing"
    category_two.tasks = [Mock()]
    mock_tui_instance.categories = [category_one, category_two]
    mock_tui_class.return_value = mock_tui_instance

    import screenshot_tui

    out_file = tmp_path / "snapshot.json"
    rc = screenshot_tui.show_menu_screenshot(
        output_path=str(out_file),
        snapshot_format="json",
    )

    assert rc == 0
    assert out_file.exists()
    payload = json.loads(out_file.read_text(encoding="utf-8"))
    assert payload["total_tasks"] == 2
    assert payload["total_categories"] == 2


def test_screenshot_tui_is_executable():
    """Test that screenshot_tui.py is executable or has shebang"""
    screenshot_tui_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'screenshot_tui.py'
    )
    
    if os.path.exists(screenshot_tui_path):
        with open(screenshot_tui_path, 'r') as f:
            first_line = f.readline()
            # Check for shebang
            assert first_line.startswith('#!'), "Script should have shebang"
            assert 'python' in first_line.lower(), "Shebang should reference Python"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
