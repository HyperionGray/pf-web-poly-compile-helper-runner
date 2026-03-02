#!/usr/bin/env bash
set -euo pipefail

if declare -F __pf_installer_cli_loaded >/dev/null 2>&1; then
  return 0
fi
__pf_installer_cli_loaded() { :; }

installer_show_help() {
  cat << EOF
pf-runner Installation Script

USAGE:
  ./install.sh [OPTIONS]

OPTIONS:
  --mode MODE       Install mode: native (default) or package (alias for native)
  --package         Alias for --mode native
  --native          Alias for --mode native
  --prefix PATH     Install prefix (default: /usr/local for root, ~/.local for user)
  --skip-deps       Skip installing system dependencies (native mode)
  --help, -h        Show this help message
