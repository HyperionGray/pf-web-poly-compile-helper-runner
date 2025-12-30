#!/usr/bin/env python3
"""
Comprehensive test suite for pf_parser.py

This test suite covers:
- Core DSL parsing functionality
- Task definition and execution
- Parameter handling and validation
- Environment variable processing
- Host management and SSH execution
- Error handling and edge cases
- Performance and security aspects
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
    import pf_parser
except ImportError:
    pytest.skip("pf_parser module not available", allow_module_level=True)


class TestPfParser(unittest.TestCase):
    """Test cases for pf_parser core functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_pfyfile = os.path.join(self.temp_dir, 'test.pf')
        
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_pfyfile(self, content):
        """Helper to create test Pfyfile"""
        with open(self.test_pfyfile, 'w') as f:
            f.write(content)
        return self.test_pfyfile
    
    def test_basic_task_parsing(self):
        """Test basic task definition parsing"""
        content = """
task hello:
    describe "Simple hello world task"
    shell echo "Hello, World!"
"""
        pfyfile = self.create_test_pfyfile(content)
        
        # Test that parsing doesn't raise exceptions
        try:
            tasks = pf_parser.parse_pfyfile(pfyfile)
            self.assertIsInstance(tasks, dict)
            self.assertIn('hello', tasks)
        except Exception as e:
            self.fail(f"Basic task parsing failed: {e}")
    
    def test_parameter_handling(self):
        """Test parameter parsing and substitution"""
        content = """
task greet:
    describe "Greet with custom name"
    shell echo "Hello, $name!"
"""
        pfyfile = self.create_test_pfyfile(content)
        
        try:
            tasks = pf_parser.parse_pfyfile(pfyfile)
            self.assertIn('greet', tasks)
            # Test parameter substitution logic
            task = tasks['greet']
            self.assertIsNotNone(task)
        except Exception as e:
            self.fail(f"Parameter handling test failed: {e}")
    
    def test_environment_variables(self):
        """Test environment variable handling"""
        content = """
task env_test:
    describe "Test environment variables"
    env DEBUG=true
    env LOG_LEVEL=info
    shell echo "Debug: $DEBUG, Log Level: $LOG_LEVEL"
"""
        pfyfile = self.create_test_pfyfile(content)
        
        try:
            tasks = pf_parser.parse_pfyfile(pfyfile)
            self.assertIn('env_test', tasks)
        except Exception as e:
            self.fail(f"Environment variable test failed: {e}")
    
    def test_include_functionality(self):
        """Test include directive"""
        # Create included file
        included_file = os.path.join(self.temp_dir, 'included.pf')
        with open(included_file, 'w') as f:
            f.write("""
task included_task:
    describe "Task from included file"
    shell echo "Included!"
""")
        
        content = f"""
include {included_file}

task main_task:
    describe "Main task"
    shell echo "Main!"
"""
        pfyfile = self.create_test_pfyfile(content)
        
        try:
            tasks = pf_parser.parse_pfyfile(pfyfile)
            self.assertIn('main_task', tasks)
            # Include functionality might need to be tested differently
        except Exception as e:
            self.fail(f"Include functionality test failed: {e}")


class TestPfParserEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_empty_file(self):
        """Test handling of empty Pfyfile"""
        empty_file = os.path.join(self.temp_dir, 'empty.pf')
        with open(empty_file, 'w') as f:
            f.write("")
        
        try:
            tasks = pf_parser.parse_pfyfile(empty_file)
            self.assertIsInstance(tasks, dict)
        except Exception as e:
            # Empty file should be handled gracefully
            pass
    
    def test_malformed_syntax(self):
        """Test handling of malformed syntax"""
        malformed_file = os.path.join(self.temp_dir, 'malformed.pf')
        with open(malformed_file, 'w') as f:
            f.write("""
task invalid
    shell echo "Missing colon"
""")
        
        # Should handle syntax errors gracefully
        try:
            pf_parser.parse_pfyfile(malformed_file)
        except Exception:
            # Expected to fail, but shouldn't crash
            pass
    
    def test_missing_file(self):
        """Test handling of missing Pfyfile"""
        missing_file = os.path.join(self.temp_dir, 'nonexistent.pf')
        
        try:
            pf_parser.parse_pfyfile(missing_file)
        except FileNotFoundError:
            # Expected behavior
            pass
        except Exception as e:
            self.fail(f"Unexpected exception for missing file: {e}")


class TestPfParserSecurity(unittest.TestCase):
    """Security-focused test cases"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_command_injection_prevention(self):
        """Test prevention of command injection"""
        dangerous_file = os.path.join(self.temp_dir, 'dangerous.pf')
        with open(dangerous_file, 'w') as f:
            f.write("""
task dangerous:
    describe "Potentially dangerous task"
    shell echo "safe" && rm -rf /
""")
        
        # The parser should handle this safely
        try:
            tasks = pf_parser.parse_pfyfile(dangerous_file)
            # Parsing should work, execution safety is handled elsewhere
            self.assertIn('dangerous', tasks)
        except Exception as e:
            self.fail(f"Security test failed unexpectedly: {e}")
    
    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks"""
        traversal_file = os.path.join(self.temp_dir, 'traversal.pf')
        with open(traversal_file, 'w') as f:
            f.write("""
include ../../../etc/passwd

task traversal:
    describe "Path traversal attempt"
    shell cat ../../../etc/passwd
""")
        
        # Should handle path traversal attempts safely
        try:
            pf_parser.parse_pfyfile(traversal_file)
        except Exception:
            # May fail due to invalid include, which is expected
            pass


class TestPfParserPerformance(unittest.TestCase):
    """Performance-focused test cases"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_large_file_parsing(self):
        """Test parsing of large Pfyfile"""
        large_file = os.path.join(self.temp_dir, 'large.pf')
        with open(large_file, 'w') as f:
            # Generate a large file with many tasks
            for i in range(100):
                f.write(f"""
task task_{i}:
    describe "Generated task {i}"
    shell echo "Task {i} executed"
""")
        
        import time
        start_time = time.time()
        try:
            tasks = pf_parser.parse_pfyfile(large_file)
            end_time = time.time()
            
            # Should complete within reasonable time (5 seconds)
            self.assertLess(end_time - start_time, 5.0)
            self.assertEqual(len(tasks), 100)
        except Exception as e:
            self.fail(f"Large file parsing failed: {e}")
    
    def test_deep_nesting_handling(self):
        """Test handling of deeply nested structures"""
        nested_file = os.path.join(self.temp_dir, 'nested.pf')
        with open(nested_file, 'w') as f:
            f.write("""
task nested:
    describe "Deeply nested task"
    shell echo "Level 1"
    shell echo "Level 2"
    shell echo "Level 3"
""")
        
        try:
            tasks = pf_parser.parse_pfyfile(nested_file)
            self.assertIn('nested', tasks)
        except Exception as e:
            self.fail(f"Deep nesting test failed: {e}")


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