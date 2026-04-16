#!/usr/bin/env python3
"""
Unit tests for pf_exceptions.py

Covers:
- PFException base class and format_error output
- PFSyntaxError default suggestion
- PFExecutionError including PE detection on Linux
- PFEnvironmentError subshell annotation
- PFTaskNotFoundError fuzzy suggestions
- PFConnectionError host formatting
- format_exception_for_user for both PF and generic exceptions
- Helper functions: _detect_container_environment, _detect_subshell_depth,
  _get_platform_info, _format_environment_context
"""

import os
import sys
import platform
import tempfile
import unittest
from unittest.mock import patch, mock_open

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pf-runner-full"))

import pytest

try:
    from pf_exceptions import (
        PFException,
        PFSyntaxError,
        PFExecutionError,
        PFEnvironmentError,
        PFTaskNotFoundError,
        PFConnectionError,
        format_exception_for_user,
        _detect_container_environment,
        _detect_subshell_depth,
        _get_platform_info,
        _format_environment_context,
    )
except ImportError:
    pytest.skip("pf_exceptions module not available", allow_module_level=True)


# ---------------------------------------------------------------------------
# Helper detection tests
# ---------------------------------------------------------------------------

class TestDetectContainerEnvironment(unittest.TestCase):
    """Tests for _detect_container_environment."""

    @patch("os.path.exists", return_value=True)
    def test_detects_docker_via_dockerenv(self, mock_exists):
        result = _detect_container_environment()
        self.assertEqual(result, "docker")

    @patch("os.path.exists", return_value=False)
    @patch("builtins.open", mock_open(read_data="12:memory:/lxc/abc123\n"))
    def test_detects_lxc_via_cgroup(self, _):
        result = _detect_container_environment()
        self.assertEqual(result, "lxc")

    @patch("os.path.exists", return_value=False)
    @patch("builtins.open", mock_open(read_data="11:memory:/kubepods/pod123\n"))
    def test_detects_kubernetes_via_cgroup(self, _):
        result = _detect_container_environment()
        self.assertEqual(result, "kubernetes")

    @patch("os.path.exists", return_value=False)
    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch.dict(os.environ, {"container": "podman"})
    def test_detects_via_container_env_var(self, *_):
        result = _detect_container_environment()
        self.assertEqual(result, "podman")

    @patch("os.path.exists", return_value=False)
    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch.dict(os.environ, {}, clear=True)
    def test_returns_none_when_not_in_container(self, *_):
        env_backup = os.environ.pop("container", None)
        try:
            result = _detect_container_environment()
            self.assertIsNone(result)
        finally:
            if env_backup is not None:
                os.environ["container"] = env_backup


class TestDetectSubshellDepth(unittest.TestCase):
    """Tests for _detect_subshell_depth."""

    @patch.dict(os.environ, {"SHLVL": "3"})
    def test_returns_depth_minus_one(self):
        self.assertEqual(_detect_subshell_depth(), 2)

    @patch.dict(os.environ, {"SHLVL": "1"})
    def test_returns_zero_for_shlvl_one(self):
        self.assertEqual(_detect_subshell_depth(), 0)

    @patch.dict(os.environ, {}, clear=True)
    def test_returns_zero_without_shlvl(self):
        env_backup = os.environ.pop("SHLVL", None)
        try:
            self.assertEqual(_detect_subshell_depth(), 0)
        finally:
            if env_backup is not None:
                os.environ["SHLVL"] = env_backup


class TestGetPlatformInfo(unittest.TestCase):
    """Tests for _get_platform_info."""

    def test_returns_expected_keys(self):
        info = _get_platform_info()
        self.assertIn("system", info)
        self.assertIn("machine", info)
        self.assertIn("python_version", info)

    def test_python_version_matches(self):
        info = _get_platform_info()
        self.assertEqual(info["python_version"], platform.python_version())


class TestFormatEnvironmentContext(unittest.TestCase):
    """Tests for _format_environment_context."""

    def test_contains_platform_and_cwd(self):
        ctx = _format_environment_context()
        self.assertIn("Platform:", ctx)
        self.assertIn("CWD:", ctx)
        self.assertIn(os.getcwd(), ctx)

    def test_contains_container_line(self):
        ctx = _format_environment_context()
        self.assertIn("Container:", ctx)


# ---------------------------------------------------------------------------
# Exception class tests
# ---------------------------------------------------------------------------

