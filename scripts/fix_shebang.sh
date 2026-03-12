#!/usr/bin/env bash
# Fix hardcoded paths in pf_parser.py
set -euo pipefail

echo "Fixing hardcoded shebang path in pf_parser.py..."

RUNNER_DIR="pf-runner-full"
if [[ ! -d "$RUNNER_DIR" && -d "pf-runner" ]]; then
    RUNNER_DIR="pf-runner"
fi
PF_PARSER="${RUNNER_DIR}/pf_parser.py"

# Create a backup
cp "$PF_PARSER" "$PF_PARSER.backup"

# Fix the shebang line
sed -i '1s|^#!/.*|#!/usr/bin/env python3|' "$PF_PARSER"

echo "Fixed shebang path in pf_parser.py"
echo "Backup saved as pf_parser.py.backup"

# Verify the change
echo "New first line:"
head -1 "$PF_PARSER"
