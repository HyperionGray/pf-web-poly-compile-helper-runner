#!/usr/bin/env bash
set -euo pipefail

dev_setup_create_dev_configs() {
  log_info "Creating development configuration files..."

  if [[ ! -d ".vscode" ]]; then
    mkdir -p .vscode
  fi

  if [[ ! -f ".vscode/settings.json" ]]; then
    cat > .vscode/settings.json <<'EOF'
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv-dev/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
EOF
    log_success "VS Code settings created"
  else
    log_info "VS Code settings already exist"
  fi
}

