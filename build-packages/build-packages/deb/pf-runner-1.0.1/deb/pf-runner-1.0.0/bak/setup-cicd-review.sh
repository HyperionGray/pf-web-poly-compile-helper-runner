#!/bin/bash

# Make CI/CD review scripts executable
chmod +x scripts/ci-cd-review/*.mjs

echo "✅ Made CI/CD review scripts executable"

# Test file analyzer
echo "🔍 Testing file analyzer..."
node scripts/ci-cd-review/file-analyzer.mjs --cicd | head -20

echo ""
echo "✅ CI/CD Review System setup completed!"
echo ""
echo "Available commands:"
echo "  npm run cicd:review              - Run complete review"
echo "  npm run cicd:review:save         - Run and save report"
echo "  npm run cicd:file-analysis       - File analysis only"
echo "  npm run cicd:docs-validation     - Documentation validation only"
echo "  npm run cicd:test-coverage       - Test coverage only"
echo "  npm run cicd:build-status        - Build status only"
echo ""
echo "GitHub Actions workflow: .github/workflows/cicd-review.yml"