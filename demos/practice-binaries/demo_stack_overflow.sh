#!/bin/bash
# Demo: Stack Buffer Overflow Exploitation
# This script demonstrates debugging and exploiting stack_overflow binary

set -e

BINARY="./buffer-overflow/stack_overflow"
DEMO_NAME="Stack Buffer Overflow"

echo "========================================"
echo "  $DEMO_NAME Demo"
echo "========================================"
echo ""

# Check if binary exists
if [ ! -f "$BINARY" ]; then
    echo "Error: Binary not found. Run 'make all' first."
    exit 1
fi

echo "Step 1: Normal Execution"
echo "------------------------"
echo "Running: $BINARY AAAA"
$BINARY "AAAA"
echo ""

echo "Step 2: Triggering Buffer Overflow"
echo "-----------------------------------"
echo "Sending 100 A's to overflow buffer..."
echo "Running: $BINARY \$(python3 -c \"print('A'*100)\")"
$BINARY $(python3 -c "print('A'*100)") 2>&1 || echo "Program crashed (expected)"
echo ""

echo "Step 3: Debugging with GDB"
echo "--------------------------"
echo "To debug this binary:"
echo ""
echo "  gdb $BINARY"
echo "  (gdb) break vulnerable_function"
echo "  (gdb) run AAAA"
echo "  (gdb) info frame"
echo "  (gdb) x/20wx \$rsp"
echo "  (gdb) continue"
echo ""
echo "To find the offset to overwrite return address:"
echo ""
echo "  (gdb) pattern create 100"
echo "  (gdb) run <pattern>"
echo "  (gdb) pattern offset <crash_address>"
echo ""

echo "Step 4: Exploitation Goal"
echo "-------------------------"
echo "The goal is to overwrite the return address to redirect"
echo "execution to the win() function."
echo ""
echo "Win function address (from binary output): Check the output above"
echo ""
echo "Steps to exploit:"
echo "  1. Find offset to return address (using pattern)"
echo "  2. Craft payload: padding + win_addr"
echo "  3. Execute: $BINARY \$(python3 exploit.py)"
echo ""

echo "Step 5: Learning Objectives"
echo "---------------------------"
echo "✓ Understand stack layout and function frames"
echo "✓ Identify buffer overflow vulnerabilities"
echo "✓ Calculate offsets to control flow data"
echo "✓ Craft exploitation payloads"
echo "✓ Bypass stack protections (disabled in this binary)"
echo ""

echo "Step 6: Next Steps"
echo "------------------"
echo "• Practice with debugger to understand stack layout"
echo "• Write a Python script to automate exploitation"
echo "• Try with stack protections enabled"
echo "• Learn about ASLR and how to bypass it"
echo ""

echo "========================================"
echo "  Demo Complete!"
echo "========================================"
