import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PF_RUNNER_DIR = REPO_ROOT / "pf-runner"
PF_MAIN = PF_RUNNER_DIR / "pf_main.py"


def _run_pf(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    # Ensure pf-runner is importable when running pf_main.py as a script.
    env["PYTHONPATH"] = f"{PF_RUNNER_DIR}{os.pathsep}{env.get('PYTHONPATH', '')}"
    return subprocess.run(
        [sys.executable, str(PF_MAIN), *args],
        cwd=str(cwd or REPO_ROOT),
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )


def test_parse_groups_shell_command_heredoc():
    sys.path.insert(0, str(PF_RUNNER_DIR))
    import pf_parser  # noqa: E402

    text = """\
task t
  shell_lang bash
  shell cat << 'EOF'
hello
EOF
end
"""
    tasks = pf_parser.parse_pfyfile_text(text)
    assert "t" in tasks
    lines = tasks["t"].lines
    assert len(lines) == 2
    assert "shell cat << 'EOF'" in lines[1]
    assert "hello" in lines[1]
    assert lines[1].strip().endswith("EOF")


def test_run_inline_lang_and_heredocs(tmp_path: Path):
    pfy = tmp_path / "Pfyfile.pf"
    pfy.write_text(
        """\
task py-inline
  shell [lang:python] print("OK")
end

task py-heredoc
  shell [lang:python] << EOF
print("A")
print("B")
EOF
end

task bash-heredoc
  shell <<'EOF'
echo "HELLO"
EOF
end

task bash-cat-heredoc
  shell_lang bash
  shell cat << 'EOF'
CAT_OK
EOF
end
""",
        encoding="utf-8",
    )

    r1 = _run_pf(["--file", str(pfy), "run", "py-inline"])
    assert r1.returncode == 0, r1.stderr
    assert "OK" in r1.stdout

    r2 = _run_pf(["--file", str(pfy), "run", "py-heredoc"])
    assert r2.returncode == 0, r2.stderr
    assert "A" in r2.stdout and "B" in r2.stdout

    r3 = _run_pf(["--file", str(pfy), "run", "bash-heredoc"])
    assert r3.returncode == 0, r3.stderr
    assert "HELLO" in r3.stdout

    r4 = _run_pf(["--file", str(pfy), "run", "bash-cat-heredoc"])
    assert r4.returncode == 0, r4.stderr
    assert "CAT_OK" in r4.stdout


def test_prune_ignores_shell_bashisms(tmp_path: Path):
    pfy = tmp_path / "Pfyfile.pf"
    pfy.write_text(
        """\
task t
  shell_lang bash
  shell echo "start"; \\
        for i in 1 2; do \\
          echo "$i"; \\
        done
end

task heredoc
  shell cat << 'EOF'
line1
EOF
end
""",
        encoding="utf-8",
    )

    r = _run_pf(["--file", str(pfy), "prune"])
    assert r.returncode == 0, r.stdout + r.stderr
