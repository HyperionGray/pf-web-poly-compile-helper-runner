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


def test_python_file_shebang_default_lang_executes(tmp_path: Path) -> None:
    fixture = tmp_path / "file-default-lang.pf"
    _write_pf(
        fixture,
        """
        #!lang:python
        task py-default
          shell print("file-default-ok")
        end
        """,
    )

    result = _run_pf(tmp_path, str(fixture), "py-default")

    assert result.returncode == 0, result.stderr
    assert "file-default-ok" in result.stdout


def test_shell_lang_default_restores_inherited_default_lang(tmp_path: Path) -> None:
    fixture = tmp_path / "shell-lang-default.pf"
    _write_pf(
        fixture,
        """
        task restore-default default_lang=python
          shell_lang bash
          shell echo "bash-before-default"
          shell_lang default
          shell print("default-restored-ok")
        end
        """,
    )

    result = _run_pf(tmp_path, str(fixture), "restore-default")

    assert result.returncode == 0, result.stderr
    assert "bash-before-default" in result.stdout
    assert "default-restored-ok" in result.stdout


def test_shell_lang_none_clears_override_and_uses_plain_shell(tmp_path: Path) -> None:
    fixture = tmp_path / "shell-lang-none.pf"
    _write_pf(
        fixture,
        """
        task clear-override
          shell_lang python
          shell print("python-before-none")
          shell_lang none
          shell echo "plain-shell-after-none"
        end
        """,
    )

    result = _run_pf(tmp_path, str(fixture), "clear-override")

    assert result.returncode == 0, result.stderr
    assert "python-before-none" in result.stdout
    assert "plain-shell-after-none" in result.stdout


def test_python_polyglot_heredoc_redirect_supports_quoted_space_path(tmp_path: Path) -> None:
    fixture = tmp_path / "polyglot-redirect-spaces.pf"
    outfile = tmp_path / "quoted results.txt"
    _write_pf(
        fixture,
        f"""
        task py-heredoc-redirect-space
          shell [lang:python] << PYEOF > "{outfile}"
        print("redirect-space-ok")
        PYEOF
        end
        """,
    )

    result = _run_pf(tmp_path, str(fixture), "py-heredoc-redirect-space")

    assert result.returncode == 0, result.stderr
    assert outfile.read_text(encoding="utf-8").strip() == "redirect-space-ok"


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


def test_prune_reports_missing_heredoc_terminator(tmp_path: Path) -> None:
    fixture = tmp_path / "missing-heredoc-end.pf"
    _write_pf(
        fixture,
        """
        task bad-heredoc
          shell cat <<EOF
        missing-end
          shell echo "should-not-run"
        end
        """,
    )

    result = _run_pf(tmp_path, str(fixture), "prune")

    assert result.returncode == 1
    combined = result.stdout + result.stderr
    assert "Heredoc delimiter 'EOF' not found" in combined


def test_playwright_shell_lang_renders_browser_context_command(tmp_path: Path) -> None:
    sys.path.insert(0, str(REPO_ROOT / "pf-runner-full"))
    import pf_parser  # type: ignore

    rendered, lang = pf_parser._render_polyglot_command(
        "playwright",
        "console.log('playwright-inline-ok')",
        str(tmp_path),
    )

    assert lang == "playwright"
    assert rendered is not None
    assert "const { chromium } = require('playwright');" in rendered
    assert "const page = await browser.newPage();" in rendered
    assert "console.log('playwright-inline-ok')" in rendered


def test_playwright_alias_browser_js_maps_to_playwright(tmp_path: Path) -> None:
    sys.path.insert(0, str(REPO_ROOT / "pf-runner-full"))
    import pf_parser  # type: ignore

    _, lang = pf_parser._render_polyglot_command(
        "browser-js",
        "console.log('alias-ok')",
        str(tmp_path),
    )

    assert lang == "playwright"
