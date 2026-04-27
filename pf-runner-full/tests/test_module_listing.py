import contextlib
import io
import tempfile
import textwrap
import unittest
from pathlib import Path

from pf_main import PfRunner
from pf_subcommand_manager import SubcommandManager


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
            self.assertIn("Pfyfile tasks:", output)
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

    def test_subcommand_execution_rejects_out_of_scope_tasks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pfyfile = self._write_pfyfiles(tmpdir)
            stderr = io.StringIO()

            with contextlib.redirect_stderr(stderr):
                rc = PfRunner().run_command(["--file", pfyfile, "alpha", "local-task"])

            error_output = stderr.getvalue()
            self.assertEqual(rc, 1)
            self.assertIn("Task 'local-task' is not available in module 'alpha'.", error_output)
            self.assertIn("alpha-task", error_output)
            self.assertIn("alpha-second", error_output)

    def test_help_command_accepts_module_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pfyfile = self._write_pfyfiles(tmpdir)
            stdout = io.StringIO()

            with contextlib.redirect_stdout(stdout):
                rc = PfRunner().run_command(["--file", pfyfile, "help", "alpha"])

            output = stdout.getvalue()
            self.assertEqual(rc, 0)
            self.assertIn("Tasks for alpha:", output)
            self.assertIn("alpha-task - Alpha task (aliases: at)", output)
            self.assertIn("alpha-second - Alpha second task", output)

    def test_flattened_modules_are_not_registered_as_subcommands(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            pf_files = root / "pf-files"
            always_dir = pf_files / "always-available"
            always_dir.mkdir(parents=True)
            (always_dir / "Pfyfile.always-available.pf").write_text(
                textwrap.dedent(
                    """
                    task shared-task
                      describe Shared root task
                    end
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            root_file = pf_files / "Pfyfile.pf"
            root_file.write_text(
                textwrap.dedent(
                    """
                    task root-task
                      describe Root task
                    end
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            subcommands = SubcommandManager().discover_subcommands(str(root_file))

            registered_files = "\n".join(sorted(subcommands))
            self.assertNotIn("Pfyfile.always-available.pf", registered_files)

    def test_default_tasks_are_summarized_not_mixed_into_pfyfile_section(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            pf_files = root / "pf-files"
            always_dir = pf_files / "always-available"
            always_dir.mkdir(parents=True)
            (always_dir / "Pfyfile.always-available.pf").write_text(
                textwrap.dedent(
                    """
                    task install-tools
                      describe Install helper
                    end
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            root_file = pf_files / "Pfyfile.pf"
            root_file.write_text(
                textwrap.dedent(
                    """
                    task local-task
                      describe Local task
                    end
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                rc = PfRunner().run_command(["--file", str(root_file), "list"])

            output = stdout.getvalue()
            self.assertEqual(rc, 0)
            self.assertIn("Pfyfile tasks:", output)
            self.assertIn("local-task - Local task", output)
            self.assertIn("Default core tasks (summarized):", output)
            self.assertIn("install (", output)
            self.assertNotIn("install-tools - Install helper", output)

    def test_task_category_summary_groups_by_prefix_and_misc(self):
        runner = PfRunner()
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            runner._print_task_category_summary(
                [
                    ("web-build", "Build web", []),
                    ("web-test", "Test web", []),
                    ("standalone", "No hyphen task", []),
                ]
            )

        output = stdout.getvalue()
        self.assertIn("web (2 tasks)", output)
        self.assertIn("misc (1 task)", output)


if __name__ == "__main__":
    unittest.main()
