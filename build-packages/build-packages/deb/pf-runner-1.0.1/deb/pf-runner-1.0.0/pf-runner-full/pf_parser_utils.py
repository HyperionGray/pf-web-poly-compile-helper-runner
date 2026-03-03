#!/usr/bin/env python3
"""
pf_parser_utils.py - small shared helpers for pf parser.
"""

import os
import re
from typing import Optional


# ---------- Interpolation ----------
_VAR_RE = re.compile(r"\$([a-zA-Z_][\w-]*)|\$\{([a-zA-Z_][\w-]*)\}")


def _interpolate(text: str, params: dict, extra_env: Optional[dict] = None) -> str:
    merged = dict(os.environ)
    if extra_env:
        merged.update(extra_env)
    merged.update(params or {})

    def repl(m):
        key = m.group(1) or m.group(2)
        return str(merged.get(key, m.group(0)))

    return _VAR_RE.sub(repl, text)
