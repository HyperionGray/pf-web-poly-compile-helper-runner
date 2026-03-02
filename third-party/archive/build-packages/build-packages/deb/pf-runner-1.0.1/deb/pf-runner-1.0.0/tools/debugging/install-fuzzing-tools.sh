#!/usr/bin/env bash
# Install kernel fuzzing tools

set -e

echo "=== Installing Kernel Fuzzing Tools ==="

OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
fi

if [ "$OS" == "linux" ]; then
    echo "Installing AFL++ (American Fuzzy Lop)..."
    sudo apt-get update
    sudo apt-get install -y afl++ || {
        echo "AFL++ not in repos, building from source..."
        cd /tmp
        git clone https://github.com/AFLplusplus/AFLplusplus || true
        cd AFLplusplus && make && sudo make install || echo "AFL++ build failed"
    }
    
    echo "Installing Syzkaller dependencies..."
    sudo apt-get install -y \
        golang \
        git \
        make \
        || echo "Some packages failed to install"
    
    echo ""
    echo "To install Syzkaller:"
    echo "  git clone https://github.com/google/syzkaller"
    echo "  cd syzkaller && make"
    echo ""
    
elif [ "$OS" == "macos" ]; then
    echo "Kernel fuzzing tools have limited macOS support"
    echo "Consider using a Linux VM for full functionality"
fi

echo "=== Installation Complete ==="
echo ""
echo "Available fuzzing tools:"
echo "  - AFL++ (coverage-guided fuzzer)"
echo "  - Syzkaller (requires manual setup)"
echo ""
echo "Usage:"
echo "  pf fuzz-basic binary=/path/to/binary"
echo "  pf fuzz-kernel-syzkaller config=/path/to/config"
