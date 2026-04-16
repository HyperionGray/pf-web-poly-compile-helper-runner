#!/usr/bin/env python3
"""
Extended unit tests for pf_shell.py

Covers edge cases and scenarios not addressed by existing
test_shell_command_parsing.py:
- parse_shell_command: empty input, env-only lines, complex quoting
- _has_shell_metacharacters: comprehensive operator coverage
- validate_shell_syntax: valid/invalid env var names, empty commands
- build_shell_command: sudo wrapping, env merging
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pf-runner-full"))

import pytest

try:
    from pf_shell import (
        parse_shell_command,
        _has_shell_metacharacters,
        validate_shell_syntax,
        build_shell_command,
    )
    from pf_exceptions import PFExecutionError
except ImportError:
    pytest.skip("pf_shell module not available", allow_module_level=True)


# ---------------------------------------------------------------------------
# parse_shell_command
# ---------------------------------------------------------------------------

class TestParseShellCommand(unittest.TestCase):

    def test_simple_command(self):
        env, cmd = parse_shell_command("echo hello")
        self.assertEqual(env, {})
        self.assertIn("echo", cmd)

    def test_env_prefix(self):
        env, cmd = parse_shell_command("FOO=bar baz")
        self.assertEqual(env, {"FOO": "bar"})
        self.assertIn("baz", cmd)

    def test_multiple_env_vars(self):
        env, cmd = parse_shell_command("A=1 B=2 cmd arg")
        self.assertEqual(env, {"A": "1", "B": "2"})
        self.assertIn("cmd", cmd)

    def test_env_only_returns_empty_command(self):
        env, cmd = parse_shell_command("ONLY=value")
        self.assertEqual(env, {"ONLY": "value"})
        self.assertEqual(cmd, "")

    def test_flag_with_equals_not_treated_as_env(self):
        env, cmd = parse_shell_command("--foo=bar cmd")
        self.assertEqual(env, {})
        self.assertIn("--foo=bar", cmd)

    def test_preserves_dollar_in_command(self):
        env, cmd = parse_shell_command("echo $HOME")
        self.assertIn("$HOME", cmd)

    def test_unclosed_quote_raises(self):
        with self.assertRaises(PFExecutionError):
            parse_shell_command('echo "unclosed')


# ---------------------------------------------------------------------------
# _has_shell_metacharacters
# ---------------------------------------------------------------------------

class TestHasShellMetacharacters(unittest.TestCase):

    def test_plain_command(self):
        self.assertFalse(_has_shell_metacharacters("echo hello"))

    def test_pipe(self):
        self.assertTrue(_has_shell_metacharacters("ls | grep foo"))

    def test_redirect(self):
        self.assertTrue(_has_shell_metacharacters("echo hi > out.txt"))

    def test_ampersand(self):
        self.assertTrue(_has_shell_metacharacters("sleep 1 &"))

    def test_double_ampersand(self):
        self.assertTrue(_has_shell_metacharacters("a && b"))

    def test_dollar_expansion(self):
        self.assertTrue(_has_shell_metacharacters("echo $VAR"))

    def test_backtick(self):
        self.assertTrue(_has_shell_metacharacters("echo `date`"))

    def test_glob_star(self):
        self.assertTrue(_has_shell_metacharacters("ls *.py"))

    def test_glob_question(self):
        self.assertTrue(_has_shell_metacharacters("ls file?.txt"))

    def test_semicolon(self):
        self.assertTrue(_has_shell_metacharacters("a; b"))

    def test_subshell(self):
        self.assertTrue(_has_shell_metacharacters("(echo hi)"))

    def test_heredoc(self):
        self.assertTrue(_has_shell_metacharacters("cat << EOF"))

    def test_newline(self):
        self.assertTrue(_has_shell_metacharacters("echo\nfoo"))


# ---------------------------------------------------------------------------
# validate_shell_syntax
# ---------------------------------------------------------------------------

class TestValidateShellSyntax(unittest.TestCase):

    def test_valid_simple(self):
        ok, err = validate_shell_syntax("echo hi")
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_valid_with_env(self):
        ok, err = validate_shell_syntax("FOO=1 echo hi")
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_env_only_invalid(self):
        ok, err = validate_shell_syntax("FOO=1")
        self.assertFalse(ok)
        self.assertIsNotNone(err)

    def test_unclosed_quote_invalid(self):
        ok, err = validate_shell_syntax('echo "oops')
        self.assertFalse(ok)
        self.assertIsNotNone(err)


# ---------------------------------------------------------------------------
# build_shell_command
# ---------------------------------------------------------------------------

class TestBuildShellCommand(unittest.TestCase):

    def test_no_env_no_sudo(self):
        result = build_shell_command({}, "echo hi")
        self.assertEqual(result, "echo hi")

    def test_env_vars_prepended(self):
        result = build_shell_command({"X": "1"}, "echo hi")
        self.assertIn("export X=", result)
        self.assertIn("echo hi", result)

    def test_task_env_merged(self):
        result = build_shell_command({"A": "2"}, "echo hi", task_env={"B": "3"})
        self.assertIn("export A=", result)
        self.assertIn("export B=", result)

    def test_env_vars_override_task_env(self):
        result = build_shell_command({"X": "new"}, "echo hi", task_env={"X": "old"})
        # The command-level env should win; shlex.quote only quotes when necessary
        self.assertIn("export X=", result)
        self.assertIn("new", result)
        self.assertNotIn("old", result)

    def test_sudo_wrapping(self):
        result = build_shell_command({}, "echo hi", sudo=True)
        self.assertIn("sudo", result)
        self.assertIn("bash", result)

    def test_sudo_user_wrapping(self):
        result = build_shell_command({}, "echo hi", sudo=True, sudo_user="deploy")
        self.assertIn("sudo", result)
        self.assertIn("-u", result)
        self.assertIn("deploy", result)


if __name__ == "__main__":
    unittest.main()
