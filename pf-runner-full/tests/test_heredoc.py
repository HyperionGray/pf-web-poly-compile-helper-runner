"""Regression test ensuring the Lark parser supports shell heredocs."""

from pf_lark_parser import parse_pf
from pf_parser import _parse_heredoc_syntax


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


def test_shell_heredoc_parsing_supports_hyphenated_delimiter():
    """Ensure heredoc delimiters with hyphens parse as a single command."""
    code = """task heredoc-hyphen
  describe Heredoc with hyphen delimiter
  shell cat <<'EOF-JSON'
{"ok": true}
EOF-JSON
end"""

    tasks = parse_pf(code)
    assert "heredoc-hyphen" in tasks

    body = tasks["heredoc-hyphen"]["body"]
    shell_stmt = next((item for item in body if item.get("type") == "shell"), None)
    assert shell_stmt is not None
    assert "EOF-JSON" in shell_stmt["command"]


def test_runtime_heredoc_parser_supports_extended_delimiters():
    """Runtime parser should accept the same delimiter forms as grammar."""
    delimiter, outfile, strip_tabs = _parse_heredoc_syntax("<<- 'EOF.JSON-1' > out.txt")
    assert delimiter == "EOF.JSON-1"
    assert outfile == "out.txt"
    assert strip_tabs is True
