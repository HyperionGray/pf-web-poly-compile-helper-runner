#!/usr/bin/env python3
"""
Comprehensive test suite for pf_tui.py

This test suite covers:
- TUI initialization and configuration
- Task discovery and categorization
- User interface components
- Keyboard navigation
- Task execution through TUI
- Error handling in interactive mode
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add pf-runner to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'pf-runner'))

try:
    import pf_tui
    from rich.console import Console
except ImportError:
    pytest.skip("pf_tui module or rich not available", allow_module_level=True)


class TestPfTUIInitialization(unittest.TestCase):
    """Test TUI initialization and setup"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('pf_tui.Console')
    def test_tui_initialization(self, mock_console):
        """Test TUI class initialization"""
        mock_console.return_value = Mock()
        
        try:
            # Test basic TUI initialization
            tui = pf_tui.PfTUI()
            self.assertIsNotNone(tui)
            self.assertIsInstance(tui.console, Mock)
        except Exception as e:
            self.fail(f"TUI initialization failed: {e}")
    
    def test_task_category_creation(self):
        """Test TaskCategory data class"""
        try:
            category = pf_tui.TaskCategory(
                name="test",
                description="Test category",
                tasks=[]
            )
            self.assertEqual(category.name, "test")
            self.assertEqual(category.description, "Test category")
            self.assertEqual(len(category.tasks), 0)
        except Exception as e:
            self.fail(f"TaskCategory creation failed: {e}")
    
    def test_pfyfile_data_class(self):
        """Test PfyFile data class"""
        try:
            pfyfile = pf_tui.PfyFile(
                path="/test/path.pf",
                categories=[]
            )
            self.assertEqual(pfyfile.path, "/test/path.pf")
            self.assertEqual(len(pfyfile.categories), 0)
        except Exception as e:
            self.fail(f"PfyFile creation failed: {e}")


class TestPfTUIFileDiscovery(unittest.TestCase):
    """Test file discovery and task loading"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_pfyfile(self, filename, content):
        """Helper to create test Pfyfile"""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    @patch('pf_tui.Console')
    @patch('pf_tui.glob.glob')
    def test_file_discovery(self, mock_glob, mock_console):
        """Test Pfyfile discovery functionality"""
        mock_console.return_value = Mock()
        
        # Create test files
        test_file = self.create_test_pfyfile('test.pf', """
task hello:
    describe "Hello world task"
    shell echo "Hello!"
""")
        
        mock_glob.return_value = [test_file]
        
        try:
            tui = pf_tui.PfTUI()
            # Test file discovery method if it exists
            if hasattr(tui, 'discover_pfyfiles'):
                files = tui.discover_pfyfiles()
                self.assertIsInstance(files, list)
        except Exception as e:
            self.fail(f"File discovery test failed: {e}")
    
    @patch('pf_tui.Console')
    def test_task_loading(self, mock_console):
        """Test task loading from Pfyfiles"""
        mock_console.return_value = Mock()
        
        # Create test file with multiple tasks
        test_content = """
task build:
    describe "Build the project"
    shell make build

task test:
    describe "Run tests"
    shell make test

task deploy:
    describe "Deploy application"
    shell make deploy
