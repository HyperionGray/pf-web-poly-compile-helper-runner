#!/bin/bash
# Comprehensive Test Runner - "Test it all again and again and again. That's thrice."
# This script runs all tests three times with fresh environment setup

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Comprehensive Test Suite"
echo "Testing it all again and again and again. That's thrice!"
echo "============================================================"

# Make sure the comprehensive test runner is executable
chmod +x test_all_comprehensive.py

# Run the comprehensive test suite
python3 test_all_comprehensive.py

exit_code=$?

echo ""
echo "============================================================"
if [ $exit_code -eq 0 ]; then
    echo "🎉 All tests completed successfully across all three runs!"
    echo "✅ Nay ye canne deny it workes!"
else
    echo "⚠️  Some tests had issues. Check the detailed report above."
    echo "❌ Review and fix failing tests."
fi
echo "============================================================"

exit $exit_code
