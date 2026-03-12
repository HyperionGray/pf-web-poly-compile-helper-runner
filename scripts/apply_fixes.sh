#!/usr/bin/env bash
# Apply fixes to the repository
set -euo pipefail

echo "Applying fixes to pf-runner repository..."

RUNNER_DIR="pf-runner-full"
if [[ ! -d "$RUNNER_DIR" && -d "pf-runner" ]]; then
    RUNNER_DIR="pf-runner"
fi
PF_PARSER="${RUNNER_DIR}/pf_parser.py"
PF_UNIVERSAL="${RUNNER_DIR}/pf_universal"

# Fix 1: Replace hardcoded shebang in pf_parser.py
echo "Fixing hardcoded shebang in pf_parser.py..."
if [[ -f "$PF_PARSER" ]]; then
    # Create backup
    cp "$PF_PARSER" "$PF_PARSER.backup"
    
    # Fix shebang
    sed -i '1s|^#!/.*|#!/usr/bin/env python3|' "$PF_PARSER"
    
    echo "✓ Fixed shebang in pf_parser.py"
    echo "  Old: $(head -1 "$PF_PARSER.backup")"
    echo "  New: $(head -1 "$PF_PARSER")"
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
if [[ -f "$PF_UNIVERSAL" ]]; then
    chmod +x "$PF_UNIVERSAL"
    echo "✓ pf_universal is executable"
else
    echo "✗ pf_universal not found"
    exit 1
fi

# Fix 4: Check for other potential hardcoded paths
echo "Checking for other hardcoded paths..."
if grep -r "/home/punk" . --exclude-dir=.git --exclude="*.backup" 2>/dev/null; then
    echo "✗ Found additional hardcoded paths that need fixing"
else
    echo "✓ No additional hardcoded paths found"
fi

echo "Repository fixes applied successfully!"