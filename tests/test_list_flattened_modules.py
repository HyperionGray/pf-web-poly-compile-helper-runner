import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PF_RUNNER_DIR = REPO_ROOT / "pf-runner"
PF_MAIN = PF_RUNNER_DIR / "pf_main.py"


def _run_pf(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{PF_RUNNER_DIR}{os.pathsep}{env.get('PYTHONPATH', '')}"
    return subprocess.run(
        [sys.executable, str(PF_MAIN), *args],
        cwd=str(cwd or REPO_ROOT),
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )


def test_list_subcommand_supports_flattened_always_available_module():
    result = _run_pf(["list", "--subcommand", "always-available"])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Tasks for always-available:" in result.stdout
    assert "always-available-help" in result.stdout


def test_list_subcommand_normalizes_underscores_for_flattened_module_names():
    result = _run_pf(["list", "--subcommand", "module_compat"])
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Tasks for module-compat:" in result.stdout
    assert "module-help" in result.stdout
