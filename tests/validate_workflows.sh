#!/bin/bash
# Simple YAML syntax validation script

echo "Validating modified GitHub Actions workflow files..."

# List of modified workflow files
workflows=(
    ".github/workflows/auto-copilot-code-cleanliness-review.yml"
    ".github/workflows/auto-copilot-test-review-playwright.yml"
    ".github/workflows/auto-copilot-functionality-docs-review.yml"
    ".github/workflows/auto-gpt5-implementation.yml"
    ".github/workflows/auto-tag-based-review.yml"
)

# Check if python3 is available for YAML validation
if command -v python3 &> /dev/null; then
    echo "Using Python for YAML validation..."
    
    for workflow in "${workflows[@]}"; do
        echo "Checking: $workflow"
        python3 -c "
import yaml
import sys
try:
    with open('$workflow', 'r') as f:
        yaml.safe_load(f)
    print('✅ Valid YAML syntax')
except yaml.YAMLError as e:
    print('❌ YAML syntax error:', e)
    sys.exit(1)
except Exception as e:
    print('❌ Error reading file:', e)
    sys.exit(1)
"
        if [ $? -ne 0 ]; then
            echo "YAML validation failed for $workflow"
            exit 1
        fi
    done
    
    echo "✅ All workflow files have valid YAML syntax"
else
    echo "⚠️  Python3 not available for YAML validation"
    echo "Performing basic syntax checks..."
    
    for workflow in "${workflows[@]}"; do
        echo "Checking: $workflow"
        # Basic checks for common YAML issues
        if grep -q "^[[:space:]]*-[[:space:]]*name:" "$workflow"; then
            echo "✅ Contains properly formatted step names"
        else
            echo "⚠️  No step names found or formatting issue"
        fi
        
        if grep -q "^[[:space:]]*uses:" "$workflow"; then
            echo "✅ Contains action uses statements"
        fi
        
        # Check for proper indentation (no tabs)
        if grep -q $'\t' "$workflow"; then
            echo "❌ Contains tab characters (should use spaces)"
            exit 1
        else
            echo "✅ Uses proper space indentation"
        fi
    done
fi

echo ""
echo "🎉 All checks passed! CI pipeline fix appears to be successful."