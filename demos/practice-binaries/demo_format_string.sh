#!/bin/bash
# Demo: Format String Exploitation
# This script demonstrates format string vulnerabilities

set -e

BINARY="./format-string/format_vuln"
DEMO_NAME="Format String Vulnerability"

echo "========================================"
echo "  $DEMO_NAME Demo"
echo "========================================"
echo ""

# Check if binary exists
if [ ! -f "$BINARY" ]; then
    echo "Error: Binary not found. Run 'make all' first."
    exit 1
fi

echo "Step 1: Normal Usage"
echo "--------------------"
echo "Running: $BINARY 'Hello World'"
$BINARY "Hello World"
echo ""

echo "Step 2: Reading Stack Values"
echo "----------------------------"
echo "Using %x to read stack as hex values:"
echo "Running: $BINARY '%x.%x.%x.%x.%x.%x.%x.%x'"
$BINARY "%x.%x.%x.%x.%x.%x.%x.%x"
echo ""

echo "Using %p to read stack as pointers:"
echo "Running: $BINARY '%p.%p.%p.%p.%p.%p.%p.%p'"
$BINARY "%p.%p.%p.%p.%p.%p.%p.%p"
echo ""

echo "Step 3: Understanding the Attack"
echo "--------------------------------"
echo "Format string vulnerabilities allow:"
echo "  • Reading arbitrary memory (information leak)"
echo "  • Writing to arbitrary memory (exploitation)"
echo ""
echo "The binary contains:"
echo "  - secret_value: a secret integer"
echo "  - auth_flag: authentication flag"
echo ""
echo "Goal: Modify auth_flag to 1337 to gain access"
echo ""

echo "Step 4: Memory Write with %n"
echo "----------------------------"
echo "The %n format specifier writes the number of bytes"
echo "printed so far to the address on the stack."
echo ""
echo "To exploit:"
echo "  1. Find offset to auth_flag address on stack"
echo "  2. Use %n to write desired value (1337)"
echo ""
echo "Example approach:"
echo "  $BINARY \"\$(python3 -c 'import sys; sys.stdout.write(\"AAAA%7\\\$n\")')\""
echo ""

echo "Step 5: Debugging in GDB"
echo "------------------------"
echo "To analyze with GDB:"
echo ""
echo "  gdb $BINARY"
echo "  (gdb) break vulnerable_printf"
echo "  (gdb) run '%p.%p.%p.%p'"
echo "  (gdb) x/20gx \$rsp     # Examine stack"
echo "  (gdb) p &auth_flag      # Get auth_flag address"
echo "  (gdb) p &secret_value   # Get secret_value address"
echo ""

echo "Step 6: Information Leak"
echo "------------------------"
echo "Reading specific memory address using %s:"
echo "(This would show memory contents as string)"
echo ""

echo "Step 7: Learning Objectives"
echo "---------------------------"
echo "✓ Understand format string vulnerabilities"
echo "✓ Read arbitrary memory locations"
echo "✓ Write to memory using %n"
echo "✓ Calculate offsets on the stack"
echo "✓ Modify program variables"
echo ""

echo "Step 8: Advanced Techniques"
echo "---------------------------"
echo "• Direct parameter access: %7\$p"
echo "• Multiple writes: Use multiple %n"
echo "• Byte-by-byte writes: %hhn for single byte"
echo "• ASLR bypass: Leak addresses with %p"
echo ""

echo "========================================"
echo "  Demo Complete!"
echo "========================================"
