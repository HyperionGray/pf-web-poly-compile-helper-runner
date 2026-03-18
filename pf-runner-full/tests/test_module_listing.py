import contextlib
import io
import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from pf_main import PfRunner


class TestModuleListing(unittest.TestCase):
    def _write_pfyfiles(self, tmpdir: str) -> str:
        root = Path(tmpdir)
        main_file = root / "Pfyfile.pf"
        alpha_file = root / "Pfyfile.alpha.pf"
        nested_dir = root / "nested"
        nested_dir.mkdir()
        beta_file = nested_dir / "Pfyfile.beta_tools.pf"

        main_file.write_text(
            textwrap.dedent(
                """
                include "Pfyfile.alpha.pf"
                include "nested/Pfyfile.beta_tools.pf"

                task local-task
                  describe Local task
                end

                task local-alias [alias lt]
                  describe Local alias task
                end
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        alpha_file.write_text(
            textwrap.dedent(
                """
                task alpha-task [alias at]
                  describe Alpha task
                end

                task alpha-second
                  describe Alpha second task
                end
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )
        beta_file.write_text(
            textwrap.dedent(
                """
                task beta-task
                  describe Beta task
                end
                """
            ).strip()
            + "\n",
            encoding="utf-8",
        )

        return str(main_file)

    def test_default_list_collapses_modules(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pfyfile = self._write_pfyfiles(tmpdir)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                rc = PfRunner().run_command(["--file", pfyfile, "list"])

            output = stdout.getvalue()
            self.assertEqual(rc, 0)
            self.assertIn("Core tasks:", output)
            self.assertIn("local-task - Local task", output)
            self.assertIn("local-alias - Local alias task (aliases: lt)", output)
            self.assertIn("Modules:", output)
            self.assertIn("alpha (2 tasks)", output)
            self.assertIn("beta-tools (1 task)", output)
            self.assertNotIn("alpha-task - Alpha task", output)
            self.assertNotIn("beta-task - Beta task", output)

    def test_subcommand_list_shows_module_tasks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pfyfile = self._write_pfyfiles(tmpdir)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                rc = PfRunner().run_command(["--file", pfyfile, "list", "--subcommand", "alpha"])

            output = stdout.getvalue()
            self.assertEqual(rc, 0)
            self.assertIn("Tasks for alpha:", output)
            self.assertIn("alpha-task - Alpha task (aliases: at)", output)
            self.assertIn("alpha-second - Alpha second task", output)
            self.assertNotIn("local-task", output)
            self.assertNotIn("beta-task", output)

    def test_default_list_json_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pfyfile = self._write_pfyfiles(tmpdir)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                rc = PfRunner().run_command(["--file", pfyfile, "list", "--json"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(rc, 0)
            self.assertGreaterEqual(payload["total_tasks"], 4)
            self.assertIn("core_tasks", payload)
            self.assertIn("modules", payload)

            core_names = {entry["name"] for entry in payload["core_tasks"]}
            self.assertIn("local-task", core_names)
            self.assertIn("local-alias", core_names)
            self.assertIn("alpha", payload["modules"])
            self.assertIn("beta-tools", payload["modules"])

    def test_subcommand_list_json_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pfyfile = self._write_pfyfiles(tmpdir)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                rc = PfRunner().run_command(
                    ["--file", pfyfile, "list", "--subcommand", "alpha", "--json"]
                )

            payload = json.loads(stdout.getvalue())
            self.assertEqual(rc, 0)
            self.assertEqual(payload["subcommand"], "alpha")
            self.assertEqual(
                {entry["name"] for entry in payload["tasks"]},
                {"alpha-task", "alpha-second"},
            )


if __name__ == "__main__":
    unittest.main()
