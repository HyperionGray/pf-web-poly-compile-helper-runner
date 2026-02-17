#!/usr/bin/env bash
# Fix hardcoded paths in pf_parser.py
set -euo pipefail

echo "Fixing hardcoded shebang path in pf_parser.py..."

# Create a backup
cp pf-runner/pf_parser.py pf-runner/pf_parser.py.backup

# Fix the shebang line
sed -i '1s|^#!/.*|#!/usr/bin/env python3|' pf-runner/pf_parser.py

echo "Fixed shebang path in pf_parser.py"
echo "Backup saved as pf_parser.py.backup"

# Verify the change
echo "New first line:"
head -1 pf-runner/pf_parser.py