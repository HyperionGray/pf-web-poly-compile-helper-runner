#!/usr/bin/env python3
"""
Backward-compatible wrapper for the canonical demos/screenshot_tui.py script.
"""

from demos import screenshot_tui as _screenshot_module

# Compatibility exports (tests patch these symbols on this module).
PfTUI = _screenshot_module.PfTUI
Console = _screenshot_module.Console

def show_menu_screenshot() -> None:
    """Run the screenshot demo via the canonical demos module."""
    _screenshot_module.PfTUI = PfTUI
    _screenshot_module.Console = Console
    _screenshot_module.show_menu_screenshot()


if __name__ == "__main__":
    show_menu_screenshot()
