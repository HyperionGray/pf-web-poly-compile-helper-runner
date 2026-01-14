#!/usr/bin/env python3
"""
Test suite for grammar updates addressing the GitHub issue.

Tests cover:
1. Whitespace handling (already implemented via %ignore WS)
2. Blank lines support in files and task bodies
3. Variable syntax ${var} support
4. New cloud action task headers
"""

import sys
import os
import pytest

# Add pf-runner to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../pf-runner'))

try:
    from pf_lark_parser import PfLarkParser
except ImportError:
    pytest.skip("pf_lark_parser not available", allow_module_level=True)


class TestWhitespaceHandling:
    """Test that whitespace is properly ignored in parsing."""
    
    def test_leading_whitespace_in_task_body(self):
        """Test that leading spaces/tabs in task body are handled correctly."""
        content = """
task foo
  describe hi
end
"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert 'foo' in result
        assert result['foo']['description'] == 'hi'
    
    def test_mixed_indentation(self):
        """Test mixed spaces and tabs."""
        content = """
task bar
\tdescribe mixed indentation
  shell echo "hello"
end
"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert 'bar' in result
    
    def test_extra_whitespace_between_tokens(self):
        """Test extra whitespace between tokens."""
        content = """
task    test
    describe    test   task
    shell    echo    "test"
end
"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert 'test' in result


class TestBlankLines:
    """Test that blank lines are allowed where expected."""
    
    def test_empty_file_with_newlines(self):
        """Test that a file with only newlines is accepted."""
        content = "\n\n\n"
        parser = PfLarkParser()
        result = parser.parse(content)
        assert isinstance(result, dict)
    
    def test_file_with_only_comments_and_newlines(self):
        """Test file with only comments and blank lines."""
        content = """
# This is a comment

# Another comment

"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert isinstance(result, dict)
    
    def test_blank_lines_in_task_body(self):
        """Test that blank lines inside task bodies are allowed."""
        content = """
task test

  describe test with blank lines
  
  shell echo "line 1"
  
  shell echo "line 2"

end
"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert 'test' in result
        # Check that we got both shell commands
        shell_cmds = [item for item in result['test']['body'] if item and item.get('type') == 'shell']
        assert len(shell_cmds) == 2
    
    def test_blank_lines_between_tasks(self):
        """Test blank lines between task definitions."""
        content = """
task first
  describe first task
end


task second
  describe second task
end

"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert 'first' in result
        assert 'second' in result
    
    def test_leading_and_trailing_blank_lines(self):
        """Test blank lines at start and end of file."""
        content = """


task middle
  describe middle task
end


"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert 'middle' in result


class TestVariableSyntax:
    """Test that both $var and ${var} syntax work."""
    
    def test_dollar_identifier_syntax(self):
        """Test traditional $var syntax still works."""
        content = """
task test
  describe test
  if $myvar
    shell echo "var exists"
  end
end
"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert 'test' in result
    
    def test_dollar_brace_identifier_syntax(self):
        """Test new ${var} syntax."""
        content = """
task test
  describe test
  if ${myvar}
    shell echo "var exists"
  end
end
"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert 'test' in result
    
    def test_both_variable_syntaxes(self):
        """Test both syntaxes in same file."""
        content = """
task test
  describe test both syntaxes
  if $var1
    shell echo "var1 exists"
  end
  if ${var2}
    shell echo "var2 exists"
  end
end
"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert 'test' in result
    
    def test_variable_in_comparison(self):
        """Test ${var} in equality comparison."""
        content = """
task test
  describe test
  if ${environment} == "production"
    shell echo "production"
  end
end
"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert 'test' in result


class TestCloudActionHeaders:
    """Test new cloud action task header statements."""
    
    def test_timeout_statement(self):
        """Test timeout statement parsing."""
        content = """
task test
  describe test timeout
  timeout 30m
  shell echo "test"
