#!/usr/bin/env python3
import subprocess
import sys


def main() -> int:
    binary = sys.argv[1] if len(sys.argv) > 1 else "demos/practice-binaries/format-string/format_vuln"

    mutations = [
        "%x",
        "%s",
        "%p",
        "%n",
        "%x.%x.%x.%x",
        "%p.%p.%p.%p",
        "AAAA%x",
        "%1$x",
        "%10$x",
        "%2147483647d%n",
    ]

    for mut in mutations:
        print(f"\n-- Testing: {mut} --")
        try:
            result = subprocess.run([binary, mut], capture_output=True, timeout=2, text=True)
            print((result.stdout or "")[:200])
        except Exception as exc:
            print(f"CRASH: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
