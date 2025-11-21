#!/usr/bin/env bash
# Install radare2 plugin

plugin="$1"

echo "[*] Installing radare2 Plugin"
echo "[*] Plugin: $plugin"
echo ""

if [ -z "$plugin" ]; then
    echo "Error: plugin path required"
    exit 1
fi

# Check if r2 is installed
if ! command -v r2 &> /dev/null; then
    echo "Error: radare2 not installed"
    echo "Install with: pf install-radare2"
    exit 1
fi

# Get r2 plugin directory
R2_USER_PLUGINS="$HOME/.local/share/radare2/plugins"
mkdir -p "$R2_USER_PLUGINS"

# Copy plugin
cp "$plugin" "$R2_USER_PLUGINS/"
echo "[+] Plugin installed to: $R2_USER_PLUGINS"
echo ""
echo "Usage in radare2:"
echo "  r2 binary"
echo "  > L  # List loaded plugins"
