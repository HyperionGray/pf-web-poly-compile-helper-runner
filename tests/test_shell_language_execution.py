#!/usr/bin/env python3
import subprocess
import sys
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PF_MAIN = REPO_ROOT / "pf-runner-full" / "pf_main.py"


def _write_pf(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def _run_pf(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PF_MAIN), *args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )


def test_python_polyglot_heredoc_executes(tmp_path: Path) -> None:
    fixture = tmp_path / "polyglot-heredoc.pf"
    _write_pf(
        fixture,
        """
        task py-heredoc
          shell [lang:python] << PYEOF
        print("py-heredoc-ok")
        PYEOF
        end
        """,
    )

    result = _run_pf(tmp_path, str(fixture), "py-heredoc")

    assert result.returncode == 0, result.stderr
    assert "py-heredoc-ok" in result.stdout


def test_python_polyglot_heredoc_redirect_writes_file(tmp_path: Path) -> None:
    fixture = tmp_path / "polyglot-redirect.pf"
    outfile = tmp_path / "polyglot-output.txt"
    _write_pf(
        fixture,
        f"""
        task py-heredoc-redirect
          shell [lang:python] << PYEOF > {outfile}
        print("redirect-ok")
        PYEOF
        end
        """,
    )

    result = _run_pf(tmp_path, str(fixture), "py-heredoc-redirect")

    assert result.returncode == 0, result.stderr
    assert outfile.read_text(encoding="utf-8").strip() == "redirect-ok"


def test_shell_lang_python_block_executes_with_indentation(tmp_path: Path) -> None:
    fixture = tmp_path / "python-block.pf"
    _write_pf(
        fixture,
        """
        task py-block
          shell_lang python
          shell |
            for i in range(2):
                print(f"py-block:{i}")
        end
        """,
    )

    result = _run_pf(tmp_path, str(fixture), "py-block")

    assert result.returncode == 0, result.stderr
    assert "py-block:0" in result.stdout
    assert "py-block:1" in result.stdout


def test_shell_lang_bash_block_preserves_bash_syntax(tmp_path: Path) -> None:
    fixture = tmp_path / "bash-block.pf"
    _write_pf(
        fixture,
        """
        task bash-block
          shell_lang bash
          shell |
            arr=(one two)
            [[ -f "/etc/passwd" ]] && echo "${arr[0]}"
            echo "${arr[@]}"
        end
        """,
    )

    result = _run_pf(tmp_path, str(fixture), "bash-block")

    assert result.returncode == 0, result.stderr
    assert "one" in result.stdout
    assert "one two" in result.stdout


def test_plain_shell_heredoc_still_works(tmp_path: Path) -> None:
    fixture = tmp_path / "shell-heredoc.pf"
    _write_pf(
        fixture,
        """
        task shell-heredoc
          shell cat <<'EOF'
        shell-heredoc-ok
        EOF
        end
        """,
    )

    result = _run_pf(tmp_path, str(fixture), "shell-heredoc")

    assert result.returncode == 0, result.stderr
    assert "shell-heredoc-ok" in result.stdout
