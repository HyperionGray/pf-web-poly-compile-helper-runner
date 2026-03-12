#!/usr/bin/env python3
import subprocess
import sys
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PF_MAIN = REPO_ROOT / "pf-runner-full" / "pf_main.py"


def _write_pf(path: Path, task_name: str, message: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        textwrap.dedent(
            f"""
            task {task_name}
              describe Fixture task {task_name}
              shell echo "{message}"
            end
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def _run_pf(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PF_MAIN), *args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )


def _write_pf_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


def test_pf_without_args_lists_default_pfyfile(tmp_path: Path) -> None:
    _write_pf(tmp_path / "Pfyfile.pf", "fixture-default-task", "default-listing")

    result = _run_pf(tmp_path)

    assert result.returncode == 0, result.stderr
    assert "fixture-default-task" in result.stdout


def test_pf_file_only_lists_specified_pfyfile(tmp_path: Path) -> None:
    fixture_file = tmp_path / "fixture-list.pf"
    _write_pf(fixture_file, "fixture-file-task", "file-listing")

    result = _run_pf(tmp_path, str(fixture_file))

    assert result.returncode == 0, result.stderr
    assert "fixture-file-task" in result.stdout


def test_pf_file_and_task_runs_specified_pfyfile(tmp_path: Path) -> None:
    fixture_file = tmp_path / "fixture-run.pf"
    _write_pf(fixture_file, "fixture-run-task", "file-run")

    result = _run_pf(tmp_path, str(fixture_file), "fixture-run-task")

    assert result.returncode == 0, result.stderr
    assert "file-run" in result.stdout


def test_pf_module_stem_resolves_to_pfyfile_module(tmp_path: Path) -> None:
    _write_pf(
        tmp_path / "pf-files" / "Pfyfile.fixture-module.pf",
        "fixture-module-task",
        "module-run",
    )

    list_result = _run_pf(tmp_path, "fixture-module")
    run_result = _run_pf(tmp_path, "fixture-module", "fixture-module-task")

    assert list_result.returncode == 0, list_result.stderr
    assert "fixture-module-task" in list_result.stdout
    assert run_result.returncode == 0, run_result.stderr
    assert "module-run" in run_result.stdout


def test_pf_space_separated_task_name_runs_hyphenated_task(tmp_path: Path) -> None:
    _write_pf_text(
        tmp_path / "Pfyfile.pf",
        """
        task this
          describe Prefix task
          shell echo "prefix-task"
        end

        task this-task
          describe Hyphenated task
          shell echo "hyphenated-task"
        end
        """,
    )

    result = _run_pf(tmp_path, "this", "task")

    assert result.returncode == 0, result.stderr
    assert "hyphenated-task" in result.stdout
    assert "prefix-task" not in result.stdout


def test_pf_task_parameter_variants_are_equivalent(tmp_path: Path) -> None:
    _write_pf_text(
        tmp_path / "Pfyfile.pf",
        """
        task param-task arg1="default"
          describe Parameter parsing fixture
          shell echo "arg1=$arg1"
        end
        """,
    )

    legacy_result = _run_pf(tmp_path, "param-task", "arg1=legacy")
    equals_result = _run_pf(tmp_path, "param-task", "--arg1=equals")
    split_result = _run_pf(tmp_path, "param-task", "--arg1", "split")

    assert legacy_result.returncode == 0, legacy_result.stderr
    assert "arg1=legacy" in legacy_result.stdout
    assert equals_result.returncode == 0, equals_result.stderr
    assert "arg1=equals" in equals_result.stdout
    assert split_result.returncode == 0, split_result.stderr
    assert "arg1=split" in split_result.stdout


def test_pf_split_task_param_can_use_value_that_is_also_a_task_name(tmp_path: Path) -> None:
    _write_pf_text(
        tmp_path / "Pfyfile.pf",
        """
        task param-task arg1="default"
          describe Parameter parsing fixture
          shell echo "arg1=$arg1"
        end

        task other-task
          describe Another task
          shell echo "other-task-ran"
        end
        """,
    )

    result = _run_pf(tmp_path, "param-task", "--arg1", "other-task")

    assert result.returncode == 0, result.stderr
    assert "arg1=other-task" in result.stdout
    assert "other-task-ran" not in result.stdout


def test_pf_two_explicit_tasks_still_run_separately_when_combined_name_exists(tmp_path: Path) -> None:
    _write_pf_text(
        tmp_path / "Pfyfile.pf",
        """
        task first
          describe First task
          shell echo "first-task"
        end

        task second
          describe Second task
          shell echo "second-task"
        end

        task first-second
          describe Combined task
          shell echo "combined-task"
        end
        """,
    )

    result = _run_pf(tmp_path, "first", "second")

    assert result.returncode == 0, result.stderr
    assert "first-task" in result.stdout
    assert "second-task" in result.stdout
    assert "combined-task" not in result.stdout
