#!/usr/bin/env bash
# Install Ghidra helper scripts

set -e

echo "=== Ghidra Installation Helper ==="
echo ""
echo "Ghidra must be downloaded manually from:"
echo "  https://ghidra-sre.org/"
echo ""
echo "Installation steps:"
echo "  1. Download Ghidra (requires Java 11+)"
echo "  2. Extract: unzip ghidra_*.zip"
echo "  3. Add to PATH or create symlink:"
echo "     sudo ln -s /path/to/ghidra_*/ghidraRun /usr/local/bin/ghidra"
echo ""
echo "For headless analysis:"
echo "  ghidra_*/support/analyzeHeadless <project_dir> <project_name> -import <binary>"
echo ""

# Check if Ghidra is already available
if command -v ghidraRun &> /dev/null; then
    echo "✓ Ghidra is already installed"
    ghidraRun --version || echo "Ghidra found but version check failed"
else
    echo "✗ Ghidra not found in PATH"
fi

echo ""
echo "After installation, use:"
echo "  pf reverse-ghidra binary=/path/to/binary"
