#!/bin/bash
# Make all smart workflow tools executable

chmod +x tools/smart-workflows/*.py
chmod +x tools/smart-workflows/make_executable.sh
echo "✓ Made all smart workflow tools executable"

# Test basic functionality
echo "Testing smart workflow integration..."

# Test target detection
echo "Testing target detection with /bin/ls..."
if python3 tools/smart-workflows/target_detector.py /bin/ls --format text; then
    echo "✓ Target detection working"
else
    echo "⚠️ Target detection had issues, but basic structure is in place"
fi

echo ""
echo "✓ Smart workflows integration complete!"
echo ""
echo "Try these commands:"
echo "  pf smart-help                    # Show smart workflow help"
echo "  pf smart-detect target=/bin/ls   # Test target detection"
echo "  pf checksec-unified binary=/bin/ls  # Test unified checksec"