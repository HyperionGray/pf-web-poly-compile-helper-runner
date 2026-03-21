#!/usr/bin/env python3
"""Tests for TUI screenshot demo script and compatibility wrapper."""

from __future__ import annotations

import importlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SCREENSHOT_SCRIPT = REPO_ROOT / "demos" / "screenshot_tui.py"
ROOT_WRAPPER_SCRIPT = REPO_ROOT / "screenshot_tui.py"


def test_screenshot_script_locations_exist() -> None:
    assert CANONICAL_SCREENSHOT_SCRIPT.exists(), "demos/screenshot_tui.py should exist"
    assert ROOT_WRAPPER_SCRIPT.exists(), "root wrapper screenshot_tui.py should exist"


def test_root_wrapper_exports_expected_entrypoints() -> None:
    module = importlib.import_module("screenshot_tui")
    assert hasattr(module, "show_menu_screenshot")
    assert callable(module.show_menu_screenshot)
    assert hasattr(module, "main")
    assert callable(module.main)


def test_screenshot_demo_returns_error_when_dependencies_fail(monkeypatch) -> None:
    module = importlib.import_module("demos.screenshot_tui")

    def fail_loader(_runner_path=None):
        raise RuntimeError("missing dependencies")

    monkeypatch.setattr(module, "_load_dependencies", fail_loader)
    rc = module.show_menu_screenshot()
    assert rc == 1


def test_show_menu_screenshot_runs_with_mocked_dependencies(monkeypatch) -> None:
    module = importlib.import_module("demos.screenshot_tui")

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
            self.tasks = {"a": object(), "b": object(), "c": object()}
            self.categories = []
            self.header_rendered = False

        def load_tasks(self):
            return True

        def categorize_tasks(self):
            self.categories = [
                FakeCategory("Core Tasks", [("build", "Build project")]),
                FakeCategory("Testing", [("test", "Run tests")]),
            ]

        def show_header(self):
            self.header_rendered = True

    monkeypatch.setattr(
        module,
        "_load_dependencies",
        lambda _runner_path=None: Path("/tmp/pf-runner-full"),
    )
    monkeypatch.setattr(module, "Console", FakeConsole)
    monkeypatch.setattr(module, "PfTUI", FakeTUI)

    rc = module.show_menu_screenshot(pfyfile="Pfyfile.pf")
    assert rc == 0


def test_show_menu_main_parses_cli_options(monkeypatch) -> None:
    module = importlib.import_module("demos.screenshot_tui")
    captured = {}

    def fake_show_menu_screenshot(pfyfile=None, runner_path=None):
        captured["pfyfile"] = pfyfile
        captured["runner_path"] = runner_path
        return 0

    monkeypatch.setattr(module, "show_menu_screenshot", fake_show_menu_screenshot)
    rc = module.main(["--file", "custom.pf", "--runner-path", "/tmp/runner"])
    assert rc == 0
    assert captured["pfyfile"] == "custom.pf"
    assert captured["runner_path"] == "/tmp/runner"
