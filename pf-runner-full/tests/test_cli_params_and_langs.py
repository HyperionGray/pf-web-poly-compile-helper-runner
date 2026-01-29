import tempfile
import textwrap

from pf_args import PfArgumentParser
from pf_parser import parse_pfyfile_text
from pf_main import PfRunner


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
