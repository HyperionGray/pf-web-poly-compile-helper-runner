#!/usr/bin/env bash
# Apply fixes to the repository
set -euo pipefail

echo "Applying fixes to pf-runner repository..."

# Fix 1: Replace hardcoded shebang in pf_parser.py
echo "Fixing hardcoded shebang in pf_parser.py..."
if [[ -f "pf-runner/pf_parser.py" ]]; then
    # Create backup
    cp pf-runner/pf_parser.py pf-runner/pf_parser.py.backup
    
    # Fix shebang
    sed -i '1s|^#!/.*|#!/usr/bin/env python3|' pf-runner/pf_parser.py
    
    echo "✓ Fixed shebang in pf_parser.py"
    echo "  Old: $(head -1 pf-runner/pf_parser.py.backup)"
    echo "  New: $(head -1 pf-runner/pf_parser.py)"
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
if [[ -f "pf-runner/pf_universal" ]]; then
    chmod +x pf-runner/pf_universal
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