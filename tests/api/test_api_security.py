#!/usr/bin/env python3
"""
Security tests for pf_api.py

Covers:
- Task name validation (reject path traversal, injection characters)
- Parameter key and value sanitization
- Command injection prevention via unsanitized params
"""

import os
import re
import sys

import pytest

# Ensure pf-runner-full is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "pf-runner-full"))


# ---------------------------------------------------------------------------
# Unit tests for validation helpers (no FastAPI/server needed)
# ---------------------------------------------------------------------------

class TestTaskNameValidation:
    """Validate _VALID_TASK_NAME_RE rejects dangerous input."""

    VALID_TASK_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")

    @pytest.mark.parametrize(
        "name",
        [
            "hello",
            "web-dev",
            "build_all",
            "my.task",
            "Task123",
            "a",
        ],
    )
    def test_valid_names_accepted(self, name):
        assert self.VALID_TASK_NAME_RE.match(name), f"'{name}' should be valid"

    @pytest.mark.parametrize(
        "name",
        [
            "",
            "../etc/passwd",
            "task; rm -rf /",
            "task$(whoami)",
            "task`id`",
            "-leading-dash",
            ".leading-dot",
            "a" * 200,  # too long
            "task\x00null",
            "task\nnewline",
        ],
    )
    def test_invalid_names_rejected(self, name):
        assert not self.VALID_TASK_NAME_RE.match(name), f"'{name}' should be rejected"


class TestParamKeyValidation:
    """Validate _VALID_PARAM_KEY_RE rejects dangerous keys."""

    VALID_PARAM_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")

    @pytest.mark.parametrize(
        "key",
        [
            "name",
            "_private",
            "ENV_VAR",
            "key123",
        ],
    )
    def test_valid_keys_accepted(self, key):
        assert self.VALID_PARAM_KEY_RE.match(key), f"'{key}' should be valid"

    @pytest.mark.parametrize(
        "key",
        [
            "",
            "123start",
            "key-with-dash",
            "key.with.dot",
            "key;injection",
            "key$(cmd)",
            "../traversal",
        ],
    )
    def test_invalid_keys_rejected(self, key):
        assert not self.VALID_PARAM_KEY_RE.match(key), f"'{key}' should be rejected"


class TestParamValueSanitization:
    """Verify shlex.quote prevents shell metacharacter injection."""

    @pytest.mark.parametrize(
        "value,description",
        [
            ("normal_value", "plain value"),
            ("value with spaces", "spaces"),
            ("$(whoami)", "command substitution"),
            ("`id`", "backtick substitution"),
            ("val;rm -rf /", "semicolon injection"),
            ("val&&echo pwned", "double-ampersand injection"),
            ("val|cat /etc/passwd", "pipe injection"),
            ("val\nnewline", "newline injection"),
        ],
    )
    def test_shlex_quote_neutralizes_injection(self, value, description):
        import shlex

        quoted = shlex.quote(value)
        # shlex.quote wraps in single quotes or escapes; the result must NOT
        # contain unquoted shell metacharacters that could be interpreted.
        assert quoted.startswith("'") or not any(
            c in quoted for c in ";|&$`\n"
        ), f"shlex.quote failed for {description}: {quoted}"


# ---------------------------------------------------------------------------
# Integration tests (import pf_api helpers if available)
# ---------------------------------------------------------------------------

class TestApiValidationFunctions:
    """Test the actual _validate_task_name and _validate_params functions."""

    @pytest.fixture(autouse=True)
    def _import_api(self):
        """Try to import pf_api; skip if FastAPI is unavailable."""
        try:
            import pf_api  # noqa: F811

            self.validate_task_name = pf_api._validate_task_name
            self.validate_params = pf_api._validate_params
        except (ImportError, SystemExit):
            pytest.skip("pf_api not importable (FastAPI missing)")

    def test_validate_task_name_valid(self):
        assert self.validate_task_name("hello-world") == "hello-world"

    def test_validate_task_name_rejects_traversal(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            self.validate_task_name("../etc/passwd")
        assert exc_info.value.status_code == 400

    def test_validate_task_name_rejects_injection(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            self.validate_task_name("task;whoami")
        assert exc_info.value.status_code == 400

    def test_validate_params_valid(self):
        result = self.validate_params({"name": "world", "count": "5"})
        assert "name" in result
        assert "count" in result

    def test_validate_params_rejects_bad_key(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            self.validate_params({"bad;key": "value"})
        assert exc_info.value.status_code == 400

    def test_validate_params_quotes_values(self):
        result = self.validate_params({"key": "$(whoami)"})
        # The sanitized value must be shell-safe
        assert "$(" not in result["key"] or result["key"].startswith("'")
