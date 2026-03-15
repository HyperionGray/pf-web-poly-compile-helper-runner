#!/usr/bin/env bash
# Minimal smoke checks for pre-install help behavior.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PF_SCRIPT="${SCRIPT_DIR}/pf-runner-full/pf_universal"

if [[ ! -x "$PF_SCRIPT" ]]; then
    echo "ERROR: Missing executable ${PF_SCRIPT}" >&2
    exit 1
fi

echo "Testing source-tree help output..."
echo ""

for flag in help --help -h; do
    echo "Test: pf ${flag}"
    OUTPUT="$("$PF_SCRIPT" "$flag" 2>&1 || true)"
    if [[ "$OUTPUT" == *"Usage"* ]] || [[ "$OUTPUT" == *"usage"* ]]; then
        echo "  PASS"
    else
        echo "  FAIL: expected usage text"
        exit 1
    fi
done

echo ""
echo "All pre-install help checks passed."
