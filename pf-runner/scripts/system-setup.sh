#!/bin/bash
# scripts/system-setup.sh - Helper script for system setup operations

set -euo pipefail

action="${1:-help}"

case "$action" in
    "update")
        echo "Updating package lists..."
        sudo apt -y update
        ;;
    "upgrade")
        echo "Upgrading system packages..."
        sudo apt -y update
        sudo apt -y upgrade
        ;;
    "install-base")
        echo "Installing base development packages..."
        sudo apt -y install curl git htop build-essential python3-dev
        ;;
    "setup-venv")
        echo "Setting up central python virtual environment..."
        if [ ! -d "/home/punk/.venv" ]; then
            /home/punk/.venv/bin/python -m venv /home/punk/.venv
        fi
        /home/punk/.venv/bin/pip install --upgrade pip
        echo "Virtual environment ready at /home/punk/.venv"
        ;;
    "help")
        echo "Usage: $0 {update|upgrade|install-base|setup-venv}"
        echo ""
        echo "  update      - Update package lists"
        echo "  upgrade     - Update and upgrade system packages"
        echo "  install-base - Install base development packages"
        echo "  setup-venv  - Set up central Python virtual environment"
        exit 0
        ;;
    *)
        echo "Error: Unknown action '$action'"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac