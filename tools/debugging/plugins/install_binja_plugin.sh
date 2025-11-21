#!/usr/bin/env bash
# Install Binary Ninja plugin

plugin="$1"

echo "[*] Installing Binary Ninja Plugin"
echo "[*] Plugin: $plugin"
echo ""

if [ -z "$plugin" ]; then
    echo "Error: plugin path required"
    exit 1
fi

# Binary Ninja user plugins directory
BINJA_PLUGINS="$HOME/.binaryninja/plugins"
mkdir -p "$BINJA_PLUGINS"

# Copy plugin
cp "$plugin" "$BINJA_PLUGINS/"
echo "[+] Plugin installed to: $BINJA_PLUGINS"
echo ""
echo "Restart Binary Ninja to load the plugin"
