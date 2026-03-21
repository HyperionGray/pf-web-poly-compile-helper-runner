#!/usr/bin/env python3
"""Compatibility wrapper for demos/screenshot_tui.py."""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from demos.screenshot_tui import main, show_menu_screenshot


if __name__ == "__main__":
    raise SystemExit(main())
