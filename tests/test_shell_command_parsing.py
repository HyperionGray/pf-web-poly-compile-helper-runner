import os
import sys
import subprocess
import tempfile

import pytest


# Test pf-runner (installed runner) behavior.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pf-runner"))

try:
    import pf_parser
    import pf_shell
except ImportError:
    pytest.skip("pf-runner modules not available", allow_module_level=True)


def test_execute_shell_command_preserves_redirects_and_grouping():
    # Previously, the command parser would quote tokens like ">/dev/null", turning
    # redirects into literal arguments and breaking common idioms.
    rc = pf_shell.execute_shell_command(
        "command -v bash >/dev/null 2>&1 || (echo 'missing bash' && exit 1)"
    )
    assert rc == 0


def test_execute_shell_command_preserves_env_assignments():
    rc = pf_shell.execute_shell_command(
        'FOO="a b" python3 -c "import os,sys; sys.exit(0 if os.getenv(\'FOO\')==\'a b\' else 2)"'
    )
    assert rc == 0


def test_polyglot_python_at_file_runs_in_place_for_imports():
    with tempfile.TemporaryDirectory() as td:
        pkg_dir = os.path.join(td, "pkg")
        os.makedirs(pkg_dir, exist_ok=True)
        with open(os.path.join(pkg_dir, "__init__.py"), "w", encoding="utf-8") as f:
            f.write("")
        with open(os.path.join(pkg_dir, "helper.py"), "w", encoding="utf-8") as f:
            f.write("VAL = 123\n")

        script_path = os.path.join(td, "main.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write("from pkg.helper import VAL\nprint(VAL)\n")

        rendered, lang = pf_parser._render_polyglot_command("python", f"@{script_path}", td)
        assert lang == "python"
        assert rendered is not None
        assert script_path in rendered
        assert "mktemp" not in rendered

        result = subprocess.run(["bash", "-lc", rendered], cwd=td, check=False)
        assert result.returncode == 0


def test_polyglot_c_at_file_compiles_from_real_path_for_includes():
    with tempfile.TemporaryDirectory() as td:
        inc_dir = os.path.join(td, "inc")
        os.makedirs(inc_dir, exist_ok=True)
        with open(os.path.join(inc_dir, "helper.h"), "w", encoding="utf-8") as f:
            f.write('#define MAGIC 7\n')

        c_path = os.path.join(td, "main.c")
        with open(c_path, "w", encoding="utf-8") as f:
            f.write(
                '#include "inc/helper.h"\n'
                "int main() { return (MAGIC == 7) ? 0 : 1; }\n"
            )

        rendered, lang = pf_parser._render_polyglot_command("c", f"@{c_path}", td)
        assert lang == "c"
        assert rendered is not None
        assert c_path in rendered

        result = subprocess.run(["bash", "-lc", rendered], cwd=td, check=False)
        assert result.returncode == 0

