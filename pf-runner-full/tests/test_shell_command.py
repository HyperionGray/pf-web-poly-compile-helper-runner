"""Tests for pf_shell module: command parsing, validation, and metacharacter detection."""

import pytest

from pf_shell import parse_shell_command, validate_shell_syntax, _has_shell_metacharacters
from pf_exceptions import PFExecutionError


class TestParseShellCommand:
    def test_plain_command(self):
        env, cmd = parse_shell_command("echo hello")
        assert env == {}
        assert "echo" in cmd
        assert "hello" in cmd

    def test_env_prefix(self):
        env, cmd = parse_shell_command("FOO=bar echo test")
        assert env == {"FOO": "bar"}
        assert "echo" in cmd

    def test_multiple_env_vars(self):
        env, cmd = parse_shell_command("A=1 B=2 python script.py")
        assert env == {"A": "1", "B": "2"}
        assert "python" in cmd

    def test_no_command_only_env(self):
        env, cmd = parse_shell_command("FOO=bar")
        assert env == {"FOO": "bar"}
        assert cmd == ""

    def test_flag_not_treated_as_env(self):
        env, cmd = parse_shell_command("--port=8080 serve")
        assert env == {}
        assert "--port=8080" in cmd

    def test_unclosed_quote_raises(self):
        with pytest.raises(PFExecutionError):
            parse_shell_command('echo "unclosed')


class TestHasShellMetacharacters:
    def test_pipe(self):
        assert _has_shell_metacharacters("cat file | grep foo") is True

    def test_redirect(self):
        assert _has_shell_metacharacters("echo hi > out.txt") is True

    def test_variable_expansion(self):
        assert _has_shell_metacharacters("echo $HOME") is True

    def test_plain_command(self):
        assert _has_shell_metacharacters("echo hello world") is False

    def test_semicolon(self):
        assert _has_shell_metacharacters("echo a; echo b") is True

    def test_and_operator(self):
        assert _has_shell_metacharacters("make && make install") is True

    def test_glob(self):
        assert _has_shell_metacharacters("ls *.py") is True


class TestValidateShellSyntax:
    def test_valid_command(self):
        is_valid, err = validate_shell_syntax("echo hello")
        assert is_valid is True
        assert err is None

    def test_valid_with_env(self):
        is_valid, err = validate_shell_syntax("PORT=8080 node server.js")
        assert is_valid is True
        assert err is None

    def test_empty_after_env_parse(self):
        # Only env vars, no actual command
        is_valid, err = validate_shell_syntax("FOO=bar")
        assert is_valid is False
        assert err is not None

    def test_unclosed_quote(self):
        is_valid, err = validate_shell_syntax('echo "unclosed')
        assert is_valid is False
        assert err is not None
