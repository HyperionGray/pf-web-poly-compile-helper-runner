#!/usr/bin/env python3
"""
Pytest-based tests for pf-runner-full core functionality.

Covers:
- PfRunner instantiation and version command
- Task name normalization and lookup
- Module name extraction from Pfyfile paths
- Argument parsing (legacy and modern)
- List command behavior
- Error handling for missing tasks
"""

import os
import sys
import tempfile
import textwrap

import pytest

# Ensure pf-runner-full is importable
_runner_dir = os.path.join(os.path.dirname(__file__), "..", "..", "pf-runner-full")
sys.path.insert(0, os.path.abspath(_runner_dir))

from pf_main import PfRunner  # noqa: E402
from pf_args import PfArgumentParser, HELP_VARIATIONS  # noqa: E402
from pf_exceptions import PFTaskNotFoundError  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def runner():
    """Create a fresh PfRunner instance for each test."""
    return PfRunner()


@pytest.fixture
def arg_parser():
    """Create a fresh PfArgumentParser."""
    return PfArgumentParser()


@pytest.fixture
def tmp_pfyfile(tmp_path):
    """Create a temporary Pfyfile with sample tasks."""
    pf_content = textwrap.dedent("""\
        task hello
          describe Say hello
          shell echo "hello world"
        end

        task build-project
          describe Build the project
          shell echo "building"
        end

        task run_tests foo="" bar="default"
          describe Run the test suite
          shell echo "testing foo=$foo bar=$bar"
        end
    """)
    pf_file = tmp_path / "Pfyfile.pf"
    pf_file.write_text(pf_content, encoding="utf-8")
    return str(pf_file)


# ---------------------------------------------------------------------------
# PfRunner instantiation
# ---------------------------------------------------------------------------

class TestPfRunnerInit:
    def test_creates_runner(self, runner):
        assert runner.arg_parser is not None
        assert runner.subcommand_manager is not None
        assert runner.builtin_handler is not None
        assert runner.task_executor is not None

    def test_autocorrect_initially_none(self, runner):
        assert runner.autocorrect is None


# ---------------------------------------------------------------------------
# Version command
# ---------------------------------------------------------------------------

