#!/usr/bin/env python3
"""Backward-compatible wrapper for demos/demo_tui.py."""

from demos.demo_tui import demo_tui, main

__all__ = ["demo_tui", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
