#!/usr/bin/env python3
"""
pf_main.py - Thin entrypoint wrapper for pf.

This module preserves the original import path for PfRunner and console_scripts
while delegating implementation to pf_runner_core.
"""

from typing import List

from pf_runner_core import PfRunner as PfRunner
from pf_runner_core import main as _core_main


def main(argv: List[str]) -> int:
    """Main entry point for enhanced pf."""
    return _core_main(argv)


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv[1:]))
