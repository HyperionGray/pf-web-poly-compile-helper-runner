#!/bin/bash
set -e

# Ensure PATH includes local bin and Ghidra
export PATH="/home/pf/.local/bin:/opt/ghidra/support:$PATH"
export GHIDRA_INSTALL_DIR="/opt/ghidra"

# Function to start GDB with pwndbg
start_gdb() {
    local binary="${1:-}"
    if [ -n "$binary" ]; then
        echo "Starting GDB with pwndbg for binary: $binary"
        exec gdb -q "$binary"
    else
        echo "Starting GDB with pwndbg (no binary specified)"
        exec gdb -q
    fi
}

# Function to start LLDB
start_lldb() {
    local binary="${1:-}"
    if [ -n "$binary" ]; then
        echo "Starting LLDB for binary: $binary"
        exec lldb "$binary"
    else
        echo "Starting LLDB (no binary specified)"
        exec lldb
    fi
}

# Function to start Radare2
start_radare2() {
    local binary="${1:-}"
    if [ -n "$binary" ]; then
        echo "Starting Radare2 for binary: $binary"
        exec radare2 "$binary"
    else
        echo "Error: Binary required for Radare2"
        exit 1
    fi
}

# Function to run Ghidra headless analysis
run_ghidra_analysis() {
    local binary="${1:-}"
    local project="${2:-analysis}"
    
    if [ -z "$binary" ]; then
        echo "Error: Binary required for Ghidra analysis"
        exit 1
    fi
    
    echo "Running Ghidra headless analysis on: $binary"
    mkdir -p /workspace/ghidra-projects
    
    exec /opt/ghidra/support/analyzeHeadless \
        /workspace/ghidra-projects "$project" \
        -import "$binary" \
        -postScript /opt/ghidra/Ghidra/Features/Base/ghidra_scripts/ExportFunctionsScript.java
}

# Function to analyze binary with multiple tools
analyze_binary() {
    local binary="${1:-}"
    
    if [ -z "$binary" ] || [ ! -f "$binary" ]; then
        echo "Error: Valid binary file required"
        exit 1
    fi
    
    echo "Comprehensive binary analysis for: $binary"
    echo "========================================"
    
    echo "File information:"
    file "$binary"
    echo ""
    
    echo "Security features (checksec):"
    checksec --file="$binary" 2>/dev/null || echo "checksec not available"
    echo ""
    
    echo "Strings (first 20):"
    strings "$binary" | head -20
    echo ""
    
    echo "ELF header:"
    readelf -h "$binary" 2>/dev/null || echo "Not an ELF file"
    echo ""
    
    echo "Symbols:"
    nm "$binary" 2>/dev/null | head -10 || echo "No symbols available"
    echo ""
    
    echo "Dependencies:"
    ldd "$binary" 2>/dev/null || echo "Not a dynamic executable"
}

# Function to find ROP gadgets
find_rop_gadgets() {
    local binary="${1:-}"
    local count="${2:-20}"
    
    if [ -z "$binary" ] || [ ! -f "$binary" ]; then
        echo "Error: Valid binary file required"
        exit 1
    fi
    
    echo "Finding ROP gadgets in: $binary"
    echo "Showing first $count gadgets:"
    
    if command -v ROPgadget >/dev/null 2>&1; then
        ROPgadget --binary "$binary" | head -"$count"
    elif command -v ropper >/dev/null 2>&1; then
        python3 -c "
import ropper
from ropper import RopperService

rs = RopperService()
rs.addFile('$binary')
rs.loadGadgetsFor()
gadgets = rs.getGadgets()
for i, gadget in enumerate(gadgets[:$count]):
    print(gadget)
"
    else
        echo "No ROP gadget finder available (ROPgadget or ropper)"
        exit 1
    fi
}

# Function to start exploit development environment
start_exploit_env() {
    echo "Starting exploit development environment..."
    echo "Available tools:"
    echo "- pwntools (Python)"
    echo "- GDB with pwndbg"
    echo "- Radare2"
    echo "- ROPgadget/ropper"
    echo "- Ghidra"
    echo ""
    echo "Starting Python with pwntools imported..."
    
    python3 -c "
import pwn
print('pwntools version:', pwn.__version__)
print('Available context architectures:', list(pwn.context.architectures.keys())[:10])
print('')
print('Starting interactive Python shell with pwntools...')
print('Use: from pwn import *')
" && python3 -i -c "from pwn import *"
}

# Function to show security tools info
show_info() {
    echo "Security Tools Environment Information:"
    echo "======================================"
    echo "GDB: $(gdb --version | head -1)"
    echo "LLDB: $(lldb --version | head -1)"
    echo "Radare2: $(radare2 -v | head -1)"
    echo "Python: $(python3 --version)"
    
    echo -n "pwntools: "
    python3 -c "import pwn; print(pwn.__version__)" 2>/dev/null || echo "Not available"
    
    echo -n "ROPgadget: "
    ROPgadget --version 2>/dev/null || echo "Not available"
    
    echo -n "Ghidra: "
    if [ -d "/opt/ghidra" ]; then
        echo "Installed at /opt/ghidra"
    else
        echo "Not available"
    fi
    
    echo -n "Checksec: "
    checksec --version 2>/dev/null || echo "Not available"
    
    echo ""
    echo "Available exploit development tools:"
    ls -la tools/exploit/ 2>/dev/null || echo "No exploit tools directory"
}

# Function to show help
show_help() {
    cat << EOF
Security Tools Container

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    gdb [BINARY]        Start GDB with pwndbg
    lldb [BINARY]       Start LLDB debugger
    radare2 BINARY      Start Radare2 reverse engineering
    ghidra BINARY [PROJECT]  Run Ghidra headless analysis
    analyze BINARY      Comprehensive binary analysis
    rop-gadgets BINARY [COUNT]  Find ROP gadgets
    exploit-env         Start exploit development environment
    info                Show security tools information
    bash                Start interactive bash shell
    help                Show this help message

Examples:
    # Debug a binary with GDB
    $0 gdb /workspace/demos/vulnerable_binary
    
    # Analyze binary with multiple tools
    $0 analyze /bin/ls
    
    # Find ROP gadgets
    $0 rop-gadgets /workspace/demos/vulnerable_binary 50
    
    # Start exploit development
    $0 exploit-env
    
    # Reverse engineer with Radare2
    $0 radare2 /workspace/demos/target_binary

Environment Variables:
    BINARY              Default binary to analyze
    DEBUG_MODE          Enable verbose debugging output
EOF
}

# Parse command line arguments
COMMAND="${1:-${DEFAULT_COMMAND:-bash}}"
shift || true

# Handle different commands
case "$COMMAND" in
    "gdb")
        start_gdb "$1"
        ;;
    "lldb")
        start_lldb "$1"
        ;;
    "radare2"|"r2")
        start_radare2 "$1"
        ;;
    "ghidra")
        run_ghidra_analysis "$1" "$2"
        ;;
    "analyze")
        analyze_binary "$1"
        ;;
    "rop-gadgets"|"rop")
        find_rop_gadgets "$1" "$2"
        ;;
    "exploit-env"|"exploit")
        start_exploit_env
        ;;
    "info")
        show_info
        ;;
    "bash")
        exec /bin/bash
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        echo "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac