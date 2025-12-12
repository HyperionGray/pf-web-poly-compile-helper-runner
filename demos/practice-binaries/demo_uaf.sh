#!/bin/bash
# Demo: Use-After-Free Exploitation
# This script demonstrates UAF vulnerability

set -e

BINARY="./heap-exploits/use_after_free"
DEMO_NAME="Use-After-Free (UAF)"

echo "========================================"
echo "  $DEMO_NAME Demo"
echo "========================================"
echo ""

# Check if binary exists
if [ ! -f "$BINARY" ]; then
    echo "Error: Binary not found. Run 'make all' first."
    exit 1
fi

echo "Step 1: Understanding the Vulnerability"
echo "----------------------------------------"
echo "Use-After-Free occurs when:"
echo "  1. Memory is allocated"
echo "  2. Memory is freed"
echo "  3. Memory is used again (without re-allocation)"
echo ""
echo "This can lead to:"
echo "  • Information leaks"
echo "  • Control flow hijacking"
echo "  • Arbitrary code execution"
echo ""

echo "Step 2: Normal Usage Flow"
echo "-------------------------"
echo "Creating an object:"
$BINARY create "TestData"
echo ""

echo "Step 3: Demonstrating UAF"
echo "-------------------------"
echo "We'll create, delete, then use the object:"
echo ""
echo "Creating object..."
$BINARY create "MyData" > /tmp/uaf_demo.log 2>&1
echo "Deleting object..."
$BINARY delete >> /tmp/uaf_demo.log 2>&1
echo "Using freed object (UAF!)..."
$BINARY use >> /tmp/uaf_demo.log 2>&1 || echo "May crash or show undefined behavior"
cat /tmp/uaf_demo.log
echo ""

echo "Step 4: Heap State Analysis"
echo "---------------------------"
echo "After free(), the memory is marked as available but"
echo "not cleared. The pointer still points to freed memory."
echo ""
echo "If we allocate new data of the same size, it may"
echo "reuse the same memory location!"
echo ""

echo "Step 5: Exploitation Strategy"
echo "-----------------------------"
echo "To exploit UAF:"
echo "  1. Trigger the UAF condition"
echo "  2. Allocate new object in freed memory"
echo "  3. Control contents of freed memory"
echo "  4. Trigger use of freed object"
echo "  5. Hijack control flow via function pointer"
echo ""

echo "Step 6: Manual Exploitation Example"
echo "------------------------------------"
echo "The object contains a function pointer at offset 32."
echo "We need to:"
echo "  1. Free the object"
echo "  2. Allocate 'evil' data with secret_handler address"
echo "  3. Call 'use' to trigger the UAF"
echo ""

echo "Step 7: Debugging in GDB"
echo "------------------------"
echo "To debug this:"
echo ""
echo "  gdb $BINARY"
echo "  (gdb) break create_object"
echo "  (gdb) break delete_object"
echo "  (gdb) break use_object"
echo ""
echo "  (gdb) run create AAAA"
echo "  (gdb) x/16gx global_obj    # Examine object"
echo "  (gdb) continue"
echo ""
echo "  (gdb) run delete"
echo "  (gdb) x/16gx global_obj    # Check freed memory"
echo "  (gdb) continue"
echo ""
echo "  (gdb) run use"
echo "  (gdb) x/16gx global_obj    # See UAF state"
echo ""

echo "Step 8: Learning Objectives"
echo "---------------------------"
echo "✓ Understand heap memory management"
echo "✓ Identify UAF vulnerabilities"
echo "✓ Exploit freed memory reuse"
echo "✓ Control object data after free"
echo "✓ Hijack function pointers"
echo ""

echo "Step 9: Real-World Context"
echo "--------------------------"
echo "UAF vulnerabilities are common in:"
echo "  • Browsers (JavaScript engines)"
echo "  • Kernels (race conditions)"
echo "  • Applications with complex object lifecycles"
echo ""
echo "Famous examples:"
echo "  • CVE-2020-0938 (Windows Font Library UAF)"
echo "  • CVE-2019-11707 (Firefox Type Confusion UAF)"
echo ""

echo "Step 10: Advanced Techniques"
echo "----------------------------"
echo "• Heap spraying to control freed memory"
echo "• Heap feng shui to control layout"
echo "• Combining with info leaks for ASLR bypass"
echo "• Exploiting with heap allocator metadata"
echo ""

echo "========================================"
echo "  Demo Complete!"
echo "========================================"
