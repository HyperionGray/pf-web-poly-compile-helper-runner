#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}"
cd "${REPO_ROOT}"

echo "Applying fixes to pf-runner repository..."

# Fix 1: Replace hardcoded shebang in pf_parser.py
echo "Fixing hardcoded shebang in pf_parser.py..."
if [[ -f "${REPO_ROOT}/pf-runner/pf_parser.py" ]]; then
    # Create backup
    cp "${REPO_ROOT}/pf-runner/pf_parser.py" "${REPO_ROOT}/pf-runner/pf_parser.py.backup"
    
    # Fix shebang
    sed -i '1s|^#!/.*|#!/usr/bin/env python3|' "${REPO_ROOT}/pf-runner/pf_parser.py"
    
    echo "✓ Fixed shebang in pf_parser.py"
    echo "  Old: $(head -1 "${REPO_ROOT}/pf-runner/pf_parser.py.backup")"
    echo "  New: $(head -1 "${REPO_ROOT}/pf-runner/pf_parser.py")"
else
    echo "✗ pf_parser.py not found"
    exit 1
fi

# Fix 2: Ensure install.sh is executable
echo "Ensuring install.sh is executable..."
if [[ -f "install.sh" ]]; then
    chmod +x install.sh
    echo "✓ install.sh is executable"
else
    echo "✗ install.sh not found"
    exit 1
fi

# Fix 3: Ensure pf_universal is executable
echo "Ensuring pf_universal is executable..."
if [[ -f "${REPO_ROOT}/pf-runner/pf_universal" ]]; then
    chmod +x "${REPO_ROOT}/pf-runner/pf_universal"
    echo "✓ pf_universal is executable"
else
    echo "✗ pf_universal not found"
    exit 1
fi

# Fix 4: Check for other potential hardcoded paths
echo "Checking for other hardcoded paths..."
HARD_CODED_HOME_REGEX='/home/[^/]+/|/Users/[^/]+/'
if grep -R -n -E "$HARD_CODED_HOME_REGEX" \
    --exclude-dir=.git \
    --exclude-dir=build-packages \
    --exclude-dir=.venv \
    --exclude-dir=node_modules \
    --exclude-dir=_asan \
    --exclude-dir=_fuzzer \
    --exclude-dir=aflfuzz \
    --exclude-dir=bak \
    --exclude="*.backup" \
    --exclude="*.broken" \
    --include="*.sh" \
    --include="*.py" \
    --include="*.pf" \
    . 2>/dev/null; then
    echo "✗ Found hardcoded home-directory paths that need fixing"
else
    echo "✓ No hardcoded home-directory paths found"
fi

echo "Repository fixes applied successfully!"
