#!/usr/bin/env bash
# Install comprehensive debugging and reverse engineering tools

set -e

echo "=== Installing Advanced Debugging Tools ==="

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    echo "Warning: Unsupported OS: $OSTYPE"
    OS="unknown"
fi

echo "Detected OS: $OS"

# Install base debugging tools
if [ "$OS" == "linux" ]; then
    echo "Installing base debugging tools (Linux)..."
    sudo apt-get update
    sudo apt-get install -y \
        lldb \
        gdb \
        strace \
        ltrace \
        binutils \
        valgrind \
        python3-pip \
        || echo "Some packages may have failed to install"
        
    # Install radare2
    echo "Installing radare2..."
    sudo apt-get install -y radare2 || {
        echo "radare2 not in repos, installing from source..."
        git clone https://github.com/radareorg/radare2 /tmp/radare2 || true
        cd /tmp/radare2 && sys/install.sh || echo "radare2 installation failed, continuing..."
    }
    
elif [ "$OS" == "macos" ]; then
    echo "Installing base debugging tools (macOS)..."
    brew install lldb radare2 binutils gdb || echo "Some packages may have failed"
fi

# Install Python packages for automation
echo "Installing Python debugging libraries..."
pip3 install --user \
    r2pipe \
    pwntools \
    capstone \
    keystone-engine \
    unicorn \
    lief \
    angr \
    || echo "Some Python packages may have failed to install"

# Install firmware analysis tools
if [ "$OS" == "linux" ]; then
    echo "Installing firmware analysis tools..."
    sudo apt-get install -y \
        binwalk \
        flashrom \
        squashfs-tools \
        || echo "Some firmware tools failed to install"
fi

# Create directory structure
echo "Creating directory structure..."
mkdir -p ~/debug_workspace/{ioctl,firmware,reversing,fuzzing,results}

echo "=== Installation Complete ==="
echo ""
echo "Installed tools:"
echo "  - LLDB debugger"
echo "  - radare2 reverse engineering framework"
echo "  - r2pipe Python library"
echo "  - Firmware analysis tools (binwalk, flashrom)"
echo "  - Binary analysis libraries (capstone, keystone, lief)"
echo ""
echo "Optional: Install Ghidra manually from https://ghidra-sre.org/"
echo "Optional: Run 'pf install-fuzzing-tools' for kernel fuzzing tools"
