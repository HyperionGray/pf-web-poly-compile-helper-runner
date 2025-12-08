#!/bin/bash
chmod +x "$0"

# Demo script showing the new smart workflow capabilities
# This demonstrates how multiple tools now work together intelligently

echo "🚀 Smart Workflow Integration Demo"
echo "=================================="
echo ""

echo "This demo shows how the enhanced pf framework now combines multiple"
echo "security tools intelligently to create powerful, automated workflows."
echo ""

# Check if pf is available
if ! command -v pf &> /dev/null; then
    echo "❌ pf command not found. Please install pf first:"
    echo "   sudo ./install.sh"
    exit 1
fi

echo "📋 Available Smart Workflows:"
echo ""
echo "1. 🎯 autopwn    - Complete binary exploitation (analysis → vuln discovery → exploit)"
echo "2. 🌐 autoweb    - Complete web security assessment (discovery → scanning → exploitation)"
echo "3. 🔧 autokernel - Complete kernel analysis (IOCTL → firmware → vulnerability analysis)"
echo "4. 🧠 smart-*    - Intelligent tool combinations that adapt to target type"
echo "5. ⛓️  exploit chains - End-to-end vulnerability to payload workflows"
echo ""

echo "🔍 Tool Detection Demo:"
echo "----------------------"
echo "First, let's see what security tools are available:"
echo ""

# Demonstrate tool detection
if [ -f "tools/orchestration/tool-detector.mjs" ]; then
    echo "Running: node tools/orchestration/tool-detector.mjs --format table"
    node tools/orchestration/tool-detector.mjs --format table 2>/dev/null || echo "Tool detector not ready yet"
else
    echo "Tool detector not found - showing available pf tasks instead:"
    pf list | grep -E "(smart-|auto)" | head -10
fi

echo ""
echo "💡 Example Usage:"
echo "----------------"
echo ""

echo "# Complete binary exploitation (one command):"
echo "pf autopwn binary=/path/to/vulnerable/binary"
echo ""

echo "# Complete web security assessment (one command):"
echo "pf autoweb url=http://target-website.com"
echo ""

echo "# Smart analysis that adapts to target type:"
echo "pf smart-full-stack target=/path/to/binary    # Auto-detects binary"
echo "pf smart-full-stack target=http://website.com # Auto-detects web app"
echo ""

echo "# Quick aliases for power users:"
echo "pf apwn binary=/path/to/binary     # Short for autopwn"
echo "pf aweb url=http://target.com      # Short for autoweb"
echo "pf sfs target=anything             # Short for smart-full-stack"
echo ""

echo "🎯 Key Improvements:"
echo "-------------------"
echo "✅ Fewer commands needed (1 instead of 10+)"
echo "✅ Intelligent tool selection based on target"
echo "✅ Automatic workflow adaptation"
echo "✅ Cross-tool result correlation"
echo "✅ Standardized output formats"
echo "✅ Smart error handling and fallbacks"
echo ""

echo "🔧 What's Different Now:"
echo "-----------------------"
echo "BEFORE: pf checksec → pf strings → pf objdump → pf rop-find → pf exploit-template"
echo "NOW:    pf autopwn binary=/path/to/binary"
echo ""
echo "BEFORE: pf security-scan → pf security-fuzz → manual correlation"
echo "NOW:    pf autoweb url=http://target.com"
echo ""

echo "📊 Integration Benefits:"
echo "----------------------"
echo "• Tools now share data automatically"
echo "• Results are correlated across domains"
echo "• Workflows adapt based on initial findings"
echo "• Reduced false positives through cross-validation"
echo "• Comprehensive reports combining all tool outputs"
echo ""

echo "🚀 Try it out:"
echo "-------------"
echo "1. Create a test binary: gcc -o test -fno-stack-protector test.c"
echo "2. Run: pf autopwn binary=./test"
echo "3. Watch as multiple tools work together automatically!"
echo ""

echo "For more examples, see:"
echo "• Pfyfile.smart-workflows.pf - Core intelligent workflows"
echo "• Pfyfile.enhanced-integration.pf - Smart tool combinations"
echo "• tools/orchestration/ - Workflow engine and tool detection"
echo ""

echo "✨ The framework now does more with less - fewer commands, smarter results!"