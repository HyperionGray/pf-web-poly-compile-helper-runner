#!/bin/bash
# Quick test to verify the comprehensive test runner works

set -euo pipefail

echo "🧪 Quick Verification Test"
echo "=========================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# Make scripts executable (idempotent)
chmod +x test_all_comprehensive.py
chmod +x test_runner_verification.py
chmod +x run_tests.sh

echo "📋 Running quick verification..."
python3 test_all_comprehensive.py --quick

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Quick verification passed!"
    echo "🚀 Ready to run full comprehensive test suite"
    echo ""
    echo "To run the full test suite (3 times), execute:"
    echo "  ./run_tests.sh"
    echo ""
    echo "Or run directly:"
    echo "  python3 test_all_comprehensive.py"
else
    echo ""
    echo "❌ Quick verification failed!"
    echo "Check the error messages above."
fi
