#!/usr/bin/env python3
"""Tests for TUI demo scripts and compatibility wrappers."""

from __future__ import annotations

import importlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DEMO_SCRIPT = REPO_ROOT / "demos" / "demo_tui.py"
ROOT_WRAPPER_SCRIPT = REPO_ROOT / "demo_tui.py"


def test_demo_tui_script_locations_exist() -> None:
    assert CANONICAL_DEMO_SCRIPT.exists(), "demos/demo_tui.py should exist"
    assert ROOT_WRAPPER_SCRIPT.exists(), "root wrapper demo_tui.py should exist"


def test_root_wrapper_exports_expected_entrypoints() -> None:
    module = importlib.import_module("demo_tui")
    assert hasattr(module, "demo_tui")
    assert callable(module.demo_tui)
    assert hasattr(module, "main")
    assert callable(module.main)


def test_demo_tui_returns_error_when_dependencies_fail(monkeypatch) -> None:
    module = importlib.import_module("demos.demo_tui")

    def fail_loader(_runner_path=None):
        raise RuntimeError("missing dependencies")

    monkeypatch.setattr(module, "_load_dependencies", fail_loader)
    rc = module.demo_tui()
    assert rc == 1


def test_demo_tui_summary_runs_with_mocked_dependencies(monkeypatch) -> None:
    module = importlib.import_module("demos.demo_tui")

    class FakeConsole:
        def __init__(self):
            self.lines = []

        def print(self, message):
            self.lines.append(str(message))

    class FakeCategory:
        def __init__(self, name, tasks):
            self.name = name
            self.tasks = tasks

    class FakeTUI:
        def __init__(self, pfyfile):
            self.pfyfile = pfyfile
            self.tasks = {"a": object(), "b": object()}
            self.categories = []

        def load_tasks(self):
            return True

        def categorize_tasks(self):
            self.categories = [
                FakeCategory("Core Tasks", [("build", "Build project")]),
                FakeCategory("Testing", [("test", "Run tests")]),
            ]

    monkeypatch.setattr(
        module,
        "_load_dependencies",
        lambda _runner_path=None: Path("/tmp/pf-runner-full"),
    )
    monkeypatch.setattr(module, "Console", FakeConsole)
    monkeypatch.setattr(module, "PfTUI", FakeTUI)

    rc = module.demo_tui(pfyfile="Pfyfile.pf")
    assert rc == 0


def test_demo_tui_main_parses_cli_options(monkeypatch) -> None:
    module = importlib.import_module("demos.demo_tui")
    captured = {}

    def fake_demo_tui(pfyfile=None, runner_path=None):
        captured["pfyfile"] = pfyfile
        captured["runner_path"] = runner_path
        return 0

    monkeypatch.setattr(module, "demo_tui", fake_demo_tui)
    rc = module.main(["--file", "custom.pf", "--runner-path", "/tmp/runner"])
    assert rc == 0
    assert captured["pfyfile"] == "custom.pf"
    assert captured["runner_path"] == "/tmp/runner"
