#!/usr/bin/env python3
"""Backward-compatible wrapper for demos/screenshot_tui.py."""

from demos.screenshot_tui import main, show_menu_screenshot

__all__ = ["show_menu_screenshot", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
