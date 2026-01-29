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

# Fast path: download official prebuilt archive if available
VERSION="v5.0"
ARCHIVE="RetDec-${VERSION}-Linux-Release.tar.xz"
URL="https://github.com/avast/retdec/releases/download/${VERSION}/${ARCHIVE}"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "${TMPDIR}"' EXIT

echo ""
echo "Attempting fast install from official prebuilt release..."
if command -v curl >/dev/null 2>&1 && curl -fL "$URL" -o "$TMPDIR/$ARCHIVE"; then
    echo "Downloaded prebuilt archive; extracting..."
    tar -C "$TMPDIR" -xf "$TMPDIR/$ARCHIVE"
    if [ -x "$TMPDIR/bin/retdec-decompiler" ] || [ -x "$TMPDIR/bin/retdec-decompiler.py" ]; then
        mkdir -p "$INSTALL_DIR"
        rsync -a "$TMPDIR"/ "$INSTALL_DIR/"
        echo "✓ RetDec installed from prebuilt archive to $INSTALL_DIR"
        echo "Add to PATH if needed: export PATH=\"$INSTALL_DIR/bin:\\$PATH\""
        exit 0
    fi
    echo "[WARN] Prebuilt archive layout unexpected or missing binaries, falling back to source build..."
else
    echo "[WARN] Could not download prebuilt archive; falling back to source build..."
fi

echo "Building RetDec from source (this may take 10-30 minutes)..."
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