class TestPFException(unittest.TestCase):
    """Tests for the PFException base class."""

    def test_basic_creation(self):
        exc = PFException(message="test error")
        self.assertEqual(exc.message, "test error")
        self.assertIsNotNone(exc._traceback)
        self.assertIsNotNone(exc._context)

    def test_format_error_contains_message(self):
        exc = PFException(message="something broke")
        output = exc.format_error()
        self.assertIn("something broke", output)
        self.assertIn("PF ERROR", output)

    def test_format_error_includes_suggestion(self):
        exc = PFException(message="fail", suggestion="try again")
        output = exc.format_error()
        self.assertIn("Suggestion: try again", output)

    def test_format_error_includes_task_name(self):
        exc = PFException(message="fail", task_name="build")
        output = exc.format_error()
        self.assertIn("Task: build", output)

    def test_format_error_includes_command_and_exit_code(self):
        exc = PFException(message="fail", command="echo hi", exit_code=42)
        output = exc.format_error()
        self.assertIn("Command: echo hi", output)
        self.assertIn("Exit Code: 42", output)

    def test_format_error_without_traceback(self):
        exc = PFException(message="fail")
        output = exc.format_error(include_traceback=False)
        self.assertNotIn("Python Traceback:", output)

    def test_format_error_without_environment(self):
        exc = PFException(message="fail")
        output = exc.format_error(include_environment=False)
        self.assertNotIn("Relevant Environment Variables:", output)

    def test_captures_pf_env_vars(self):
        with patch.dict(os.environ, {"PF_DEBUG": "1"}):
            exc = PFException(message="fail")
            self.assertIn("PF_DEBUG", exc.environment)

    def test_str_returns_formatted(self):
        exc = PFException(message="test")
        self.assertIn("test", str(exc))


class TestPFSyntaxError(unittest.TestCase):

    def test_default_suggestion(self):
        exc = PFSyntaxError(message="bad syntax")
        self.assertIn("prune", exc.suggestion)


class TestPFExecutionError(unittest.TestCase):

    def test_basic_creation(self):
        exc = PFExecutionError(message="command failed", exit_code=1)
        self.assertEqual(exc.message, "command failed")
        self.assertEqual(exc.exit_code, 1)

    @patch("platform.system", return_value="Linux")
    def test_pe_detection_by_extension(self, _):
        exc = PFExecutionError(
            message="exec failed",
            exit_code=126,
            command="app.exe",
        )
        self.assertIsNotNone(exc.suggestion)
        self.assertIn("Windows PE", exc.suggestion)

    @patch("platform.system", return_value="Linux")
    def test_pe_detection_by_mz_header(self, _):
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as tmp:
            tmp.write(b"MZ" + b"\x00" * 100)
            tmp.flush()
            tmp_path = tmp.name

        try:
            exc = PFExecutionError(
                message="exec failed",
                exit_code=127,
                command=tmp_path,
            )
            self.assertIn("Windows PE", exc.suggestion)
        finally:
            os.unlink(tmp_path)

    @patch("platform.system", return_value="Darwin")
    def test_no_pe_detection_on_macos(self, _):
        exc = PFExecutionError(
            message="exec failed",
            exit_code=126,
            command="app.exe",
        )
        # On non-Linux, PE detection should not trigger
        self.assertTrue(exc.suggestion is None or "Windows PE" not in exc.suggestion)


class TestPFEnvironmentError(unittest.TestCase):

    @patch("pf_exceptions._detect_subshell_depth", return_value=3)
    def test_subshell_annotation(self, _):
        exc = PFEnvironmentError(message="missing VAR")
        self.assertIn("subshell", exc.message)
        self.assertIn("3", exc.message)


class TestPFTaskNotFoundError(unittest.TestCase):

    def test_message_contains_task_name(self):
        exc = PFTaskNotFoundError(task_name="deploy")
        self.assertIn("deploy", exc.message)

    def test_suggests_similar_tasks(self):
        exc = PFTaskNotFoundError(
            task_name="deploy",
            available_tasks=["deploy-prod", "deploy-staging", "build"],
        )
        self.assertIn("deploy-prod", exc.suggestion)

    def test_fallback_suggestion(self):
        exc = PFTaskNotFoundError(task_name="xyz", available_tasks=[])
        self.assertIn("pf list", exc.suggestion)

    def test_explicit_suggestion_takes_precedence(self):
        exc = PFTaskNotFoundError(
            task_name="xyz",
            available_tasks=["xyz-real"],
            suggestion="custom hint",
        )
        self.assertEqual(exc.suggestion, "custom hint")


class TestPFConnectionError(unittest.TestCase):

    def test_host_in_message(self):
        exc = PFConnectionError(message="timeout", host="10.0.0.1")
        self.assertIn("10.0.0.1", exc.message)

    def test_default_suggestion(self):
        exc = PFConnectionError(message="timeout")
        self.assertIn("reachable", exc.suggestion)


# ---------------------------------------------------------------------------
# format_exception_for_user
# ---------------------------------------------------------------------------

class TestFormatExceptionForUser(unittest.TestCase):

    def test_formats_pf_exception(self):
        exc = PFException(message="oops")
        output = format_exception_for_user(exc)
        self.assertIn("PF ERROR", output)
        self.assertIn("oops", output)

    def test_formats_generic_exception(self):
        try:
            raise ValueError("bad value")
        except ValueError as exc:
            output = format_exception_for_user(exc)
        self.assertIn("UNEXPECTED ERROR", output)
        self.assertIn("ValueError", output)
        self.assertIn("bad value", output)

    def test_respects_traceback_flag(self):
        exc = PFException(message="x")
        output = format_exception_for_user(exc, include_traceback=False)
        self.assertNotIn("Python Traceback:", output)


if __name__ == "__main__":
    unittest.main()
