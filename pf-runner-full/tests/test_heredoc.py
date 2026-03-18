"""Regression test ensuring the Lark parser supports shell heredocs."""

import textwrap

from pf_lark_parser import parse_pf
from pf_parser import run_task_by_name


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


def test_run_task_by_name_executes_grouped_bare_heredoc(tmp_path):
    """Grouped bare heredocs should still execute via the refactored runner path."""
    output_path = tmp_path / "heredoc-output.txt"
    pfyfile = tmp_path / "Pfyfile.pf"
    pfyfile.write_text(
        textwrap.dedent(
            f"""
            task grouped-heredoc
              shell <<'EOF' > {output_path}
            printf 'grouped-ok\\n'
            EOF
            end
            """
        ).lstrip(),
        encoding="utf-8",
    )

    rc = run_task_by_name("grouped-heredoc", file_arg=str(pfyfile))

    assert rc == 0
    assert output_path.read_text(encoding="utf-8") == "grouped-ok\n"
