#!/usr/bin/env python3
import random
import string
import subprocess
import sys


def main() -> int:
    binary = sys.argv[1] if len(sys.argv) > 1 else "demos/practice-binaries/buffer-overflow/stack_overflow"

    for i in range(10):
        length = random.randint(10, 200)
        input_str = "".join(random.choices(string.ascii_letters, k=length))
        print(f"\n-- Test {i+1}: Length {length} --")
        try:
            result = subprocess.run([binary, input_str], capture_output=True, timeout=2, text=True)
            print((result.stdout or "")[:200])
        except subprocess.TimeoutExpired:
            print("TIMEOUT")
        except Exception as exc:
            print(f"CRASH: {exc}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
