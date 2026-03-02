#!/bin/bash
# Helper script to install RetDec binary lifter

set -e

echo "========================================="
echo "RetDec Binary Lifter Installation"
echo "========================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v cmake &> /dev/null; then
    echo "Error: cmake is required but not installed"
    echo "Install with: sudo apt-get install cmake"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo "Error: git is required but not installed"
    echo "Install with: sudo apt-get install git"
    exit 1
fi

if ! command -v clang &> /dev/null; then
    echo "Error: clang is required but not installed"
    echo "Install with: sudo apt-get install clang"
    exit 1
fi

echo "✓ Prerequisites satisfied"
echo ""

# Set installation directory
INSTALL_DIR="${1:-$HOME/.local}"
RETDEC_DIR="${2:-/tmp/retdec}"

echo "Installation directory: $INSTALL_DIR"
echo "Build directory: $RETDEC_DIR"
echo ""

# Clone or update RetDec
if [ -d "$RETDEC_DIR" ]; then
    echo "RetDec directory exists, updating..."
    cd "$RETDEC_DIR"
    git pull
else
    echo "Cloning RetDec..."
    git clone https://github.com/avast/retdec "$RETDEC_DIR"
    cd "$RETDEC_DIR"
fi

echo ""
echo "Building RetDec (this may take 10-30 minutes)..."
mkdir -p build
cd build

# Configure with CMake
echo "Configuring with CMake..."
cmake .. \
    -DCMAKE_INSTALL_PREFIX="$INSTALL_DIR" \
    -DCMAKE_BUILD_TYPE=Release

# Build with all available cores
echo "Building..."
make -j$(nproc)

# Install
echo "Installing to $INSTALL_DIR..."
make install

echo ""
echo "========================================="
echo "RetDec Installation Complete!"
echo "========================================="
echo ""
echo "Installation location: $INSTALL_DIR/bin"
echo ""
echo "Add to PATH if not already present:"
echo "  export PATH=\"$INSTALL_DIR/bin:\$PATH\""
echo ""
echo "Test installation:"
echo "  retdec-decompiler.py --version"
echo ""
echo "Usage example:"
echo "  retdec-decompiler.py --backend llvmir myprogram -o output.ll"
echo ""
