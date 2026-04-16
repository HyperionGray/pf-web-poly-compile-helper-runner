"""Tests for pf_exceptions module: exception classes, formatting, and context detection."""

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
)


class TestPFException:
    def test_basic_creation(self):
        exc = PFException(message="something broke")
        assert exc.message == "something broke"

    def test_suggestion_included(self):
        exc = PFException(message="err", suggestion="try this")
        assert exc.suggestion == "try this"

    def test_format_error_contains_message(self):
        exc = PFException(message="test error")
        formatted = exc.format_error()
        assert "test error" in formatted
        assert "PF ERROR" in formatted

    def test_format_error_contains_task(self):
        exc = PFException(message="fail", task_name="deploy")
        formatted = exc.format_error()
        assert "deploy" in formatted

    def test_format_error_contains_command(self):
        exc = PFException(message="fail", command="echo boom")
        formatted = exc.format_error()
        assert "echo boom" in formatted


class TestPFTaskNotFoundError:
    def test_message_includes_task_name(self):
        exc = PFTaskNotFoundError(task_name="missing-task")
        assert "missing-task" in exc.message

    def test_similar_tasks_suggested(self):
        exc = PFTaskNotFoundError(
            task_name="buil",
            available_tasks=["build", "bundle", "deploy"],
        )
        assert exc.suggestion is not None
        assert "build" in exc.suggestion or "pf list" in exc.suggestion

    def test_explicit_suggestion_overrides(self):
        exc = PFTaskNotFoundError(
            task_name="x",
            available_tasks=["y"],
            suggestion="use y instead",
        )
        assert exc.suggestion == "use y instead"


class TestPFSyntaxError:
    def test_default_suggestion(self):
        exc = PFSyntaxError(message="bad syntax")
        assert "prune" in exc.suggestion


class TestPFConnectionError:
    def test_host_in_message(self):
        exc = PFConnectionError(message="timeout", host="10.0.0.1")
        assert "10.0.0.1" in exc.message


class TestFormatExceptionForUser:
    def test_pf_exception(self):
        exc = PFException(message="pf error")
        text = format_exception_for_user(exc)
        assert "PF ERROR" in text
        assert "pf error" in text

    def test_generic_exception(self):
        exc = ValueError("bad value")
        text = format_exception_for_user(exc)
        assert "UNEXPECTED ERROR" in text
        assert "bad value" in text

    def test_without_traceback(self):
        exc = PFException(message="err")
        text = exc.format_error(include_traceback=False)
        assert "Python Traceback:" not in text


class TestContextDetection:
    def test_subshell_depth_returns_int(self):
        depth = _detect_subshell_depth()
        assert isinstance(depth, int)
        assert depth >= 0

    def test_container_detection_returns_str_or_none(self):
        result = _detect_container_environment()
        assert result is None or isinstance(result, str)

    def test_platform_info_has_required_keys(self):
        info = _get_platform_info()
        assert "system" in info
        assert "machine" in info
        assert "python_version" in info