end
"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert 'test' in result
        timeout_items = [item for item in result['test']['body'] if item and item.get('type') == 'timeout']
        assert len(timeout_items) == 1
        assert timeout_items[0]['line'] == '30m'
    
    def test_sandbox_statement(self):
        """Test sandbox statement parsing."""
        content = """
task test
  describe test sandbox
  sandbox microvm
  shell echo "test"
end
"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert 'test' in result
        sandbox_items = [item for item in result['test']['body'] if item and item.get('type') == 'sandbox']
        assert len(sandbox_items) == 1
        assert sandbox_items[0]['value'] == 'microvm'
    
    def test_network_statement(self):
        """Test network statement parsing."""
        content = """
task test
  describe test network
  network restricted
  shell echo "test"
end
"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert 'test' in result
        network_items = [item for item in result['test']['body'] if item and item.get('type') == 'network']
        assert len(network_items) == 1
        assert network_items[0]['value'] == 'restricted'
    
    def test_allowlist_statement(self):
        """Test allowlist statement parsing."""
        content = """
task test
  describe test allowlist
  network allowlist
  allowlist host=github.com host=pypi.org
  shell echo "test"
end
"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert 'test' in result
        allowlist_items = [item for item in result['test']['body'] if item and item.get('type') == 'allowlist']
        assert len(allowlist_items) == 1
        assert 'github.com' in allowlist_items[0]['line']
    
    def test_artifact_statement(self):
        """Test artifact statement parsing."""
        content = """
task test
  describe test artifacts
  artifact path/to/file.txt
  shell echo "test"
end
"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert 'test' in result
        artifact_items = [item for item in result['test']['body'] if item and item.get('type') == 'artifact']
        assert len(artifact_items) == 1
        assert 'path/to/file.txt' in artifact_items[0]['line']
    
    def test_secrets_statement(self):
        """Test secrets statement parsing."""
        content = """
task test
  describe test secrets
  secrets allow HF_TOKEN NPM_TOKEN
  shell echo "test"
end
"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert 'test' in result
        secrets_items = [item for item in result['test']['body'] if item and item.get('type') == 'secrets']
        assert len(secrets_items) == 1
        assert 'HF_TOKEN' in secrets_items[0]['line']
    
    def test_multiple_cloud_headers(self):
        """Test multiple cloud action headers in one task."""
        content = """
task deploy
  describe production deployment
  timeout 1h
  sandbox container
  network allowlist
  allowlist host=github.com host=docker.io
  artifact build/output.tar.gz
  secrets allow NPM_TOKEN GITHUB_TOKEN
  shell ./deploy.sh
end
"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert 'deploy' in result
        body = result['deploy']['body']
        
        # Filter out None items
        body = [item for item in body if item is not None]
        
        # Check we have all the headers
        assert any(item.get('type') == 'timeout' for item in body)
        assert any(item.get('type') == 'sandbox' for item in body)
        assert any(item.get('type') == 'network' for item in body)
        assert any(item.get('type') == 'allowlist' for item in body)
        assert any(item.get('type') == 'artifact' for item in body)
        assert any(item.get('type') == 'secrets' for item in body)


class TestRegressions:
    """Test that existing functionality still works."""
    
    def test_basic_task_still_works(self):
        """Ensure basic tasks parse correctly."""
        content = """
task hello
  describe Hello world
  shell echo "Hello, World!"
end
"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert 'hello' in result
    
    def test_if_statement_still_works(self):
        """Ensure if statements still work."""
        content = """
task test
  describe test if
  if $var == "value"
    shell echo "matched"
  else
    shell echo "no match"
  end
end
"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert 'test' in result
    
    def test_for_loop_still_works(self):
        """Ensure for loops still work."""
        content = """
task test
  describe test for
  for item in ["a", "b", "c"]
    shell echo "item"
  end
end
"""
        parser = PfLarkParser()
        result = parser.parse(content)
        assert 'test' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
