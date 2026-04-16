"""Tests for PfRunner version and list command handling."""

import contextlib
import io
import tempfile
import textwrap

from pf_main import PfRunner


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
