"""Regression test ensuring the Lark parser supports shell heredocs."""

from pf_lark_parser import parse_pf


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
