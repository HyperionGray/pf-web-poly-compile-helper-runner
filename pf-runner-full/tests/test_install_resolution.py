import os
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from pf_main import PfRunner
from pf_parser import (
    BUILTINS,
    _find_pfyfile,
    _load_pfy_source_with_includes,
    parse_pfyfile_text,
)
from pfuck import PfAutocorrect


class TestInstallResolution(unittest.TestCase):
    def test_default_lookup_prefers_pf_files_entrypoint_from_nested_dir(self):
        repo_root = Path(__file__).resolve().parents[2]
        nested_dir = repo_root / "tools" / "injection"

        resolved = Path(_find_pfyfile(start_dir=str(nested_dir))).resolve()

        self.assertEqual(resolved, (repo_root / "pf-files" / "Pfyfile.pf").resolve())

    def test_local_lookup_beats_installed_default_file_hint(self):
        repo_root = Path(__file__).resolve().parents[2]
        nested_dir = repo_root / "tools" / "injection"

        with tempfile.TemporaryDirectory() as temp_dir:
            fallback = Path(temp_dir) / "Pfyfile.pf"
            fallback.write_text("task installed-default\nend\n", encoding="utf-8")

            with mock.patch.dict(os.environ, {"PFY_DEFAULT_FILE": str(fallback)}, clear=False):
                resolved = Path(_find_pfyfile(start_dir=str(nested_dir))).resolve()

        self.assertEqual(resolved, (repo_root / "pf-files" / "Pfyfile.pf").resolve())

    def test_installed_default_file_hint_is_used_when_no_local_pfyfile_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            fallback = temp_root / "Pfyfile.pf"
            fallback.write_text("task installed-default\nend\n", encoding="utf-8")
            empty_dir = temp_root / "empty"
            empty_dir.mkdir()

            with mock.patch.dict(os.environ, {"PFY_DEFAULT_FILE": str(fallback)}, clear=False):
                resolved = Path(_find_pfyfile(start_dir=str(empty_dir))).resolve()

        self.assertEqual(resolved, fallback.resolve())

    def test_explicit_file_load_refreshes_environment_hints(self):
        repo_root = Path(__file__).resolve().parents[2]
        pe_pfy = (repo_root / "pf-files" / "Pfyfile.pe.pf").resolve()

        with mock.patch.dict(
            os.environ,
            {"PFY_FILE_PATH": "/tmp/stale/Pfyfile.pf", "PFY_ROOT": "/tmp/stale"},
            clear=False,
        ):
            _load_pfy_source_with_includes(file_arg=str(pe_pfy))

            self.assertEqual(Path(os.environ["PFY_FILE_PATH"]).resolve(), pe_pfy)
            self.assertEqual(Path(os.environ["PFY_ROOT"]).resolve(), pe_pfy.parent)


    def test_root_install_task_exists_and_resolves_without_autocorrect(self):
        repo_root = Path(__file__).resolve().parents[2]
        root_pfy = repo_root / "pf-files" / "Pfyfile.pf"

        dsl_src, task_sources = _load_pfy_source_with_includes(file_arg=str(root_pfy))
        dsl_tasks = parse_pfyfile_text(dsl_src, task_sources)

        self.assertIn("install", dsl_tasks)
        self.assertIn("install-all", dsl_tasks)

        runner = PfRunner()
        runner.autocorrect = PfAutocorrect(str(root_pfy))
        valid_task_names = set(BUILTINS.keys()) | set(dsl_tasks.keys())
        task_name_lookup = runner._build_task_name_lookup(valid_task_names)

        resolved = runner._resolve_task_name("install", valid_task_names, task_name_lookup)
        self.assertEqual(resolved, "install")


if __name__ == "__main__":
    unittest.main()
