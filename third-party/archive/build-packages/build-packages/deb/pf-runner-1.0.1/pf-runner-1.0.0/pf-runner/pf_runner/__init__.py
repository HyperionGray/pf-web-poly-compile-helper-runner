"""
pf_runner package shim

This package exposes the existing single-file runner modules so that the
console script entry point `pf_runner.cli:main` resolves correctly when
installed. The actual logic lives in the top-level modules (pf_main.py, etc.).
"""

# Re-export main modules for convenience
from pf_main import main  # noqa: F401
