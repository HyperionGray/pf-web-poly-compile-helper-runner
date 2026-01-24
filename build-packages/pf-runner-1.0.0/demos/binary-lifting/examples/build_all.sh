#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p bin output
gcc -O0 -g simple_math.c   -o bin/simple_math_O0
gcc -O2     simple_math.c   -o bin/simple_math_O2
gcc -O3     simple_math.c   -o bin/simple_math
gcc -O0 -g string_ops.c    -o bin/string_ops_O0
gcc -O2     string_ops.c    -o bin/string_ops_O2
gcc -O3     string_ops.c    -o bin/string_ops
gcc -O0 -g loop_example.c  -o bin/loop_example_O0
gcc -O2     loop_example.c  -o bin/loop_example_O2
gcc -O3     loop_example.c  -o bin/loop_example
echo "All examples built successfully!"
ls -lh bin/
