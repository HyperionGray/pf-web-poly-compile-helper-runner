#!/usr/bin/env bash
set -euo pipefail
source_file=${1:-}
target=${2:-}
if [[ -z "$source_file" ]]; then
  echo "Usage: build_with_asan.sh <source.c> [output]" >&2
  exit 1
fi
if [[ -z "$target" ]]; then
  target="${source_file%.*}_asan"
fi
dir=$(dirname "$target")
[[ -d "$dir" ]] || mkdir -p "$dir"
echo "Building $source_file with AddressSanitizer -> $target ..."
clang -fsanitize=address -g -O1 "$source_file" -o "$target"
echo "✅ Built: $target"
echo "Run with: ASAN_OPTIONS=detect_leaks=1 ./$target"
