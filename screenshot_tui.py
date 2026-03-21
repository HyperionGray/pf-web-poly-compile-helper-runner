#!/usr/bin/env python3
"""Compatibility wrapper for demos/screenshot_tui.py."""

from __future__ import annotations

from demos.screenshot_tui import main, show_menu_screenshot

__all__ = ["show_menu_screenshot", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
