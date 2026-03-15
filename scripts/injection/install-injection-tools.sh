#!/usr/bin/env bash
set -euo pipefail

echo "Installing binary injection tools..."

os="$(uname -s)"
if [ "$os" = "Linux" ]; then
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y patchelf nasm binaryen wabt
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y patchelf nasm binaryen wabt
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -S --noconfirm patchelf nasm binaryen wabt
  else
    echo "ERROR: unsupported Linux distribution; install manually: patchelf nasm binaryen wabt"
    exit 1
  fi
elif [ "$os" = "Darwin" ]; then
  if command -v brew >/dev/null 2>&1; then
    brew install patchelf nasm binaryen wabt
  else
    echo "ERROR: Homebrew not found; install it then rerun"
    exit 1
  fi
else
  echo "ERROR: unsupported OS; install manually: patchelf nasm binaryen wabt"
  exit 1
fi

echo "Verifying installations..."
patchelf --version 2>/dev/null || echo "  patchelf: NOT installed"
nasm -version 2>/dev/null || echo "  nasm: NOT installed"
wasm-opt --version 2>/dev/null || echo "  binaryen: NOT installed"
wat2wasm --version 2>/dev/null || echo "  wabt: NOT installed"

echo ""
echo "[OK] Binary injection tools installed successfully!"
echo ""
echo "USAGE EXAMPLES:"
echo "  pf compile-c-shared-lib source=code.c output=lib.so"
echo "  pf inject-shared-lib binary=./program lib=hook.so"
echo "  pf patch-binary-deps binary=./program old_lib=libold.so new_lib=./libnew.so"
echo "  pf demo-injection-workflow  # Run a complete injection demo"
echo ""
echo "TEST COMMANDS:"
echo "  patchelf --version"
echo "  nasm -version"
echo "  wasm-opt --version"
echo "  wat2wasm --version"
