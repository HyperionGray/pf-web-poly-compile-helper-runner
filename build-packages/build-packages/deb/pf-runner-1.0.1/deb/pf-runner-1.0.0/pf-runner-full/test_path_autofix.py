#!/usr/bin/env python3
"""Regression checks for pf path autofix.

This is intentionally lightweight (no pytest dependency). Run with:
  python pf-runner/test_path_autofix.py
"""

import os
import tempfile
import unittest

import pf_main


class TestPathAutofix(unittest.TestCase):
    def test_generates_corrected_shell_script_next_to_original(self):
        runner = pf_main.PfRunner()
        runner.config = {
            "runner": {
                "pathAutofix": True,
                "pathAutofixWriteCorrectedNextToScript": True,
            }
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = tmp
            sub = os.path.join(root, "sub")
            scripts = os.path.join(root, "scripts")
            os.makedirs(sub, exist_ok=True)
            os.makedirs(scripts, exist_ok=True)

            helpers = os.path.join(scripts, "helpers.sh")
            demo = os.path.join(scripts, "demo.sh")

            with open(helpers, "w", encoding="utf-8") as fh:
                fh.write("#!/usr/bin/env bash\n")
                fh.write("set -euo pipefail\n")
                fh.write("echo helper\n")

            with open(demo, "w", encoding="utf-8") as fh:
                fh.write("#!/usr/bin/env bash\n")
                fh.write("set -euo pipefail\n")
                fh.write("source ./helpers.sh\n")
                fh.write("echo demo\n")

            os.chmod(helpers, 0o755)
            os.chmod(demo, 0o755)

            cmd, cwd_override, warnings = runner._autofix_shell_command_context(
                "bash scripts/demo.sh", invocation_cwd=root, task_cwd=sub
            )

            self.assertIsNone(cwd_override)
            self.assertIn("demo.sh.corrected", cmd)
            self.assertTrue(any("generated corrected script" in w for w in warnings))

            corrected = demo + ".corrected"
            self.assertTrue(os.path.exists(corrected))

            with open(corrected, "r", encoding="utf-8") as fh:
                corrected_text = fh.read()
            self.assertIn("pf-path-autofix", corrected_text)
            # Should rewrite the source path to an absolute path.
            self.assertIn(os.path.abspath(helpers), corrected_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
