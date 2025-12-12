#!/usr/bin/env bash
# quadlet-doctor.sh — diagnose quadlet + podman + systemd-user environment
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info(){ echo -e "${BLUE}[INFO]${NC} $*"; }
ok(){ echo -e "${GREEN}[OK]${NC} $*"; }
warn(){ echo -e "${YELLOW}[WARN]${NC} $*"; }
err(){ echo -e "${RED}[ERR]${NC} $*"; }

USER_MODE=true
if [[ ${EUID:-0} -eq 0 ]]; then USER_MODE=false; fi
SYSTEMCTL="systemctl --user"
$USER_MODE || SYSTEMCTL=systemctl

# 1) Podman
if command -v podman >/dev/null 2>&1; then
  ok "podman found: $(podman --version | head -1)"
else
  err "podman not found in PATH"; exit 1
fi

# 2) Rootless socket
RUNDIR=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
SOCK="$RUNDIR/podman/podman.sock"
if [[ -S "$SOCK" ]]; then
  ok "rootless socket present: $SOCK"
else
  warn "rootless socket missing: $SOCK"
  warn "try: systemctl --user enable --now podman.socket"
fi

# 3) podman ps connectivity (respects CONTAINER_HOST if set)
if podman ps >/dev/null 2>&1; then
  ok "podman ps succeeded"
else
  warn "podman ps failed (CONTAINER_HOST=${CONTAINER_HOST:-unset})"
fi

# 4) Quadlet paths
DEST_USER="$HOME/.config/containers/systemd"
DEST_SYS="/etc/containers/systemd"
[[ -d "$DEST_USER" ]] && ok "user quadlets dir exists: $DEST_USER" || warn "no user quadlets dir ($DEST_USER)"
[[ -d "$DEST_SYS" ]] && ok "system quadlets dir exists: $DEST_SYS" || true

# 5) systemd user availability
if $SYSTEMCTL --version >/dev/null 2>&1; then
  ok "$SYSTEMCTL available"
else
  warn "$SYSTEMCTL not available"
fi

# 6) Units
$SYSTEMCTL daemon-reload || warn "daemon-reload failed (user instance might be inactive)"

mapfile -t PF_UNITS < <(ls "$DEST_USER"/pf-* 2>/dev/null | sed 's#.*/##' | sed 's/\..*/.service/')
if [[ ${#PF_UNITS[@]} -gt 0 ]]; then
  info "pf units expected (from quadlets):"
  printf '  - %s\n' "${PF_UNITS[@]}"
  info "installed unit-files (filtered):"
  $SYSTEMCTL list-unit-files | grep -E '^pf-.*\.(service|target)' || true
else
  warn "no pf-* quadlet files found under $DEST_USER"
fi

# 7) pf-suite.target
if [[ -f "$DEST_USER/pf-suite.target" ]]; then
  ok "pf-suite.target present"
  $SYSTEMCTL status pf-suite.target >/dev/null 2>&1 && info "pf-suite.target status available"
else
  warn "pf-suite.target missing — run: pf quadlet-install"
fi

exit 0