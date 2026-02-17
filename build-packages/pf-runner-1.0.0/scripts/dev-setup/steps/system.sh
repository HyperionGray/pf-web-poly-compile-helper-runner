#!/usr/bin/env bash
set -euo pipefail

dev_setup_check_system_requirements() {
  log_info "Checking system requirements..."

  local missing=()

  if command_exists python3; then
    log_success "Python $(python3 --version | awk '{print $2}') found"
  else
    missing+=("python3")
  fi

  if command_exists node; then
    log_success "Node.js $(node --version) found"
  else
    missing+=("node")
  fi

  if command_exists npm; then
    log_success "npm $(npm --version) found"
  else
    missing+=("npm")
  fi

  if command_exists git; then
    log_success "Git $(git --version | awk '{print $3}') found"
  else
    missing+=("git")
  fi

  if [[ ${#missing[@]} -gt 0 ]]; then
    log_error "Missing required dependencies: ${missing[*]}"
    printf '%s\n' "Install them and re-run this script."
    printf '%s\n' "Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip nodejs npm git"
    printf '%s\n' "macOS: brew install python3 node npm git"
    exit 1
  fi

  if ! python3 -m pip --version >/dev/null 2>&1; then
    log_error "python3 -m pip is required but not available"
    exit 1
  fi

  log_success "All system requirements met"
}

