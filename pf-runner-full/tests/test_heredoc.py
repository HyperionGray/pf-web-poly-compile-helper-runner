"""Regression test ensuring the Lark parser supports shell heredocs."""

import contextlib
import io
import tempfile
import textwrap

import pf_main
from pf_lark_parser import parse_pf
from pf_main import PfRunner
from pf_parser import parse_pfyfile_text


def test_shell_heredoc_parsing_includes_block():
    """Ensure a heredoc shell statement parses as a single command."""
    code = """task heredoc
  describe Heredoc test
  shell cat <<'EOF'
Hello
EOF
end"""

    tasks = parse_pf(code)
    assert "heredoc" in tasks

    body = tasks["heredoc"]["body"]
    assert body, "Expected at least one body item"

    shell_stmt = next((item for item in body if item.get("type") == "shell"), None)
    assert shell_stmt is not None, "Shell statement not found in task body"
    command = shell_stmt["command"]

    assert "shell cat <<'EOF'\nHello\nEOF\n" in command


def test_unterminated_heredoc_does_not_swallow_following_tasks():
    """Ensure parser keeps reading subsequent tasks when heredoc is unterminated."""
    code = textwrap.dedent(
        """\
        task broken
          shell cat <<EOF
          hello
        end

        task still-there
          describe This task should still be parsed
        end
        """
    )

    tasks = parse_pfyfile_text(code)
    assert "broken" in tasks
    assert "still-there" in tasks


def test_unterminated_pregrouped_heredoc_fails_before_execution(monkeypatch):
    """Ensure pre-grouped heredoc path raises instead of attempting execution."""
    pfy = textwrap.dedent(
        """\
        task broken
          shell cat <<EOF
          hello
        end
        """
    )
    with tempfile.NamedTemporaryFile("w", suffix=".pf") as pfy_file:
        pfy_file.write(pfy)
        pfy_file.flush()

        executed = False

        def _record_exec(*_args, **_kwargs):
            nonlocal executed
            executed = True
            return 0

        monkeypatch.setattr(pf_main, "_exec_line_fabric", _record_exec)

        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            rc = PfRunner().run_command(["--file", pfy_file.name, "broken"])

    assert rc == 1
    assert not executed
    assert "Heredoc delimiter 'EOF' not found" in stderr.getvalue()


def test_bash_heredoc_redirection_writes_expected_content(tmp_path):
    """Regression: heredoc redirection should not be double-applied/clobbered."""
    output_file = tmp_path / "heredoc.txt"
    pfy_path = tmp_path / "Pfyfile.pf"
    pfy_path.write_text(
        textwrap.dedent(
            f"""\
            task write-out
              shell cat <<EOF > {output_file}
            hello from heredoc
            EOF
            end
            """
        ),
        encoding="utf-8",
    )

    rc = PfRunner().run_command(["--file", str(pfy_path), "write-out"])
    assert rc == 0
    assert output_file.exists()
    assert output_file.read_text(encoding="utf-8") == "hello from heredoc\n"
