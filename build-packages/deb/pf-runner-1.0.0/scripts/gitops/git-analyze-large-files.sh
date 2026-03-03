#!/usr/bin/env bash
set -euo pipefail

min_mb="${1:-1}"
limit="${2:-50}"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "ERROR: not a git repo (run inside a repository)"
  exit 1
fi

min_bytes=$(( min_mb * 1024 * 1024 ))

# Prints: <size>\t<path>
git rev-list --all --objects \
  | git cat-file --batch-check="%(objecttype) %(objectname) %(objectsize) %(rest)" \
  | awk -v min="$min_bytes" '$1=="blob" && $3>=min {print $3 "\t" $4}' \
  | sort -nr \
  | head -n "$limit" \
  | awk '{
      size=$1; path=$2;
      unit="B";
      if (size>=1024) { size/=1024; unit="KB" }
      if (size>=1024) { size/=1024; unit="MB" }
      if (size>=1024) { size/=1024; unit="GB" }
      printf("%8.2f %s\t%s\n", size, unit, path);
    }'
