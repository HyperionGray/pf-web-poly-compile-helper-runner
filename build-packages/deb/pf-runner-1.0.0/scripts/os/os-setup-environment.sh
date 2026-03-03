#!/usr/bin/env bash
set -euo pipefail

mkdir -p "$HOME/.local/bin"

cat > "$HOME/.local/bin/pf-os-env" <<'EOF'
#!/usr/bin/env bash
# OS Environment Manager for pf
# Usage: pf-os-env <os-name> [command]

os_name="${1:-}"
shift || true
command="${*:-}"

case "$os_name" in
  centos|fedora|arch|opensuse|macos-like)
    export PF_CURRENT_OS="$os_name"
    export PATH="/opt/pf-os/$os_name/bin:$PATH"
    export LD_LIBRARY_PATH="/opt/pf-os/$os_name/lib:${LD_LIBRARY_PATH:-}"

    if [ -n "$command" ]; then
      exec $command
    fi

    echo "Environment set for $os_name"
    echo "PATH: $PATH"
    exec "${SHELL:-/bin/bash}"
    ;;
  *)
    echo "Available OS environments: centos, fedora, arch, opensuse, macos-like"
    exit 1
    ;;
esac
EOF

chmod +x "$HOME/.local/bin/pf-os-env"
echo "OK OS environment manager installed to $HOME/.local/bin/pf-os-env"
