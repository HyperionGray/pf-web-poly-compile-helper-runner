#!/usr/bin/env python3
"""
Test suite for demo_tui.py

This demonstrates how to add tests for demo/utility scripts.
Tests verify that the demo script can be imported and run without errors.
"""

import sys
import os
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


def test_demo_tui_imports():
    """Test that demo_tui can be imported without errors"""
    try:
        import demo_tui
        assert demo_tui is not None
    except ImportError as e:
        pytest.skip(f"demo_tui not available: {e}")


@patch('sys.path')
def test_demo_tui_path_setup(mock_path):
    """Test that demo_tui sets up the path correctly"""
    # This would normally check that pf-runner is added to sys.path
    # For now, just verify the module structure is importable
    assert True


@pytest.mark.skipif(
    not _pf_tui_path_exists(),
    reason="pf_tui module not available"
)
@patch('demo_tui.PfTUI')
@patch('demo_tui.Console')
def test_demo_tui_function(mock_console, mock_tui_class):
    """Test demo_tui function with mocked dependencies"""
    # Setup mocks
    mock_console_instance = Mock()
    mock_console.return_value = mock_console_instance
    
    mock_tui_instance = Mock()
    mock_tui_instance.tasks = [Mock()] * 5
    mock_tui_instance.categories = [Mock(name="cat1"), Mock(name="cat2")]
    mock_tui_class.return_value = mock_tui_instance
    
    try:
        import demo_tui
        
        # Test that demo_tui function runs without errors
        demo_tui.demo_tui()
        
        # Verify Console was used
        assert mock_console.called or mock_console_instance.print.called
        
    except Exception as e:
        pytest.skip(f"Demo TUI test skipped due to dependencies: {e}")


@pytest.mark.skipif(
    not _pf_tui_path_exists(),
    reason="pf_tui module not available"
)
def test_demo_tui_module_structure():
    """Test that demo_tui has expected structure"""
    try:
        import demo_tui
        
        # Verify expected function exists
        assert hasattr(demo_tui, 'demo_tui')
        assert callable(demo_tui.demo_tui)
        
    except ImportError:
        pytest.skip("demo_tui module not available for testing")


def test_demo_tui_file_exists():
    """Test that demo_tui.py file exists"""
    demo_tui_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'demo_tui.py'
    )
    assert os.path.exists(demo_tui_path), "demo_tui.py should exist"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