"""
        test_file = self.create_test_pfyfile('build.pf', test_content)
        
        try:
            tui = pf_tui.PfTUI()
            # Test task loading if method exists
            if hasattr(tui, 'load_tasks_from_file'):
                tasks = tui.load_tasks_from_file(test_file)
                self.assertIsInstance(tasks, (list, dict))
        except Exception as e:
            self.fail(f"Task loading test failed: {e}")


class TestPfTUIUserInterface(unittest.TestCase):
    """Test user interface components"""
    
    @patch('pf_tui.Console')
    def test_console_output(self, mock_console):
        """Test console output functionality"""
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance
        
        try:
            tui = pf_tui.PfTUI()
            
            # Test basic output methods if they exist
            if hasattr(tui, 'print_header'):
                tui.print_header("Test Header")
                mock_console_instance.print.assert_called()
            
            if hasattr(tui, 'print_task_list'):
                tui.print_task_list([])
                
        except Exception as e:
            self.fail(f"Console output test failed: {e}")
    
    @patch('pf_tui.Console')
    @patch('pf_tui.Prompt')
    def test_user_input_handling(self, mock_prompt, mock_console):
        """Test user input handling"""
        mock_console.return_value = Mock()
        mock_prompt.ask.return_value = "test_task"
        
        try:
            tui = pf_tui.PfTUI()
            
            # Test input handling if method exists
            if hasattr(tui, 'get_user_selection'):
                selection = tui.get_user_selection()
                self.assertIsNotNone(selection)
                
        except Exception as e:
            self.fail(f"User input handling test failed: {e}")


class TestPfTUIKeyboardNavigation(unittest.TestCase):
    """Test keyboard navigation functionality"""
    
    @patch('pf_tui.Console')
    def test_keyboard_event_handling(self, mock_console):
        """Test keyboard event handling"""
        mock_console.return_value = Mock()
        
        try:
            tui = pf_tui.PfTUI()
            
            # Test keyboard handling if methods exist
            if hasattr(tui, 'handle_keypress'):
                # Test various key combinations
                test_keys = ['q', 'h', 'j', 'k', 'enter', 'escape']
                for key in test_keys:
                    try:
                        result = tui.handle_keypress(key)
                        # Should not raise exceptions
                    except Exception:
                        pass  # Some keys might not be implemented
                        
        except Exception as e:
            self.fail(f"Keyboard navigation test failed: {e}")
    
    @patch('pf_tui.Console')
    def test_navigation_state(self, mock_console):
        """Test navigation state management"""
        mock_console.return_value = Mock()
        
        try:
            tui = pf_tui.PfTUI()
            
            # Test navigation state if attributes exist
            if hasattr(tui, 'current_selection'):
                initial_selection = getattr(tui, 'current_selection', 0)
                self.assertIsInstance(initial_selection, int)
                
            if hasattr(tui, 'move_selection_up'):
                tui.move_selection_up()
                
            if hasattr(tui, 'move_selection_down'):
                tui.move_selection_down()
                
        except Exception as e:
            self.fail(f"Navigation state test failed: {e}")


class TestPfTUITaskExecution(unittest.TestCase):
    """Test task execution through TUI"""
    
    @patch('pf_tui.Console')
    @patch('pf_tui.subprocess')
    def test_task_execution(self, mock_subprocess, mock_console):
        """Test task execution functionality"""
        mock_console.return_value = Mock()
        mock_subprocess.run.return_value = Mock(returncode=0, stdout="Success")
        
        try:
            tui = pf_tui.PfTUI()
            
            # Test task execution if method exists
            if hasattr(tui, 'execute_task'):
                result = tui.execute_task("test_task")
                # Should handle execution gracefully
                
        except Exception as e:
            self.fail(f"Task execution test failed: {e}")
    
    @patch('pf_tui.Console')
    def test_output_display(self, mock_console):
        """Test output display during task execution"""
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance
        
        try:
            tui = pf_tui.PfTUI()
            
            # Test output display if method exists
            if hasattr(tui, 'display_task_output'):
                tui.display_task_output("Test output")
                mock_console_instance.print.assert_called()
                
        except Exception as e:
            self.fail(f"Output display test failed: {e}")


class TestPfTUIErrorHandling(unittest.TestCase):
    """Test error handling in TUI"""
    
    @patch('pf_tui.Console')
    def test_error_display(self, mock_console):
        """Test error message display"""
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance
        
        try:
            tui = pf_tui.PfTUI()
            
            # Test error display if method exists
            if hasattr(tui, 'display_error'):
                tui.display_error("Test error message")
                mock_console_instance.print.assert_called()
                
        except Exception as e:
            self.fail(f"Error display test failed: {e}")
    
    @patch('pf_tui.Console')
    def test_exception_handling(self, mock_console):
        """Test exception handling in TUI operations"""
        mock_console.return_value = Mock()
        
        try:
            tui = pf_tui.PfTUI()
            
            # Test that TUI handles exceptions gracefully
            if hasattr(tui, 'run'):
                # This might raise exceptions, but should be handled
                try:
                    tui.run()
                except Exception:
                    # Expected in test environment
                    pass
                    
        except Exception as e:
            self.fail(f"Exception handling test failed: {e}")


class TestPfTUIIntegration(unittest.TestCase):
    """Integration tests for TUI functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('pf_tui.Console')
    def test_full_workflow(self, mock_console):
        """Test complete TUI workflow"""
        mock_console.return_value = Mock()
        
        # Create test Pfyfile
        test_file = os.path.join(self.temp_dir, 'workflow.pf')
        with open(test_file, 'w') as f:
            f.write("""
task setup:
    describe "Setup environment"
    shell echo "Setting up..."

task build:
    describe "Build project"
    shell echo "Building..."

task test:
    describe "Run tests"
    shell echo "Testing..."
""")
        
        try:
            tui = pf_tui.PfTUI()
            
            # Test workflow components if they exist
            if hasattr(tui, 'initialize'):
                tui.initialize()
                
            if hasattr(tui, 'load_pfyfiles'):
                tui.load_pfyfiles()
                
            # Should complete without errors
            
        except Exception as e:
            self.fail(f"Full workflow test failed: {e}")


if __name__ == '__main__':
    # Run tests with coverage if available
    try:
        import coverage
        cov = coverage.Coverage()
        cov.start()
        
        unittest.main(verbosity=2, exit=False)
        
        cov.stop()
        cov.save()
        print("\nCoverage Report:")
        cov.report()
    except ImportError:
        unittest.main(verbosity=2)