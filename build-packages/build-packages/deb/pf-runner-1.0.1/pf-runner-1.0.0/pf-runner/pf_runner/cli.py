"""
Console entrypoint wrapper for pf.

Keeps the published script target `pf_runner.cli:main` stable while the
implementation lives in the top-level `pf_main.py`.
"""

from pf_main import main as _main


def main() -> int:
    return _main()


if __name__ == "__main__":
    raise SystemExit(main())
