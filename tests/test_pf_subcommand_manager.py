#!/usr/bin/env python3
"""
Unit tests for pf_subcommand_manager.py

Covers:
- _module_name_from_source_file: naming normalization, edge cases
- _pick_module_source: preference for shorter/shallower paths
- _extract_include_files: single-/double-quoted and bare include paths
- _load_include_file: relative and absolute path resolution
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pf-runner-full"))

import pytest

try:
    from pf_subcommand_manager import SubcommandManager
except ImportError:
    pytest.skip("pf_subcommand_manager module not available", allow_module_level=True)


class TestModuleNameFromSourceFile(unittest.TestCase):
    """Tests for SubcommandManager._module_name_from_source_file."""

    def setUp(self):
        self.mgr = SubcommandManager()

    # -- Happy-path cases ---------------------------------------------------

    def test_standard_module_name(self):
        self.assertEqual(
            self.mgr._module_name_from_source_file("/a/b/Pfyfile.web-testing.pf"),
            "web-testing",
        )

    def test_underscores_converted_to_hyphens(self):
        self.assertEqual(
            self.mgr._module_name_from_source_file("/x/Pfyfile.my_module.pf"),
            "my-module",
        )

    def test_case_lowered(self):
        self.assertEqual(
            self.mgr._module_name_from_source_file("/x/Pfyfile.MyMod.pf"),
            "mymod",
        )

    # -- Edge / rejection cases ---------------------------------------------

    def test_none_input(self):
        self.assertIsNone(self.mgr._module_name_from_source_file(None))

    def test_empty_string(self):
        self.assertIsNone(self.mgr._module_name_from_source_file(""))

    def test_main_pfyfile_rejected(self):
        # Pfyfile.pf is the root; should not map to a module.
        self.assertIsNone(self.mgr._module_name_from_source_file("/a/Pfyfile.pf"))

    def test_non_pfyfile_name(self):
        self.assertIsNone(self.mgr._module_name_from_source_file("/a/tasks.pf"))

    def test_wrong_extension(self):
        self.assertIsNone(self.mgr._module_name_from_source_file("/a/Pfyfile.web.txt"))

    def test_module_named_pf_rejected(self):
        # "Pfyfile.pf.pf" -> module name "pf", which is rejected
        self.assertIsNone(self.mgr._module_name_from_source_file("/a/Pfyfile.pf.pf"))


class TestPickModuleSource(unittest.TestCase):
    """Tests for SubcommandManager._pick_module_source."""

    def setUp(self):
        self.mgr = SubcommandManager()

    def test_returns_candidate_when_current_is_none(self):
        result = self.mgr._pick_module_source(None, "/a/b/Pfyfile.x.pf")
        self.assertEqual(result, "/a/b/Pfyfile.x.pf")

    def test_returns_current_when_candidate_is_none(self):
        result = self.mgr._pick_module_source("/a/b/Pfyfile.x.pf", None)
        self.assertEqual(result, "/a/b/Pfyfile.x.pf")

    def test_prefers_shallower_path(self):
        shallow = "/a/Pfyfile.x.pf"
        deep = "/a/b/c/Pfyfile.x.pf"
        self.assertEqual(self.mgr._pick_module_source(deep, shallow), shallow)
        self.assertEqual(self.mgr._pick_module_source(shallow, deep), shallow)

    def test_equal_depth_uses_lexicographic_tiebreak(self):
        a = "/x/alpha.pf"
        b = "/x/bravo.pf"
        result = self.mgr._pick_module_source(a, b)
        self.assertEqual(result, a)


class TestExtractIncludeFiles(unittest.TestCase):
    """Tests for SubcommandManager._extract_include_files."""

    def setUp(self):
        self.mgr = SubcommandManager()

    def test_bare_include(self):
        src = "include path/to/file.pf\n"
        self.assertEqual(self.mgr._extract_include_files(src), ["path/to/file.pf"])

    def test_double_quoted_include(self):
        src = 'include "path/to/file.pf"\n'
        self.assertEqual(self.mgr._extract_include_files(src), ["path/to/file.pf"])

    def test_single_quoted_include(self):
        src = "include 'path/to/file.pf'\n"
        self.assertEqual(self.mgr._extract_include_files(src), ["path/to/file.pf"])

    def test_multiple_includes(self):
        src = "include a.pf\ntask foo\n  shell echo hi\nend\ninclude b.pf\n"
        self.assertEqual(self.mgr._extract_include_files(src), ["a.pf", "b.pf"])

    def test_no_includes(self):
        src = "task foo\n  shell echo hi\nend\n"
        self.assertEqual(self.mgr._extract_include_files(src), [])


class TestLoadIncludeFile(unittest.TestCase):
    """Tests for SubcommandManager._load_include_file."""

    def setUp(self):
        self.mgr = SubcommandManager()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_absolute_path(self):
        fpath = os.path.join(self.tmpdir, "inc.pf")
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("task inc-task\n  shell echo ok\nend\n")

        content = self.mgr._load_include_file(fpath)
        self.assertIn("inc-task", content)

    def test_relative_to_pfyfile(self):
        pfyfile = os.path.join(self.tmpdir, "Pfyfile.pf")
        inc_path = os.path.join(self.tmpdir, "sub", "inc.pf")
        os.makedirs(os.path.dirname(inc_path), exist_ok=True)
        with open(inc_path, "w", encoding="utf-8") as f:
            f.write("task rel-task\n  shell echo ok\nend\n")

        content = self.mgr._load_include_file("sub/inc.pf", pfyfile=pfyfile)
        self.assertIn("rel-task", content)

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.mgr._load_include_file("/nonexistent/file.pf")


if __name__ == "__main__":
    unittest.main()
