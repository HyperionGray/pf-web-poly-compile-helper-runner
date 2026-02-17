#!/usr/bin/env bash
set -euo pipefail

dev_setup_setup_git_hooks() {
  log_info "Setting up Git hooks..."

  if [[ -f ".git/hooks/pre-commit" ]]; then
    chmod +x .git/hooks/pre-commit
    log_success "Pre-commit hook configured"
  else
    log_warning "Pre-commit hook not found"
  fi

  cat > .git/commit-template <<'EOF'
# <type>(<scope>): <subject>
#
# <body>
#
# <footer>
#
# Types:
# feat: A new feature
# fix: A bug fix
# docs: Documentation only changes
# style: Changes that do not affect the meaning of the code
# refactor: A code change that neither fixes a bug nor adds a feature
# perf: A code change that improves performance
# test: Adding missing tests or correcting existing tests
# chore: Changes to the build process or auxiliary tools
EOF

  git config commit.template .git/commit-template || log_warning "Failed to set git commit.template (non-critical)"
  log_success "Git commit template configured"
}

