"""Regression tests for bash-friendly parsing and passthrough blocks."""

from pf_lark_parser import parse_pf


def test_shell_pipe_and_inline_passthrough():
    code = """#!lang:bash
task bashy
  default_lang bash
  shell |
    echo hi
    for i in 1 2; do echo $i; done
  echo "inline ok"
end
"""
    tasks = parse_pf(code)
    assert "bashy" in tasks
    task = tasks["bashy"]
    assert task.get("default_lang") == "bash"

    body = task["body"]
    shell_cmd = next(item for item in body if item.get("type") == "shell")["command"]
    # We should keep all bash lines without parse errors
    assert "for i in 1 2; do echo $i; done" in shell_cmd
    assert "echo \"inline ok\"" in shell_cmd


def test_file_shebang_sets_default_lang():
    code = """#!lang:python
task simple
  shell echo hi
end
"""
    tasks = parse_pf(code)
    assert tasks["simple"].get("default_lang") == "python"
