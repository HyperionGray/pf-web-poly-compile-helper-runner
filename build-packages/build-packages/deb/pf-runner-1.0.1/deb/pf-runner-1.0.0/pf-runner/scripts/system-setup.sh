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
"install-build-tools")
	echo "Installing polyglot build tools (C/C++, Fortran, Go, Rust, Java, etc.)..."
	sudo apt -y update
	# Core compilers and build tools
	sudo apt -y install clang llvm gfortran golang ninja-build cmake meson
	# Java (try openjdk-25, fallback to openjdk-21 if not available)
	if apt-cache show openjdk-25-jdk >/dev/null 2>&1; then
		sudo apt -y install openjdk-25-jdk
	elif apt-cache show openjdk-21-jdk >/dev/null 2>&1; then
		sudo apt -y install openjdk-21-jdk
	else
		sudo apt -y install default-jdk
	fi
	# Install Rust via rustup if not already installed
	if ! command -v rustup >/dev/null 2>&1; then
		echo "Installing Rust via rustup..."
		curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
		# Source cargo env for current session
		if [ -f "$HOME/.cargo/env" ]; then
			. "$HOME/.cargo/env"
		fi
		echo "Rust installed successfully"
	else
		echo "Rust (rustup) already installed"
	fi
	echo "Build tools installation complete"
	;;
"setup-venv")
	echo "Setting up central python virtual environment..."
	if [ ! -d "$HOME/.venv" ]; then
		python3 -m venv "$HOME/.venv"
	fi
	"$HOME/.venv/bin/pip" install --upgrade pip
	echo "Virtual environment ready at $HOME/.venv"
	;;
"help")
	echo "Usage: $0 {update|upgrade|install-base|install-build-tools|setup-venv}"
	echo ""
	echo "  update            - Update package lists"
	echo "  upgrade           - Update and upgrade system packages"
	echo "  install-base      - Install base development packages"
	echo "  install-build-tools - Install polyglot build tools (C/C++, Fortran, Go, Rust, Java)"
	echo "  setup-venv        - Set up central Python virtual environment"
	exit 0
	;;
*)
	echo "Error: Unknown action '$action'"
	echo "Run '$0 help' for usage information"
	exit 1
	;;
esac
