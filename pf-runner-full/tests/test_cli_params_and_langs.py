import tempfile
import textwrap
import types
import os
import shutil

import pytest

from pf_args import PfArgumentParser
from pf_parser import parse_pfyfile_text
from pf_main import PfRunner
from pf_task_executor import TaskExecutor
from pf_polyglot import is_supported_language


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
          shell [lang:python] |
            import os
            import sys
            root = os.environ.get("ROOT")
            sys.exit(0 if root == {expected_root!r} else 1)
        end
        """
    )
    with tempfile.NamedTemporaryFile("w", suffix=".pf") as f:
        f.write(pfy)
        f.flush()
        runner = PfRunner()
        rc = runner.run_command(["--file", f.name, "keep-state"])
        assert rc == 0


def test_requested_languages_are_supported():
    requested_hints = ["c++", "fortran-latest", "java", "kotlin", "julia", "cuda", "rust"]
    unsupported = [hint for hint in requested_hints if not is_supported_language(hint)]
    assert unsupported == []


def test_requested_polyglot_languages_share_one_environment():
    required_tools = {
        "c++": ("clang++",),
        "fortran-latest": ("gfortran",),
        "java": ("javac", "java"),
        "kotlin": ("kotlinc", "java"),
        "julia": ("julia",),
        "cuda": ("nvcc",),
        "rust": ("rustc",),
    }
    all_languages = list(required_tools.keys())
    available_languages = [
        lang
        for lang in all_languages
        if all(shutil.which(tool) for tool in required_tools[lang])
    ]
    if not available_languages:
        pytest.skip("No requested language toolchains are available in this test environment")

    snippets = {
        "c++": """
            extern "C" char *getenv(const char *);
            extern "C" int strcmp(const char *, const char *);
            int main() {
              const char* a = getenv("PFY_SHARED_ENV");
              const char* b = getenv("SHARED_SHELL_VAR");
              if (!a || !b) return 1;
              return (strcmp(a, "poly-ok") == 0 && strcmp(b, "runner-state") == 0) ? 0 : 1;
            }
        """,
        "fortran-latest": """
            program main
              character(len=64) :: a
              character(len=64) :: b
              call get_environment_variable("PFY_SHARED_ENV", a)
              call get_environment_variable("SHARED_SHELL_VAR", b)
              if (trim(a) /= "poly-ok" .or. trim(b) /= "runner-state") stop 1; end program main
        """,
        "java": """
            public class Main {
              public static void main(String[] args) {
                String a = System.getenv("PFY_SHARED_ENV");
                String b = System.getenv("SHARED_SHELL_VAR");
                if (!"poly-ok".equals(a) || !"runner-state".equals(b)) {
                  System.exit(1);
                }
              }
            }
        """,
        "kotlin": """
            fun main() {
              val a = System.getenv("PFY_SHARED_ENV")
              val b = System.getenv("SHARED_SHELL_VAR")
              if (a != "poly-ok" || b != "runner-state") {
                throw RuntimeException("unexpected environment")
              }
            }
        """,
        "julia": """
            a = get(ENV, "PFY_SHARED_ENV", "")
            b = get(ENV, "SHARED_SHELL_VAR", "")
            a == "poly-ok" && b == "runner-state" || error("unexpected environment")
        """,
        "cuda": """
            extern "C" char *getenv(const char *);
            extern "C" int strcmp(const char *, const char *);
            int main() {
              const char* a = getenv("PFY_SHARED_ENV");
              const char* b = getenv("SHARED_SHELL_VAR");
              if (!a || !b) return 1;
              return (strcmp(a, "poly-ok") == 0 && strcmp(b, "runner-state") == 0) ? 0 : 1;
            }
        """,
        "rust": """
            fn main() {
                let a = std::env::var("PFY_SHARED_ENV").unwrap_or_default();
                let b = std::env::var("SHARED_SHELL_VAR").unwrap_or_default();
                if a != "poly-ok" || b != "runner-state" {
                    std::process::exit(1);
                }
            }
        """,
    }

    lines = [
        "task lang-env-shared",
        "  env PFY_SHARED_ENV=poly-ok",
        "  shell SHARED_SHELL_VAR=runner-state",
    ]
    for lang in available_languages:
        snippet = textwrap.dedent(snippets[lang]).strip("\n")
        lines.append(f"  shell [lang:{lang}] |")
        lines.extend([f"    {line}" for line in snippet.splitlines()])
    lines.append("end")
    pfy = "\n".join(lines) + "\n"

    with tempfile.NamedTemporaryFile("w", suffix=".pf") as f:
        f.write(pfy)
        f.flush()
        runner = PfRunner()
        rc = runner.run_command(["--file", f.name, "lang-env-shared"])
        assert rc == 0
