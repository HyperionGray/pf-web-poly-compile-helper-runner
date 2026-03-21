#!/usr/bin/env python3
"""Compatibility wrapper for demos/demo_tui.py."""

from __future__ import annotations

from demos.demo_tui import demo_tui, main

__all__ = ["demo_tui", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