class TestVersionCommand:
    def test_version_flag_returns_zero(self, runner, capsys):
        rc = runner.run_command(["--version"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "pf" in out.lower()

    def test_version_word_returns_zero(self, runner, capsys):
        rc = runner.run_command(["version"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "pf" in out.lower()


# ---------------------------------------------------------------------------
# Task name normalization
# ---------------------------------------------------------------------------

class TestTaskNameNormalization:
    def test_basic_normalization(self, runner):
        assert runner._normalize_task_name_key("Build_Project") == "build-project"

    def test_spaces_become_hyphens(self, runner):
        assert runner._normalize_task_name_key("build project") == "build-project"

    def test_multiple_hyphens_collapsed(self, runner):
        assert runner._normalize_task_name_key("build--project") == "build-project"

    def test_leading_trailing_hyphens_stripped(self, runner):
        assert runner._normalize_task_name_key("-build-project-") == "build-project"

    def test_empty_string(self, runner):
        assert runner._normalize_task_name_key("") == ""


# ---------------------------------------------------------------------------
# Module name extraction
# ---------------------------------------------------------------------------

class TestModuleNameExtraction:
    def test_standard_module_file(self, runner):
        assert runner._module_name_from_source_file("/path/Pfyfile.web-demo.pf") == "web-demo"

    def test_underscore_normalized(self, runner):
        assert runner._module_name_from_source_file("/path/Pfyfile.build_helpers.pf") == "build-helpers"

    def test_main_pfyfile_returns_none(self, runner):
        assert runner._module_name_from_source_file("/path/Pfyfile.pf") is None

    def test_none_input(self, runner):
        assert runner._module_name_from_source_file(None) is None

    def test_non_matching_file(self, runner):
        assert runner._module_name_from_source_file("/path/somefile.py") is None


# ---------------------------------------------------------------------------
# Task name lookup
# ---------------------------------------------------------------------------

class TestTaskNameLookup:
    def test_build_lookup_exact(self, runner):
        names = {"hello", "build-project", "run-tests"}
        lookup = runner._build_task_name_lookup(names)
        assert lookup["hello"] == "hello"
        assert lookup["build-project"] == "build-project"

    def test_find_match_case_insensitive(self, runner):
        names = {"Hello-World"}
        lookup = runner._build_task_name_lookup(names)
        result = runner._find_task_name_match("hello-world", lookup)
        assert result == "Hello-World"

    def test_find_match_underscore_hyphen(self, runner):
        names = {"build-project"}
        lookup = runner._build_task_name_lookup(names)
        result = runner._find_task_name_match("build_project", lookup)
        assert result == "build-project"

    def test_find_match_returns_none_for_unknown(self, runner):
        names = {"hello"}
        lookup = runner._build_task_name_lookup(names)
        assert runner._find_task_name_match("nonexistent", lookup) is None


# ---------------------------------------------------------------------------
# Format helpers
# ---------------------------------------------------------------------------

class TestFormatHelpers:
    def test_single_task_count(self, runner):
        assert runner._format_task_count(1) == "1 task"

    def test_multiple_task_count(self, runner):
        assert runner._format_task_count(5) == "5 tasks"

    def test_zero_task_count(self, runner):
        assert runner._format_task_count(0) == "0 tasks"


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

class TestArgumentParsing:
    def test_no_args_defaults_to_list(self, arg_parser):
        ns = arg_parser.parse_args([])
        assert ns.command == "list"

    def test_explicit_list(self, arg_parser):
        ns = arg_parser.parse_args(["list"])
        assert ns.command == "list"

    def test_explicit_run(self, arg_parser):
        ns = arg_parser.parse_args(["run", "hello"])
        assert ns.command == "run"
        assert "hello" in ns.tasks

    def test_help_variations_recognized(self, arg_parser):
        for variation in ("help", "hlep", "hepl", "hlp"):
            ns = arg_parser.parse_args([variation, "sometask"])
            assert ns.command == "help"
            assert ns.topic == "sometask"

    def test_file_flag(self, arg_parser):
        ns = arg_parser.parse_args(["--file", "/tmp/test.pf", "list"])
        assert ns.file == "/tmp/test.pf"


# ---------------------------------------------------------------------------
# List command with temp Pfyfile
# ---------------------------------------------------------------------------

class TestListCommand:
    def test_list_with_file(self, runner, tmp_pfyfile, capsys):
        rc = runner.run_command(["--file", tmp_pfyfile, "list"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "hello" in out
        assert "build-project" in out

    def test_list_shows_descriptions(self, runner, tmp_pfyfile, capsys):
        rc = runner.run_command(["--file", tmp_pfyfile, "list"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Say hello" in out


# ---------------------------------------------------------------------------
# Global env extraction
# ---------------------------------------------------------------------------

class TestGlobalEnvExtraction:
    def test_extracts_env_outside_task(self, runner):
        dsl = textwrap.dedent("""\
            env FOO=bar BAZ=qux
            task hello
              shell echo hi
            end
        """)
        env = runner._extract_global_env(dsl)
        assert env["FOO"] == "bar"
        assert env["BAZ"] == "qux"

    def test_ignores_env_inside_task(self, runner):
        dsl = textwrap.dedent("""\
            task hello
              env INSIDE=yes
              shell echo hi
            end
        """)
        env = runner._extract_global_env(dsl)
        assert "INSIDE" not in env


# ---------------------------------------------------------------------------
# Param token detection
# ---------------------------------------------------------------------------

class TestParamTokenDetection:
    def test_double_dash_is_param(self, runner):
        assert runner._looks_like_param_token("--verbose") is True

    def test_equals_is_param(self, runner):
        assert runner._looks_like_param_token("key=value") is True

    def test_bare_word_is_not_param(self, runner):
        assert runner._looks_like_param_token("hello") is False


# ---------------------------------------------------------------------------
# Help command
# ---------------------------------------------------------------------------

class TestHelpCommand:
    def test_help_on_existing_task(self, runner, tmp_pfyfile, capsys):
        rc = runner.run_command(["--file", tmp_pfyfile, "help", "hello"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "hello" in out.lower()

    def test_help_on_missing_task(self, runner, tmp_pfyfile, capsys):
        rc = runner.run_command(["--file", tmp_pfyfile, "help", "nonexistent"])
        assert rc == 1
        out = capsys.readouterr().out
        assert "not found" in out.lower()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
