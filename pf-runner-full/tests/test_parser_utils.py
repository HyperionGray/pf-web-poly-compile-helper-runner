"""Tests for pf_parser utility functions.

Covers: _normalize_hosts, _merge_env_hosts, _dedupe_preserve_order,
        _parse_host, list_dsl_tasks_with_desc, get_alias_map
"""

import os
import tempfile
import textwrap
import unittest
from pathlib import Path

from pf_parser import (
    _normalize_hosts,
    _merge_env_hosts,
    _dedupe_preserve_order,
    _parse_host,
    list_dsl_tasks_with_desc,
    get_alias_map,
)


class TestNormalizeHosts(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual(_normalize_hosts([]), [])

    def test_single_host(self):
        self.assertEqual(_normalize_hosts(["host1"]), ["host1"])

    def test_deduplicates_hosts(self):
        result = _normalize_hosts(["host1", "host2", "host1"])
        self.assertEqual(result, ["host1", "host2"])

    def test_filters_empty_strings(self):
        result = _normalize_hosts(["host1", "", "host2"])
        self.assertNotIn("", result)
        self.assertIn("host1", result)
        self.assertIn("host2", result)

    def test_preserves_order(self):
        result = _normalize_hosts(["b", "a", "c"])
        self.assertEqual(result, ["b", "a", "c"])


class TestDedupePreserveOrder(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual(_dedupe_preserve_order([]), [])

    def test_no_duplicates(self):
        self.assertEqual(_dedupe_preserve_order(["a", "b", "c"]), ["a", "b", "c"])

    def test_removes_duplicates(self):
        result = _dedupe_preserve_order(["a", "b", "a", "c", "b"])
        self.assertEqual(result, ["a", "b", "c"])

    def test_preserves_first_occurrence_order(self):
        result = _dedupe_preserve_order(["z", "a", "z", "m"])
        self.assertEqual(result, ["z", "a", "m"])


class TestMergeEnvHosts(unittest.TestCase):
    def test_unknown_env_names_return_empty(self):
        result = _merge_env_hosts(["PF_NONEXISTENT_ENV_XYZ"])
        self.assertEqual(result, [])

    def test_empty_env_names(self):
        result = _merge_env_hosts([])
        self.assertEqual(result, [])


class TestParseHost(unittest.TestCase):
    def test_local_shorthand(self):
        spec = _parse_host("@local")
        self.assertEqual(spec["host"], "localhost")
        self.assertTrue(spec["local"])

    def test_simple_hostname(self):
        spec = _parse_host("myhost")
        self.assertEqual(spec["host"], "myhost")
        self.assertFalse(spec["local"])

    def test_user_at_host(self):
        spec = _parse_host("user@myhost")
        self.assertEqual(spec["user"], "user")
        self.assertEqual(spec["host"], "myhost")
        self.assertFalse(spec["local"])

    def test_host_with_port(self):
        spec = _parse_host("myhost:2222")
        self.assertEqual(spec["host"], "myhost")
        self.assertEqual(spec["port"], 2222)

    def test_user_host_port(self):
        spec = _parse_host("admin@myhost:2222")
        self.assertEqual(spec["user"], "admin")
        self.assertEqual(spec["host"], "myhost")
        self.assertEqual(spec["port"], 2222)

    def test_default_user_applied(self):
        spec = _parse_host("myhost", default_user="deploy")
        self.assertEqual(spec["user"], "deploy")

    def test_default_port_applied(self):
        spec = _parse_host("myhost", default_port=22)
        self.assertEqual(spec["port"], 22)

    def test_explicit_user_overrides_default(self):
        spec = _parse_host("other@myhost", default_user="deploy")
        self.assertEqual(spec["user"], "other")


class TestListDslTasksWithDesc(unittest.TestCase):
    def _make_pfyfile(self, content: str):
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".pf", delete=False, encoding="utf-8"
        )
        f.write(content)
        f.flush()
        f.close()
        return f.name

    def tearDown(self):
        for attr in ("_pfyfile",):
            path = getattr(self, attr, None)
            if path and Path(path).exists():
                os.unlink(path)

    def test_returns_task_names(self):
        path = self._make_pfyfile(
            textwrap.dedent(
                """
                task build
                  describe Build the project
                end

                task test
                  describe Run tests
                end
                """
            ).strip()
            + "\n"
        )
        self._pfyfile = path
        tasks = list_dsl_tasks_with_desc(file_arg=path)
        names = [t[0] for t in tasks]
        self.assertIn("build", names)
        self.assertIn("test", names)

    def test_includes_descriptions(self):
        path = self._make_pfyfile(
            textwrap.dedent(
                """
                task greet
                  describe Say hello
                end
                """
            ).strip()
            + "\n"
        )
        self._pfyfile = path
        tasks = list_dsl_tasks_with_desc(file_arg=path)
        greet = next((t for t in tasks if t[0] == "greet"), None)
        self.assertIsNotNone(greet)
        self.assertEqual(greet[1], "Say hello")

    def test_includes_aliases(self):
        path = self._make_pfyfile(
            textwrap.dedent(
                """
                task deploy [alias d]
                  describe Deploy
                end
                """
            ).strip()
            + "\n"
        )
        self._pfyfile = path
        tasks = list_dsl_tasks_with_desc(file_arg=path)
        deploy = next((t for t in tasks if t[0] == "deploy"), None)
        self.assertIsNotNone(deploy)
        self.assertIn("d", deploy[2])

    def test_empty_pfyfile_returns_empty(self):
        path = self._make_pfyfile("")
        self._pfyfile = path
        tasks = list_dsl_tasks_with_desc(file_arg=path)
        self.assertEqual(tasks, [])

    def test_nonexistent_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            list_dsl_tasks_with_desc(file_arg="/tmp/pf_nonexistent_xyz.pf")


class TestGetAliasMap(unittest.TestCase):
    def _make_pfyfile(self, content: str):
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".pf", delete=False, encoding="utf-8"
        )
        f.write(content)
        f.flush()
        f.close()
        return f.name

    def tearDown(self):
        for attr in ("_pfyfile",):
            path = getattr(self, attr, None)
            if path and Path(path).exists():
                os.unlink(path)

    def test_alias_maps_to_task(self):
        path = self._make_pfyfile(
            textwrap.dedent(
                """
                task my-task [alias mt]
                  describe My task
                end
                """
            ).strip()
            + "\n"
        )
        self._pfyfile = path
        alias_map = get_alias_map(file_arg=path)
        self.assertIn("mt", alias_map)
        self.assertEqual(alias_map["mt"], "my-task")

    def test_no_aliases_returns_empty_map(self):
        path = self._make_pfyfile(
            textwrap.dedent(
                """
                task plain
                  describe No aliases
                end
                """
            ).strip()
            + "\n"
        )
        self._pfyfile = path
        alias_map = get_alias_map(file_arg=path)
        self.assertEqual(alias_map, {})

    def test_nonexistent_file_returns_empty(self):
        alias_map = get_alias_map(file_arg="/tmp/pf_nonexistent_xyz.pf")
        self.assertEqual(alias_map, {})

    def test_multiple_aliases(self):
        path = self._make_pfyfile(
            textwrap.dedent(
                """
                task build [alias b]
                  describe Build
                end

                task test [alias t]
                  describe Test
                end
                """
            ).strip()
            + "\n"
        )
        self._pfyfile = path
        alias_map = get_alias_map(file_arg=path)
        self.assertIn("b", alias_map)
        self.assertIn("t", alias_map)
        self.assertEqual(alias_map["b"], "build")
        self.assertEqual(alias_map["t"], "test")


if __name__ == "__main__":
    unittest.main()
