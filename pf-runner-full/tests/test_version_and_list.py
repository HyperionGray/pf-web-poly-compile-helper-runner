"""Tests for PfRunner version and list command handling."""

import contextlib
import io
import os
import tempfile
import textwrap
from unittest.mock import patch

from pf_main import PfRunner
from pf_exceptions import PFExecutionError


class TestVersionCommand:
    def test_version_flag(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            rc = PfRunner().run_command(["--version"])
        assert rc == 0
        assert "pf" in stdout.getvalue().lower()

    def test_version_short_flag(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            rc = PfRunner().run_command(["-V"])
        assert rc == 0

    def test_version_subcommand(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            rc = PfRunner().run_command(["version"])
        assert rc == 0


class TestListCommandEdgeCases:
    def test_list_empty_pfyfile(self):
        pfy = textwrap.dedent("""\
            # empty file with no tasks
        """)
        with tempfile.NamedTemporaryFile("w", suffix=".pf") as f:
            f.write(pfy)
            f.flush()
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                rc = PfRunner().run_command(["--file", f.name, "list"])
            assert rc == 0
            assert "No tasks found" in stdout.getvalue()

    def test_list_with_tasks(self):
        pfy = textwrap.dedent("""\
            task hello
              describe Greet the user
              shell echo hello
            end
        """)
        with tempfile.NamedTemporaryFile("w", suffix=".pf") as f:
            f.write(pfy)
            f.flush()
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                rc = PfRunner().run_command(["--file", f.name, "list"])
            assert rc == 0
            assert "hello" in stdout.getvalue()
            assert "Greet the user" in stdout.getvalue()


class TestErrorOutput:
    def test_failure_shows_short_error_and_usage_when_pf_debug_is_off(self):
        stderr = io.StringIO()
        runner = PfRunner()
        with patch.object(runner, "_handle_run_command", side_effect=PFExecutionError(message="boom")):
            with patch.dict(os.environ, {"PF_DEBUG": "0"}):
                with contextlib.redirect_stderr(stderr):
                    rc = runner.run_command(["run", "demo-task"])

        output = stderr.getvalue()
        assert rc == 1
        assert "Error: boom" in output
        assert "usage: pf" in output
        assert "--env" in output
        assert "Python Traceback:" not in output

    def test_failure_shows_full_traceback_when_pf_debug_is_on(self):
        stderr = io.StringIO()
        runner = PfRunner()
        with patch.object(runner, "_handle_run_command", side_effect=PFExecutionError(message="boom")):
            with patch.dict(os.environ, {"PF_DEBUG": "1"}):
                with contextlib.redirect_stderr(stderr):
                    rc = runner.run_command(["run", "demo-task"])

        output = stderr.getvalue()
        assert rc == 1
        assert "PF ERROR" in output
        assert "Python Traceback:" in output
