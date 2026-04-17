import contextlib
import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pf_main import PfRunner
from pf_parser import parse_pfyfile_dependencies


class TestDependencyParsing(unittest.TestCase):
    def test_parses_apt_and_github_dependencies(self):
        deps = parse_pfyfile_dependencies(
            "dep apt curl jq\ndep github HyperionGray/pf-web-poly-compiler-helper\n"
        )
        self.assertEqual(deps["apt"], ["curl", "jq"])
        self.assertEqual(
            deps["pip"],
            ["git+https://github.com/HyperionGray/pf-web-poly-compiler-helper.git"],
        )


class TestDependencyInstall(unittest.TestCase):
    def test_install_declared_dependencies_dry_run(self):
        runner = PfRunner()
        dsl = "dep apt pf-nonexistent-package\ndep github owner/repo\ntask hello\n  shell echo hi\nend\n"
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            rc = runner._install_declared_dependencies(dsl, dry_run=True)
        output = stdout.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("apt-get install -y pf-nonexistent-package", output)
        self.assertIn("pip install git+https://github.com/owner/repo.git", output)

    def test_install_declared_dependencies_installs_only_missing_apt(self):
        runner = PfRunner()
        dsl = "dep apt curl jq\n"
        calls = []

        def fake_check_run(command, **_kwargs):
            if command[:2] == ["dpkg", "-s"]:
                return SimpleNamespace(returncode=(0 if command[-1] == "curl" else 1))
            return SimpleNamespace(returncode=0)

        def fake_install_run(command):
            calls.append(command)
            return 0

        with patch("pf_main.subprocess.run", side_effect=fake_check_run):
            with patch.object(runner, "_run_dependency_command", side_effect=fake_install_run):
                with patch("pf_main.os.geteuid", return_value=0):
                    rc = runner._install_declared_dependencies(dsl, dry_run=False)

        self.assertEqual(rc, 0)
        self.assertIn(["apt-get", "install", "-y", "jq"], calls)


if __name__ == "__main__":
    unittest.main()
