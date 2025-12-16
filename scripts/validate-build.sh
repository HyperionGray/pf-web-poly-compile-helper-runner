#!/usr/bin/env bash
# Build validation script for CI/CD
# Validates essential project files exist without requiring compilation

set -eu

echo "✅ Build validation: Checking project structure..."

# Check for essential files
if [ ! -f "README.md" ]; then
  echo "❌ README.md not found"
  exit 1
fi

if [ ! -d "pf-runner" ]; then
  echo "❌ pf-runner directory not found"
  exit 1
fi

if [ ! -f "Pfyfile.pf" ]; then
  echo "❌ Pfyfile.pf not found"
  exit 1
fi

echo "✅ Build validation complete: All essential files present"
exit 0