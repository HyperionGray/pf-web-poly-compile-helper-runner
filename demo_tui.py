#!/usr/bin/env python3
"""
Compatibility wrapper for demos/demo_tui.py.
"""

from __future__ import annotations

from typing import Optional, Sequence

import demos.demo_tui as _impl

# Re-export symbols used by existing tests and callers.
Console = _impl.Console
PfTUI = _impl.PfTUI


def demo_tui(pfyfile: Optional[str] = None) -> int:
    """Run non-interactive TUI demo."""
    _impl.Console = Console
    _impl.PfTUI = PfTUI
    return _impl.demo_tui(pfyfile=pfyfile)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point for compatibility script."""
    _impl.Console = Console
    _impl.PfTUI = PfTUI
    return _impl.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
