#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}"

echo "Fixing hardcoded shebang path in pf_parser.py..."

# Create a backup
cp "${REPO_ROOT}/pf-runner/pf_parser.py" "${REPO_ROOT}/pf-runner/pf_parser.py.backup"

# Fix the shebang line
sed -i '1s|^#!/.*|#!/usr/bin/env python3|' "${REPO_ROOT}/pf-runner/pf_parser.py"

echo "Fixed shebang path in pf_parser.py"
echo "Backup saved as pf_parser.py.backup"

# Verify the change
echo "New first line:"
head -1 "${REPO_ROOT}/pf-runner/pf_parser.py"
