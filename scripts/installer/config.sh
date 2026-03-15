#!/usr/bin/env bash
set -euo pipefail

if declare -F __pf_installer_config_loaded >/dev/null 2>&1; then
  return 0
fi
__pf_installer_config_loaded() { :; }

# Defaults
DEFAULT_PREFIX_NATIVE="/usr/local"
DEFAULT_PREFIX_USER="$(pf_home_dir)/.local"
DEFAULT_PREFIX_CONTAINER="$(pf_home_dir)/.local"

BASE_IMAGE_DEFAULT="localhost/pf-base:latest"
RUNNER_IMAGE_DEFAULT="localhost/pf-runner:latest"

# CLI settings
MODE="package" # package behaves like native in this repo
PREFIX=""
PREFIX_SET=false
SKIP_DEPS=false
SHOW_HELP=false
DRY_RUN=false
WRITE_SHELL_PROFILE=false
SHELL_PROFILE=""
SHELL_PROFILE_SET=false

CONTAINER_RT="podman"
CONTAINER_RT_SET=false
CONTAINER_IMAGE="${RUNNER_IMAGE_DEFAULT}"
SKIP_BUILD=false
NO_WRAPPER=false
BUILD_ONLY=false

PACKAGE_FORMATS=()
FORCE_BUILD_PACKAGES=false

