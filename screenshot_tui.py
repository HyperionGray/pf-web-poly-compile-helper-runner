#!/usr/bin/env python3
"""
Compatibility wrapper for demos/screenshot_tui.py.
"""

from __future__ import annotations

from typing import Optional, Sequence

import demos.screenshot_tui as _impl

# Re-export symbols used by existing tests and callers.
Console = _impl.Console
PfTUI = _impl.PfTUI


def show_menu_screenshot(
    output_path: Optional[str] = None,
    snapshot_format: str = "text",
    pfyfile: Optional[str] = None,
) -> int:
    """Render a TUI snapshot, optionally saving it to a file."""
    _impl.Console = Console
    _impl.PfTUI = PfTUI
    return _impl.show_menu_screenshot(
        output_path=output_path,
        snapshot_format=snapshot_format,
        pfyfile=pfyfile,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point for compatibility script."""
    _impl.Console = Console
    _impl.PfTUI = PfTUI
    return _impl.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
