#!/usr/bin/env python3
"""
Backward-compatible wrapper for the canonical demos/demo_tui.py script.
"""

from demos import demo_tui as _demo_module

# Compatibility exports (tests patch these symbols on this module).
PfTUI = _demo_module.PfTUI
Console = _demo_module.Console

def demo_tui() -> None:
    """Run the demo via the canonical demos module."""
    _demo_module.PfTUI = PfTUI
    _demo_module.Console = Console
    _demo_module.demo_tui()


if __name__ == "__main__":
    demo_tui()
