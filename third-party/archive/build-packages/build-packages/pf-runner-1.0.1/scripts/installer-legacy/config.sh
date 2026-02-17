#!/usr/bin/env bash
set -euo pipefail

if declare -F __pf_installer_config_loaded >/dev/null 2>&1; then
  return 0
fi
__pf_installer_config_loaded() { :; }

DEFAULT_PREFIX_NATIVE="/usr/local"
DEFAULT_PREFIX_USER="$(pf_home_dir)/.local"

MODE="native"
PREFIX=""
PREFIX_SET=false
SKIP_DEPS=false
SHOW_HELP=false
