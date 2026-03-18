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


def _run_pf(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PF_MAIN), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def _write_hyphen_module_fixture(tmp_path: Path) -> None:
    _write_pf(
        tmp_path / "pf-files" / "Pfyfile.pf",
        """
        include Pfyfile.my-module.pf

        task root-task
          describe Root task
          shell echo "root"
        end
        """,
    )
    _write_pf(
        tmp_path / "pf-files" / "Pfyfile.my-module.pf",
        """
        task mod-usage
          describe Usage task in a hyphenated module
          shell echo "module-alias-ok"
        end
        """,
    )


def test_explicit_module_listing_excludes_always_available_tasks(tmp_path: Path) -> None:
    _write_pf(
        tmp_path / "pf-files" / "always-available" / "Pfyfile.always-available.pf",
        """
        task shared-task
          describe Shared task that should stay off explicit module listings
          shell echo "shared"
        end
        """,
    )
    _write_pf(
        tmp_path / "pf-files" / "Pfyfile.widget.pf",
        """
        task widget-task
          describe Public task for the widget module
          shell echo "widget"
        end
        """,
    )

    result = _run_pf(tmp_path, "widget")

    assert result.returncode == 0, result.stderr
    assert "widget-task" in result.stdout
    assert "shared-task" not in result.stdout


def test_root_listing_still_includes_always_available_tasks(tmp_path: Path) -> None:
    _write_pf(
        tmp_path / "pf-files" / "always-available" / "Pfyfile.always-available.pf",
        """
        task shared-task
          describe Shared task that should remain on the root surface
          shell echo "shared"
        end
        """,
    )
    _write_pf(
        tmp_path / "pf-files" / "Pfyfile.pf",
        """
        task root-task
          describe Root task
          shell echo "root"
        end
        """,
    )

    result = _run_pf(tmp_path)

    assert result.returncode == 0, result.stderr
    assert "root-task" in result.stdout
    assert "shared-task" in result.stdout


def test_module_alias_with_underscore_lists_hyphenated_subcommand(tmp_path: Path) -> None:
    _write_hyphen_module_fixture(tmp_path)

    result = _run_pf(tmp_path, "my_module")

    assert result.returncode == 0, result.stderr
    assert "mod-usage" in result.stdout
    assert "Auto-corrected" not in result.stderr


def test_module_alias_with_underscore_runs_hyphenated_subcommand_task(tmp_path: Path) -> None:
    _write_hyphen_module_fixture(tmp_path)

    result = _run_pf(tmp_path, "my_module", "mod-usage")

    assert result.returncode == 0, result.stderr
    assert "module-alias-ok" in result.stdout
    assert "Auto-corrected" not in result.stderr


def test_list_subcommand_accepts_underscore_module_alias(tmp_path: Path) -> None:
    _write_hyphen_module_fixture(tmp_path)

    result = _run_pf(tmp_path, "list", "--subcommand", "my_module")

    assert result.returncode == 0, result.stderr
    assert "Tasks for my-module:" in result.stdout
    assert "mod-usage" in result.stdout


def test_repo_pe_module_lists_local_surface_only() -> None:
    result = _run_pf(REPO_ROOT, "pe")

    assert result.returncode == 0, result.stderr
    assert "install" in result.stdout
    assert "execute" in result.stdout
    assert "build-all" in result.stdout
    assert "pe-execute" not in result.stdout
    assert "always-available-help" not in result.stdout


def test_repo_pe_module_usage_task_runs() -> None:
    result = _run_pf(REPO_ROOT, "pe", "usage")

    assert result.returncode == 0, result.stderr
    assert "pf pe install" in result.stdout
    assert "pf pe execute pe_file=/path/to/app.exe" in result.stdout


def test_repo_web_module_lists_local_surface_only() -> None:
    result = _run_pf(REPO_ROOT, "web")

    assert result.returncode == 0, result.stderr
    assert "ambiguous" not in result.stderr
    assert "install" in result.stdout
    assert "usage" in result.stdout
    assert "build-rust" in result.stdout
    assert "api-server" in result.stdout
    assert "web-dev" not in result.stdout
    assert "always-available-help" not in result.stdout


def test_repo_web_module_usage_task_runs() -> None:
    result = _run_pf(REPO_ROOT, "web", "usage")

    assert result.returncode == 0, result.stderr
    assert "pf web install" in result.stdout
    assert "pf web dev" in result.stdout


def test_repo_security_module_lists_local_surface_only() -> None:
    result = _run_pf(REPO_ROOT, "security")

    assert result.returncode == 0, result.stderr
    assert "ambiguous" not in result.stderr
    assert "install" in result.stdout
    assert "scan" in result.stdout
    assert "fuzz" in result.stdout
    assert "checksec" in result.stdout
    assert "security-scan" not in result.stdout
    assert "smart-scan" not in result.stdout
    assert "always-available-help" not in result.stdout


def test_repo_security_module_usage_task_runs() -> None:
    result = _run_pf(REPO_ROOT, "security", "usage")

    assert result.returncode == 0, result.stderr
    assert "pf security install" in result.stdout
    assert "pf security scan" in result.stdout


def test_repo_root_lists_compat_surface_without_internal_module_leaks() -> None:
    result = _run_pf(REPO_ROOT)

    assert result.returncode == 0, result.stderr
    assert "module-help" in result.stdout
    assert "install-module-web" in result.stdout
    assert "install-module-security" in result.stdout
    assert "install-module-pe" in result.stdout
    assert "pe-help" in result.stdout
    assert "security-help" in result.stdout
    assert "web-dev" in result.stdout
    assert "build-rust" not in result.stdout
    assert "pe-build-windows-server" not in result.stdout
    assert "security-scan-json" not in result.stdout
    assert "security-assess-comprehensive" not in result.stdout


def test_repo_root_pe_help_wrapper_runs() -> None:
    result = _run_pf(REPO_ROOT, "pe-help")

    assert result.returncode == 0, result.stderr
    assert "pf pe execute pe_file=/path/to/app.exe" in result.stdout


def test_repo_root_security_help_wrapper_runs() -> None:
    result = _run_pf(REPO_ROOT, "security-help")

    assert result.returncode == 0, result.stderr
    assert "pf security scan" in result.stdout

def test_repo_module_help_mentions_module_install_paths() -> None:
    result = _run_pf(REPO_ROOT, "module-help")

    assert result.returncode == 0, result.stderr
    assert "pf web install" in result.stdout
    assert "pf security install" in result.stdout
    assert "pf pe install" in result.stdout


def test_repo_unified_security_requires_explicit_file() -> None:
    unified_file = REPO_ROOT / "pf-files" / "vuln-hunting" / "Pfyfile.unified-security.pf"
    result = _run_pf(REPO_ROOT, str(unified_file))

    assert result.returncode == 0, result.stderr
    assert "security-assess-comprehensive" in result.stdout
