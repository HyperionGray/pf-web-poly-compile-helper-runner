#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/pf-bash-lib.sh
source "${SCRIPT_DIR}/../lib/pf-bash-lib.sh"

DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: install-pr-tools.sh [--dry-run] [--help]

Install PR management dependencies:
  - gh   (GitHub CLI)
  - glab (GitLab CLI)
  - jq   (JSON CLI helper)

Options:
  --dry-run   Print actions without installing anything
  -h, --help  Show this help message and exit
EOF
}

run_cmd() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[DRY-RUN]'
    printf ' %q' "$@"
    printf '\n'
    return 0
  fi
  "$@"
}

run_root_cmd() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[DRY-RUN]'
    printf ' %q' "$@"
    printf '\n'
    return 0
  fi
  run_as_root "$@"
}

run_root_shell_cmd() {
  local shell_cmd="$1"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[DRY-RUN] %s\n' "$shell_cmd"
    return 0
  fi
  run_as_root bash -lc "$shell_cmd"
}

install_linux_gh() {
  run_root_shell_cmd "curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg > /usr/share/keyrings/githubcli-archive-keyring.gpg"
  run_root_shell_cmd "echo \"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main\" > /etc/apt/sources.list.d/github-cli.list"
  run_root_cmd apt-get update
  run_root_cmd apt-get install -y gh
}

install_linux_glab() {
  local arch
  local url
  local tmpdir
  arch="$(uname -m)"
  case "$arch" in
    x86_64) arch="amd64" ;;
    aarch64|arm64) arch="arm64" ;;
    *)
      die "Unsupported Linux architecture for glab binary: ${arch}"
      ;;
  esac

  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[DRY-RUN] Download latest glab release for linux_${arch}.tar.gz"
    echo "[DRY-RUN] Extract and move glab to /usr/local/bin/glab"
    return 0
  fi

  tmpdir="$(mktemp -d)"
  trap 'rm -rf "$tmpdir"' EXIT

  url="$(curl -fsSL https://api.github.com/repos/profclems/glab/releases/latest \
    | sed -n "s/.*\"browser_download_url\": \"\\([^\"]*linux_${arch}\\.tar\\.gz\\)\".*/\\1/p" \
    | sed -n '1p')"

  [[ -n "$url" ]] || die "Could not resolve glab release URL for linux_${arch}"

  (
    cd "$tmpdir"
    curl -fsSLO "$url"
    tar -xzf glab_*_linux_"${arch}".tar.gz
  )
  run_root_cmd mv "$tmpdir/bin/glab" /usr/local/bin/
}

install_linux_jq() {
  run_root_cmd apt-get update
  run_root_cmd apt-get install -y jq
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      log_error "Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
  shift
done

echo "Installing PR management tools..."
[[ "$DRY_RUN" -eq 1 ]] && echo "[DRY-RUN] No changes will be made."

if ! command_exists gh || [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Installing GitHub CLI (gh)..."
  if [[ "$(detect_os)" == "debian" ]]; then
    install_linux_gh
  elif [[ "$(detect_os)" == "macos" ]] && command_exists brew; then
    run_cmd brew install gh
  else
    die "Unsupported OS/package manager for gh install"
  fi
else
  echo "[OK] gh already installed"
fi

if ! command_exists glab || [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Installing GitLab CLI (glab)..."
  if [[ "$(detect_os)" == "debian" || "$(detect_os)" == "rhel" || "$(detect_os)" == "arch" || "$(detect_os)" == "linux" ]]; then
    install_linux_glab
  elif [[ "$(detect_os)" == "macos" ]] && command_exists brew; then
    run_cmd brew install glab
  else
    die "Unsupported OS/package manager for glab install"
  fi
else
  echo "[OK] glab already installed"
fi

if ! command_exists jq || [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Installing jq..."
  if [[ "$(detect_os)" == "debian" ]]; then
    install_linux_jq
  elif [[ "$(detect_os)" == "macos" ]] && command_exists brew; then
    run_cmd brew install jq
  else
    die "Unsupported OS/package manager for jq install"
  fi
else
  echo "[OK] jq already installed"
fi

echo ""
echo "[OK] PR management tools installation flow completed"
if [[ "$DRY_RUN" -eq 0 ]]; then
  command_exists gh && echo "  gh:   $(gh --version | sed -n '1p')"
  command_exists glab && echo "  glab: $(glab --version | sed -n '1p')"
  command_exists jq && echo "  jq:   $(jq --version)"
fi
echo ""
echo "USAGE:"
echo "  pf install-pr-tools"
echo "  pf pr-help"
echo ""
echo "TEST:"
echo "  gh --version"
echo "  glab --version"
echo "  jq --version"
