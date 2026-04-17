import tempfile
import textwrap
import types
import os

from pf_args import PfArgumentParser
from pf_parser import parse_pfyfile_text
from pf_main import PfRunner
from pf_task_executor import TaskExecutor


def test_gnu_style_params_are_forwarded_to_task():
    parser = PfArgumentParser()

    ns = parser.parse_args(["mytask", "--foo", "bar", "--flag"])
    assert ns.command == "run"
    # Tasks should see the raw params (still prefixed with --) for downstream parsing
    assert ns.tasks == ["mytask", "--foo", "bar", "--flag"]

    ns_eq = parser.parse_args(["mytask", "--foo=bar"])
    assert ns_eq.tasks == ["mytask", "--foo=bar"]


def test_default_lang_in_task_header_sets_lang():
    code = """task demo default_lang=python
  shell print("hi")
end
"""
    tasks = parse_pfyfile_text(code)
    assert tasks["demo"].default_lang == "python"
    # Header param should not linger as a normal param
    assert "default_lang" not in tasks["demo"].params


def test_inline_lang_bracket_executes():
    pfy = textwrap.dedent(
        """
        task inline-lang
          shell [lang:python] print("inline-ok")
        end
        """
    )
    with tempfile.NamedTemporaryFile("w", suffix=".pf") as f:
        f.write(pfy)
        f.flush()
        runner = PfRunner()
        rc = runner.run_command(["--file", f.name, "inline-lang"])
        assert rc == 0


def test_task_executor_uses_main_runner_execution_path():
    pfy = textwrap.dedent(
        """
        task inline-lang
          shell [lang:python] print("executor-ok")
        end
        """
    )
    with tempfile.NamedTemporaryFile("w", suffix=".pf") as f:
        f.write(pfy)
        f.flush()
        args = types.SimpleNamespace(
            task="inline-lang",
            file=f.name,
            env=[],
            hosts=[],
            host=[],
            user=None,
            port=None,
            sudo=False,
            sudo_user=None,
            task_args=[],
        )
        rc = TaskExecutor().handle_run_command(args)
        assert rc == 0


def test_env_only_shell_assignment_persists_across_shell_lang_switch():
    expected_root = os.getcwd()
    pfy = textwrap.dedent(
        f"""
        task keep-state
          shell ROOT="$(pwd)"
          shell [lang:python] import os, sys; sys.exit(0 if os.environ.get("ROOT") == {expected_root!r} else 1)
        end
        """
    )
    with tempfile.NamedTemporaryFile("w", suffix=".pf") as f:
        f.write(pfy)
        f.flush()
        runner = PfRunner()
        rc = runner.run_command(["--file", f.name, "keep-state"])
        assert rc == 0
