#!/usr/bin/env bash
set -euo pipefail

echo "Installing PR management tools..."

install_linux_gh() {
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg >/dev/null
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list >/dev/null
  sudo apt-get update
  sudo apt-get install -y gh
}

install_linux_glab() {
  local tmpdir
  tmpdir="$(mktemp -d)"
  trap 'rm -rf "$tmpdir"' EXIT

  (cd "$tmpdir" && curl -fsSL https://api.github.com/repos/profclems/glab/releases/latest \
    | grep "browser_download_url.*linux_amd64.tar.gz" \
    | cut -d '"' -f 4 \
    | xargs -n 1 curl -fsSLO)

  (cd "$tmpdir" && tar -xzf glab_*_linux_amd64.tar.gz)
  sudo mv "$tmpdir/bin/glab" /usr/local/bin/
}

install_linux_jq() {
  sudo apt-get update
  sudo apt-get install -y jq
}

if ! command -v gh >/dev/null 2>&1; then
  echo "Installing GitHub CLI (gh)..."
  if [[ "${OSTYPE:-}" == "linux-gnu"* ]] && command -v apt-get >/dev/null 2>&1; then
    install_linux_gh
  elif [[ "${OSTYPE:-}" == "darwin"* ]] && command -v brew >/dev/null 2>&1; then
    brew install gh
  else
    echo "ERROR: unsupported OS/package manager for gh install"
    exit 1
  fi
else
  echo "OK gh already installed"
fi

if ! command -v glab >/dev/null 2>&1; then
  echo "Installing GitLab CLI (glab)..."
  if [[ "${OSTYPE:-}" == "linux-gnu"* ]]; then
    install_linux_glab
  elif [[ "${OSTYPE:-}" == "darwin"* ]] && command -v brew >/dev/null 2>&1; then
    brew install glab
  else
    echo "ERROR: unsupported OS/package manager for glab install"
    exit 1
  fi
else
  echo "OK glab already installed"
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "Installing jq..."
  if [[ "${OSTYPE:-}" == "linux-gnu"* ]] && command -v apt-get >/dev/null 2>&1; then
    install_linux_jq
  elif [[ "${OSTYPE:-}" == "darwin"* ]] && command -v brew >/dev/null 2>&1; then
    brew install jq
  else
    echo "ERROR: unsupported OS/package manager for jq install"
    exit 1
  fi
else
  echo "OK jq already installed"
fi

echo "OK PR management tools installation complete"
