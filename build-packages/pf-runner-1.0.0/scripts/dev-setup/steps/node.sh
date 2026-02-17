#!/usr/bin/env bash
set -euo pipefail

dev_setup_install_node_dependencies() {
  log_info "Installing Node.js dependencies..."

  if [[ ! -f "package.json" ]]; then
    log_warning "No package.json found, skipping Node.js dependencies"
    return 0
  fi

  if [[ -f "package-lock.json" ]]; then
    npm ci || die "Failed to install Node.js dependencies (npm ci)"
  else
    npm install || die "Failed to install Node.js dependencies (npm install)"
  fi

  log_success "Node.js dependencies installed"
}

dev_setup_install_playwright_browsers() {
  log_info "Installing Playwright browsers..."

  if ! command_exists npx; then
    log_warning "npx not available, skipping Playwright browser installation"
    return 0
  fi

  npx playwright install --with-deps || log_warning "Failed to install Playwright browsers (non-critical)"
  log_success "Playwright browsers installed"
}

