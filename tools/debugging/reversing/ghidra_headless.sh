#!/usr/bin/env bash
# Ghidra Headless Analysis Wrapper
binary="$1"
script="${2:-}"

echo "[*] Ghidra Headless Analysis"
echo "[!] This is a stub - Ghidra must be installed separately"
echo ""
echo "To run Ghidra headless analysis:"
echo "  analyzeHeadless /tmp/project MyProject -import $binary -postScript $script"
echo ""
echo "Install Ghidra from: https://ghidra-sre.org/"
