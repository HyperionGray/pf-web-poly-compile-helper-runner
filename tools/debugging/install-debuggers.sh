#!/bin/bash
# Install debuggers (gdb, lldb) and pwndbg for advanced debugging

set -e

echo "=== Installing Debugging Tools ==="

# Install base debuggers
echo "Installing GDB and LLDB..."
sudo apt-get update
sudo apt-get install -y gdb lldb python3-pip

# Check versions
echo "GDB version:"
gdb --version | head -1

echo "LLDB version:"
lldb --version | head -1

# Install pwndbg for enhanced debugging
echo "Installing pwndbg..."
PWNDBG_DIR="$HOME/.pwndbg"

if [ -d "$PWNDBG_DIR" ]; then
    echo "pwndbg already installed at $PWNDBG_DIR"
    echo "Updating pwndbg..."
    cd "$PWNDBG_DIR"
    git pull
else
    echo "Cloning pwndbg..."
    git clone https://github.com/pwndbg/pwndbg "$PWNDBG_DIR"
    cd "$PWNDBG_DIR"
fi

# Install pwndbg dependencies and setup
echo "Setting up pwndbg..."
./setup.sh

# Create gdbinit file if it doesn't exist
GDBINIT="$HOME/.gdbinit"
if ! grep -q "source.*pwndbg/gdbinit.py" "$GDBINIT" 2>/dev/null; then
    echo "Adding pwndbg to .gdbinit..."
    echo "source $PWNDBG_DIR/gdbinit.py" >> "$GDBINIT"
fi

echo ""
echo "=== Installation Complete ==="
echo "GDB with pwndbg is ready!"
echo "LLDB is installed and ready!"
echo ""
echo "Quick test:"
echo "  gdb --quiet --batch -ex 'pi import pwndbg; print(\"pwndbg loaded!\")'"
